"""Route handlers for /api/* synthesis endpoints."""

from __future__ import annotations

import base64
import io
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
from document_simulator.synthesis.generator import SyntheticDocumentGenerator
from document_simulator.synthesis.zones import SynthesisConfig

router = APIRouter()

_ALLOWED_IMAGE_EXTS = {".png", ".jpg", ".jpeg"}
_ALLOWED_PDF_EXTS = {".pdf"}
_ALLOWED_EXTS = _ALLOWED_IMAGE_EXTS | _ALLOWED_PDF_EXTS

_SAMPLES_DIR = Path(__file__).resolve().parents[4] / "data" / "samples" / "synthetic_generator"


def _pil_to_png_b64(img: Image.Image) -> str:
    """Convert a PIL Image to a base64-encoded PNG string."""
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def _render_template_bytes(file_bytes: bytes, filename: str, dpi: int, page: int) -> tuple[Image.Image, bool]:
    """Render file bytes to a PIL Image.

    Returns:
        (pil_image, is_pdf)

    Raises:
        HTTPException(422) for unsupported types or empty files.
    """
    if not file_bytes:
        raise HTTPException(status_code=422, detail="Uploaded file is empty.")

    lower = filename.lower()
    ext = "." + lower.rsplit(".", 1)[-1] if "." in lower else ""

    if ext in _ALLOWED_PDF_EXTS:
        try:
            import fitz  # PyMuPDF
        except ImportError as exc:
            raise HTTPException(status_code=500, detail="PyMuPDF not installed.") from exc
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        pix = doc[page].get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72))
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        return img, True

    if ext in _ALLOWED_IMAGE_EXTS:
        try:
            img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
            return img, False
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"Cannot open image: {exc}") from exc

    raise HTTPException(
        status_code=422,
        detail=f"Unsupported file type '{ext}'. Allowed: .pdf, .png, .jpg, .jpeg",
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

    img, is_pdf = _render_template_bytes(file_bytes, filename, dpi=dpi, page=page)

    image_b64 = _pil_to_png_b64(img)
    logger.info(f"Template uploaded: {filename!r} → {img.width}×{img.height}px is_pdf={is_pdf}")

    return TemplateResponse(
        image_b64=image_b64,
        width_px=img.width,
        height_px=img.height,
        dpi=dpi,
        is_pdf=is_pdf,
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

    # Build a blank template sized from generator config
    template = Image.new(
        "RGB",
        (synthesis_config.generator.image_width, synthesis_config.generator.image_height),
        color=(255, 255, 255),
    )
    gen = SyntheticDocumentGenerator(template=template, synthesis_config=synthesis_config)

    samples: list[PreviewSample] = []
    for seed in body.seeds:
        img, _gt = gen.generate_one(seed=seed)
        samples.append(PreviewSample(seed=seed, image_b64=_pil_to_png_b64(img)))

    return PreviewResponse(samples=samples)


def _run_generate_job(job_id: str, synthesis_config_dict: dict, n: int) -> None:
    """Background task: generate n documents and store ZIP bytes in job store."""
    try:
        update_job(job_id, status="running")

        synthesis_config = SynthesisConfig.model_validate(synthesis_config_dict)
        template = Image.new(
            "RGB",
            (synthesis_config.generator.image_width, synthesis_config.generator.image_height),
            color=(255, 255, 255),
        )
        gen = SyntheticDocumentGenerator(template=template, synthesis_config=synthesis_config)

        pairs = gen.generate(n=n, write=False)

        # Build ZIP in memory
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for i, (img, gt) in enumerate(pairs):
                stem = f"doc_{i + 1:06d}"

                img_buf = io.BytesIO()
                img.save(img_buf, format="PNG")
                zf.writestr(f"{stem}.png", img_buf.getvalue())
                zf.writestr(f"{stem}.json", gt.model_dump_json(indent=2))

                progress = (i + 1) / n
                update_job(job_id, progress=progress)

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
    background_tasks.add_task(_run_generate_job, job_id, body.synthesis_config, body.n)
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
        if f.suffix.lower() in _ALLOWED_EXTS and not f.name.startswith(".")
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
    img, is_pdf = _render_template_bytes(file_bytes, safe_name, dpi=dpi, page=page)
    logger.info(f"Sample loaded: {safe_name!r} → {img.width}×{img.height}px")
    return TemplateResponse(image_b64=_pil_to_png_b64(img), width_px=img.width, height_px=img.height, dpi=dpi, is_pdf=is_pdf)


@router.get("/api/config/schema")
def config_schema() -> dict:
    """Return the JSON Schema for SynthesisConfig."""
    return SynthesisConfig.model_json_schema()
