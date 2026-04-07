"""Route handlers for /api/* synthesis endpoints."""

from __future__ import annotations

import base64
import io
import uuid
import zipfile
from typing import Annotated

from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from loguru import logger
from PIL import Image
from pydantic import ValidationError

from document_simulator.api.jobs import create_job, get_job, update_job
from document_simulator.api.models import (
    GenerateRequest,
    GenerateResponse,
    JobStatusResponse,
    PreviewRequest,
    PreviewResponse,
    PreviewSample,
    TemplateResponse,
)
from document_simulator.data.ground_truth import GroundTruth
from document_simulator.synthesis.annotation import AnnotationBuilder
from document_simulator.synthesis.field_schema import DocumentSchema
from document_simulator.synthesis.generator import SyntheticDocumentGenerator
from document_simulator.synthesis.renderer import StyleResolver, ZoneRenderer
from document_simulator.synthesis.sampler import ZoneDataSampler, generate_respondent
from document_simulator.synthesis.schema_extractor import Backend, SchemaExtractor
from document_simulator.synthesis.zones import SynthesisConfig

router = APIRouter()

_ALLOWED_EXTS = {".pdf"}

_SAMPLES_DIR = Path(__file__).resolve().parents[4] / "data" / "samples" / "synthetic_generator"

# In-memory store: template_id → raw PDF bytes.
# Populated on every /api/template upload and /api/samples/{filename} load.
_template_store: dict[str, bytes] = {}


def _pil_to_png_b64(img: Image.Image) -> str:
    """Convert a PIL Image to a base64-encoded PNG string."""
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def _render_template_bytes(file_bytes: bytes, filename: str, dpi: int, page: int) -> tuple[Image.Image, bool, int]:
    """Render PDF file bytes to a PIL Image.

    Returns:
        (pil_image, is_pdf, page_count)

    Raises:
        HTTPException(422) for unsupported types or empty files.
    """
    if not file_bytes:
        raise HTTPException(status_code=422, detail="Uploaded file is empty.")

    lower = filename.lower()
    ext = "." + lower.rsplit(".", 1)[-1] if "." in lower else ""

    if ext == ".pdf":
        try:
            import fitz  # PyMuPDF
        except ImportError as exc:
            raise HTTPException(status_code=500, detail="PyMuPDF not installed.") from exc
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        page_count = len(doc)
        safe_page = max(0, min(page, page_count - 1))
        pix = doc[safe_page].get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72))
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        return img, True, page_count

    raise HTTPException(
        status_code=422,
        detail="Only PDF templates are supported. Please upload a .pdf file.",
    )


@router.post("/api/template", response_model=TemplateResponse)
async def upload_template(
    file: UploadFile,
    dpi: Annotated[int, Form()] = 150,
    page: Annotated[int, Form()] = 0,
) -> TemplateResponse:
    """Accept a PNG/JPG/PDF file, render it to a PNG, and return as base64."""
    file_bytes = await file.read()
    filename = file.filename or ""

    img, is_pdf, page_count = _render_template_bytes(file_bytes, filename, dpi=dpi, page=page)

    # Store raw PDF bytes for multi-page generation later
    template_id = str(uuid.uuid4())
    _template_store[template_id] = file_bytes

    image_b64 = _pil_to_png_b64(img)
    logger.info(f"Template uploaded: {filename!r} → {img.width}×{img.height}px is_pdf={is_pdf} pages={page_count} id={template_id}")

    return TemplateResponse(
        image_b64=image_b64,
        width_px=img.width,
        height_px=img.height,
        dpi=dpi,
        is_pdf=is_pdf,
        page_count=page_count,
        template_id=template_id,
    )


def _validate_synthesis_config_strict(data: dict) -> SynthesisConfig:
    """Validate a dict against SynthesisConfig, rejecting unknown-only dicts.

    Raises:
        HTTPException(422) if the dict contains only unknown fields or is invalid.
    """
    known_keys = set(SynthesisConfig.model_fields.keys())
    incoming_keys = set(data.keys())
    if incoming_keys and not incoming_keys.intersection(known_keys):
        raise HTTPException(
            status_code=422,
            detail=f"Unknown fields: {sorted(incoming_keys)}. "
            f"Expected keys from: {sorted(known_keys)}",
        )
    try:
        return SynthesisConfig.model_validate(data)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/api/preview", response_model=PreviewResponse)
def preview(body: PreviewRequest) -> PreviewResponse:
    """Generate preview samples from a SynthesisConfig."""
    synthesis_config = _validate_synthesis_config_strict(body.synthesis_config)

    # Filter zones to the current page so the preview only shows zones drawn on this page
    page_config = synthesis_config.model_copy(
        update={"zones": [z for z in synthesis_config.zones if z.page == body.current_page]}
    )

    # Use the uploaded template if provided, otherwise fall back to a blank canvas
    if body.template_b64:
        try:
            raw = base64.b64decode(body.template_b64)
            template = Image.open(io.BytesIO(raw)).convert("RGB")
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"Cannot decode template_b64: {exc}") from exc
    else:
        template = Image.new(
            "RGB",
            (synthesis_config.generator.image_width, synthesis_config.generator.image_height),
            color=(255, 255, 255),
        )
    gen = SyntheticDocumentGenerator(template=template, synthesis_config=page_config)

    samples: list[PreviewSample] = []
    for seed in body.seeds:
        img, _gt = gen.generate_one(seed=seed)
        samples.append(PreviewSample(seed=seed, image_b64=_pil_to_png_b64(img)))

    return PreviewResponse(samples=samples)


def _generate_multipage_doc(
    pdf_raw: bytes,
    synthesis_config: SynthesisConfig,
    seed: int,
    dpi: int = 150,
) -> tuple[list[Image.Image], GroundTruth]:
    """Render each PDF page and apply page-specific zones, returning all rendered pages."""
    import fitz  # PyMuPDF

    doc = fitz.open(stream=pdf_raw, filetype="pdf")
    page_count = len(doc)

    resolver = StyleResolver(synthesis_config, seed=seed)
    respondent_identities = {
        r.respondent_id: generate_respondent(r.respondent_id, global_seed=seed)
        for r in synthesis_config.respondents
    }

    pages_out: list[Image.Image] = []
    all_rendered_regions: list[dict] = []

    for pg in range(page_count):
        pix = doc[pg].get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72))
        canvas = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

        for zone in synthesis_config.zones:
            if zone.page != pg:
                continue
            style = resolver.resolve(zone.respondent_id, zone.field_type_id)
            identity = respondent_identities.get(zone.respondent_id, {})
            text = ZoneDataSampler.sample(zone, identity, seed=seed)
            canvas = ZoneRenderer.draw(canvas, text, style, zone, seed=seed)
            all_rendered_regions.append({
                "box": zone.box,
                "text": text,
                "page": zone.page,
                "label": zone.label,
                "faker_provider": zone.faker_provider,
                "respondent": zone.respondent_id,
                "field_type": zone.field_type_id,
                "font_family": style.font_family,
                "font_size": style.font_size,
                "font_color": style.font_color,
                "alignment": zone.alignment,
                "fill_style": style.fill_style,
            })

        pages_out.append(canvas)

    gt = AnnotationBuilder.build(
        image_path=f"doc_{seed:06d}.pdf",
        rendered_regions=all_rendered_regions,
        seed=seed,
    )
    return pages_out, gt


def _run_generate_job(
    job_id: str,
    synthesis_config_dict: dict,
    n: int,
    template_b64: str | None = None,
    template_pdf_b64: str | None = None,
    template_id: str | None = None,
) -> None:
    """Background task: generate n documents and store ZIP bytes in job store."""
    try:
        update_job(job_id, status="running")

        synthesis_config = SynthesisConfig.model_validate(synthesis_config_dict)
        base_seed = synthesis_config.generator.seed

        # Resolve raw PDF bytes — template_id (server-side store) takes priority
        pdf_raw: bytes | None = None
        if template_id and template_id in _template_store:
            pdf_raw = _template_store[template_id]
            logger.info(f"Job {job_id}: using server-side template {template_id!r}")
        elif template_pdf_b64:
            try:
                pdf_raw = base64.b64decode(template_pdf_b64)
            except Exception as exc:
                raise ValueError(f"Cannot decode template_pdf_b64: {exc}") from exc

        # Build ZIP in memory — generate documents one by one for progress reporting
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for i in range(n):
                stem = f"doc_{i + 1:06d}"
                seed = base_seed + i

                if pdf_raw is not None:
                    # Multi-page path: render each PDF page with its zones
                    pages, gt = _generate_multipage_doc(pdf_raw, synthesis_config, seed)
                    pdf_buf = io.BytesIO()
                    if len(pages) == 1:
                        pages[0].save(pdf_buf, format="PDF")
                    else:
                        pages[0].save(pdf_buf, format="PDF", save_all=True, append_images=pages[1:])
                else:
                    # Single-page path: use rendered PNG template or blank canvas
                    if template_b64:
                        try:
                            raw = base64.b64decode(template_b64)
                            template = Image.open(io.BytesIO(raw)).convert("RGB")
                        except Exception as exc:
                            raise ValueError(f"Cannot decode template_b64: {exc}") from exc
                    else:
                        template = Image.new(
                            "RGB",
                            (synthesis_config.generator.image_width, synthesis_config.generator.image_height),
                            color=(255, 255, 255),
                        )
                    gen = SyntheticDocumentGenerator(template=template, synthesis_config=synthesis_config)
                    img, gt = gen.generate_one(seed=seed)
                    pdf_buf = io.BytesIO()
                    img.save(pdf_buf, format="PDF")

                zf.writestr(f"{stem}.pdf", pdf_buf.getvalue())
                zf.writestr(f"{stem}.json", gt.model_dump_json(indent=2))
                update_job(job_id, progress=(i + 1) / n)

        buf.seek(0)
        update_job(job_id, status="done", progress=1.0, result_bytes=buf.read())
        logger.info(f"Job {job_id}: generated {n} documents → done")

    except Exception as exc:
        logger.error(f"Job {job_id} failed: {exc}", exc_info=True)
        update_job(job_id, status="failed", error=str(exc))


@router.post("/api/generate", status_code=202, response_model=GenerateResponse)
def generate(body: GenerateRequest, background_tasks: BackgroundTasks) -> GenerateResponse:
    """Start a batch generation job and return its ID immediately."""
    # Validate config before accepting the job
    try:
        SynthesisConfig.model_validate(body.synthesis_config)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    job_id = create_job()
    background_tasks.add_task(
        _run_generate_job, job_id, body.synthesis_config, body.n,
        body.template_b64, body.template_pdf_b64, body.template_id,
    )
    logger.info(f"Job {job_id} queued: n={body.n}")
    return GenerateResponse(job_id=job_id)


@router.get("/api/jobs/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str) -> JobStatusResponse:
    """Return the current status of a generation job."""
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        progress=job.progress,
        error=job.error,
    )


@router.get("/api/jobs/{job_id}/download")
def download_job(job_id: str) -> StreamingResponse:
    """Download the ZIP archive for a completed job."""
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    if job.status != "done" or job.result_bytes is None:
        raise HTTPException(
            status_code=404,
            detail=f"Job '{job_id}' is not done yet (status={job.status}).",
        )
    return StreamingResponse(
        iter([job.result_bytes]),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=synthetic_documents.zip"},
    )


@router.get("/api/samples")
def list_samples() -> dict:
    """List available sample template files."""
    if not _SAMPLES_DIR.exists():
        return {"samples": []}
    files = sorted(
        f.name for f in _SAMPLES_DIR.iterdir()
        if f.suffix.lower() == ".pdf" and not f.name.startswith(".")
    )
    return {"samples": files}


@router.get("/api/samples/{filename}", response_model=TemplateResponse)
def load_sample(filename: str, dpi: int = 150, page: int = 0) -> TemplateResponse:
    """Render a sample file from disk and return as base64 PNG."""
    safe_name = Path(filename).name  # prevent path traversal
    sample_path = _SAMPLES_DIR / safe_name
    if not sample_path.exists():
        raise HTTPException(status_code=404, detail=f"Sample '{safe_name}' not found.")
    file_bytes = sample_path.read_bytes()
    img, is_pdf, page_count = _render_template_bytes(file_bytes, safe_name, dpi=dpi, page=page)

    # Store raw PDF bytes for multi-page generation later
    # Use a stable key based on filename so repeated page navigations reuse the same slot
    template_id = f"sample:{safe_name}"
    _template_store[template_id] = file_bytes

    logger.info(f"Sample loaded: {safe_name!r} → {img.width}×{img.height}px pages={page_count} id={template_id}")
    return TemplateResponse(
        image_b64=_pil_to_png_b64(img),
        width_px=img.width,
        height_px=img.height,
        dpi=dpi,
        is_pdf=is_pdf,
        page_count=page_count,
        template_id=template_id,
    )


@router.get("/api/config/schema")
def config_schema() -> dict:
    """Return the JSON Schema for SynthesisConfig."""
    return SynthesisConfig.model_json_schema()


@router.post("/api/synthesis/extract-schema", response_model=DocumentSchema)
async def extract_schema(
    files: list[UploadFile],
    backend: Annotated[Backend, Form()] = "mock",
) -> DocumentSchema:
    """Extract a DocumentSchema from 1–10 sample document scan images.

    Accepts multipart form data with:
    - ``files``: 1–10 image files (PNG, JPG, TIFF, PDF first-page)
    - ``backend``: ``mock`` (default) | ``openai`` | ``anthropic``

    Returns a ``DocumentSchema`` JSON object.
    """
    if not files:
        raise HTTPException(status_code=422, detail="At least one file is required.")
    if len(files) > 10:
        files = files[:10]

    images: list[Image.Image] = []
    for upload in files:
        raw = await upload.read()
        if not raw:
            continue
        filename = upload.filename or ""
        lower = filename.lower()
        try:
            if lower.endswith(".pdf"):
                try:
                    import fitz  # type: ignore[import-untyped]
                except ImportError as exc:
                    raise HTTPException(status_code=500, detail="PyMuPDF not installed.") from exc
                doc = fitz.open(stream=raw, filetype="pdf")
                pix = doc[0].get_pixmap(matrix=fitz.Matrix(150 / 72, 150 / 72))
                img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            else:
                img = Image.open(io.BytesIO(raw)).convert("RGB")
            images.append(img)
        except HTTPException:
            raise
        except Exception as exc:
            logger.warning(f"Could not decode uploaded file {filename!r}: {exc}")

    if not images:
        raise HTTPException(status_code=422, detail="No valid images could be decoded from the uploaded files.")

    try:
        extractor = SchemaExtractor(backend=backend)
        schema = extractor.extract(images)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.error(f"Schema extraction failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Schema extraction failed: {exc}") from exc

    return schema
