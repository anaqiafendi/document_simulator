"""FastAPI router for the photoreal receipt synthesis pipeline (FDD #28 + #29).

Endpoints under ``/api/receipt-synthesis``:

  * ``POST /render``                  — run the pipeline once, return base64
                                        images per stage + the ImageGroundTruth.
                                        v0.3d adds an optional 3D Eevee render
                                        via the bpy sidecar.
  * ``GET  /templates``               — list templates with dropdown metadata.
  * ``GET  /augraphy-presets``        — list Augraphy preset names.
  * ``GET  /hdri-thumbnails``         — bundled HDRIs with base64 thumbnails.
  * ``POST /batch``                   — start a resumable dataset batch (v0.4).
  * ``GET  /batch/{job_id}``          — batch job status + failure report.
  * ``GET  /batch/{job_id}/samples``  — page through the batch's manifest.
  * ``GET  /batch/{job_id}/download`` — download the dataset as a ZIP.

The router is a thin HTTP shell: every pipeline decision lives in
``synthesis.receipts.batch``, so ``/render`` and a batch worker take the exact
same code path.
"""

from __future__ import annotations

import base64
import io
import os
import time
import zipfile
from functools import cache, lru_cache
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from fastapi.responses import StreamingResponse
from loguru import logger
from PIL import Image, ImageOps

from document_simulator.api.jobs import create_job, get_job, update_job
from document_simulator.api.models import (
    AugraphyPresetListResponse,
    HDRIInfo,
    HDRIListResponse,
    ReceiptBatchFailure,
    ReceiptBatchRequest,
    ReceiptBatchSample,
    ReceiptBatchSampleListResponse,
    ReceiptBatchStartResponse,
    ReceiptBatchStatusResponse,
    ReceiptRenderRequest,
    ReceiptRenderResponse,
    StageOutput,
    TemplateInfo,
    TemplateListResponse,
)
from document_simulator.config import settings
from document_simulator.synthesis.receipts.augraphy_pretreat import SUPPORTED_PRESETS

# The template registry is imported, never redeclared: a second copy in this
# module is what let the router and `content.py` drift apart in v0.2.
from document_simulator.synthesis.receipts.batch import (
    BatchProgress,
    BatchResult,
    read_manifest,
    run_batch,
    synthesize_one,
)
from document_simulator.synthesis.receipts.content import TEMPLATE_IDS

router = APIRouter(prefix="/api/receipt-synthesis", tags=["receipt-synthesis"])

# 0.3.0 added the 3D render path; 0.4.0 added spec-driven layout + batch.
PIPELINE_VERSION = "0.4.0"

# ``data/hdri/`` holds the bundled CC0 HDRIs and their pre-baked 128x128
# thumbnails. Resolved relative to the package root so it works from any cwd.
_HDRI_DIR: Path = Path(__file__).resolve().parents[4] / "data" / "hdri"

# Default Eevee resolution for the 3D render. Kept small (384x384) so HF
# Spaces' shared CPU stays under ~15s per render. Override via
# ``RECEIPT_RENDER_RESOLUTION=1024`` for local M-series boxes.
_DEFAULT_3D_RESOLUTION = 384

# Sidecar render hard-timeout. Cold start is 30-60s on first call (worker
# spawns + bpy initializes), warm renders are 1-2s. We give it 180s so the
# first request never trips the timeout.
_SIDECAR_RENDER_TIMEOUT = 180.0

#: Where batch datasets land. Callers name a subdirectory, never a path.
BATCH_ROOT: Path = Path(settings.output_dir) / "receipt_batches"

#: Refuse to build a download ZIP larger than this in memory.
_MAX_ZIP_BYTES = 512 * 1024 * 1024

# ---------------------------------------------------------------------------
# Display metadata
#
# Only presentation strings live here — ids and template files come from the
# content registry. An id with no entry still renders, with a derived name, so
# adding a template never 500s this endpoint.
# ---------------------------------------------------------------------------

_TEMPLATE_DISPLAY: dict[str, tuple[str, str]] = {
    "thermal_minimal": (
        "Thermal Single-Column",
        "Classic 80mm thermal printer receipt with merchant header, line items, and totals.",
    ),
    "restaurant_tip": (
        "Restaurant w/ Tip Lines",
        "Sit-down restaurant receipt: server name, table, tip suggestions (15/18/20%).",
    ),
    "retail_multicol": (
        "Retail Multi-Column",
        "Big-box retail receipt with a 3-column SKU / description / price grid.",
    ),
    "a4_invoice": (
        "A4 Invoice",
        "Full-page A4 invoice layout with billing block, item table, and grand total.",
    ),
    "taxi_stub": (
        "Taxi / Parking Stub",
        "Narrow rideshare or parking stub: driver, route, fare breakdown, tip line.",
    ),
}

#: Rough per-receipt token budget used for the dropdown estimate. Header block
#: (merchant, address, date/time, receipt no.), per-item spans (sku, qty, price)
#: and the totals/payment footer.
_HEADER_TOKENS = 6
_TOKENS_PER_ITEM = 3
_FOOTER_TOKENS = 7


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _pil_to_png_b64(img: Image.Image) -> str:
    """Encode a PIL image as a base64 PNG string (no data: prefix)."""
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


@cache
def _estimate_token_count(template_id: str) -> int:
    """Cheap token-count estimate for the template dropdown.

    This used to do a full WeasyPrint render memoised on ``template_id``. That
    cache key stopped being sound in v0.4: token count now depends on the
    sampled ``LayoutSpec`` (which blocks and money rows are present), not on the
    template alone, so one cached render would have been reported for every
    layout. Rather than key the cache on a spec the dropdown does not have, the
    figure is derived from content only — which genuinely *is* a function of the
    template id — and is honestly an estimate. It also takes ``/templates`` from
    five WeasyPrint renders to none.
    """
    from document_simulator.synthesis.receipts.content import make_receipt

    receipt = make_receipt(seed=0, template=template_id)
    return _HEADER_TOKENS + _TOKENS_PER_ITEM * len(receipt.items) + _FOOTER_TOKENS


def _validate_template(template: str) -> None:
    """400 when the template id is not in the content registry."""
    if template not in TEMPLATE_IDS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown template {template!r}. Valid: {sorted(TEMPLATE_IDS)}",
        )


def _validate_preset(preset: str | None) -> None:
    """400 when an Augraphy preset name is not supported."""
    if preset is not None and preset not in SUPPORTED_PRESETS:
        raise HTTPException(
            status_code=400,
            detail=(f"Unknown augraphy_preset {preset!r}. Supported: {list(SUPPORTED_PRESETS)}"),
        )


def _list_hdri_ids() -> list[str]:
    """Sorted list of HDRI ids (file stems) bundled in ``data/hdri/``.

    Mirrors :func:`document_simulator.synthesis.receipts.scene.list_hdris`
    but does not import the bpy-touching scene module — keeping the router
    importable on bpy-free interpreters.
    """
    if not _HDRI_DIR.exists():
        return []
    return sorted(p.stem for p in _HDRI_DIR.glob("*.hdr"))


def _get_3d_resolution() -> tuple[int, int]:
    """Resolve the 3D render resolution from env or default.

    ``RECEIPT_RENDER_RESOLUTION=1024`` produces a 1024x1024 render. Anything
    non-positive falls back to the HF-friendly 384x384 default.
    """
    raw = os.environ.get("RECEIPT_RENDER_RESOLUTION", "").strip()
    if not raw:
        return (_DEFAULT_3D_RESOLUTION, _DEFAULT_3D_RESOLUTION)
    try:
        n = int(raw)
        if n <= 0:
            raise ValueError
        return (n, n)
    except ValueError:
        logger.warning(
            "RECEIPT_RENDER_RESOLUTION={!r} not a positive int; falling back to {}",
            raw,
            _DEFAULT_3D_RESOLUTION,
        )
        return (_DEFAULT_3D_RESOLUTION, _DEFAULT_3D_RESOLUTION)


@lru_cache(maxsize=1)
def _get_sidecar():
    """Lazy-init the BpySidecar singleton; spawn the worker on first call.

    Why lazy?
        Cold-start spawn is 30-60s (the worker imports bpy from scratch in
        the spawn process). Eager-starting at FastAPI startup would block
        ``uvicorn``'s health check window. Lazy-init pushes the cost onto
        the first ``render_3d=True`` request — the user is already waiting
        for a 3D render so the cold start is amortized into expected wait.

    Subsequent calls reuse the cached instance (1-2s warm renders).
    """
    from document_simulator.synthesis.receipts.scene.sidecar import BpySidecar

    sidecar = BpySidecar()
    sidecar.start()
    logger.info("BpySidecar singleton spawned for /receipt-synthesis/render")
    return sidecar


def _vflip_png_bytes(image: Image.Image) -> bytes:
    """V-flip a PIL image and return PNG bytes.

    PIL stores images with origin top-left; Blender's image-texture sampler
    treats v=0 as the BOTTOM of the texture (OpenGL/UV convention). The
    receipt mesh's identity UV unwrap maps top-of-receipt to v=0 (PIL
    convention), so we pre-flip the texture to cancel out the conventions.
    See ``tests/synthesis/receipts/test_bbox_projector_full_chain.py``
    line 100-103 for the original derivation.
    """
    flipped = ImageOps.flip(image)
    buf = io.BytesIO()
    flipped.save(buf, format="PNG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Single-render endpoints
# ---------------------------------------------------------------------------


@router.post("/render", response_model=ReceiptRenderResponse)
def render(req: ReceiptRenderRequest) -> ReceiptRenderResponse:
    """Run the receipt synthesis pipeline once and return all stage outputs.

    Pipeline: ``layout -> content -> raster -> augraphy (if a preset is given)
    -> 3d_render (if ``render_3d=True``)``.

    Returns base64 PNGs per executed stage plus the consolidated
    ImageGroundTruth. The ``layout`` and ``content`` stages carry no image.

    **3D render latency note**: the first call with ``render_3d=True`` triggers
    the bpy sidecar cold start (~30-60s). Subsequent calls in the same process
    reuse the warm worker (~1-2s). The HF-friendly default render resolution
    is 384x384; override locally via ``RECEIPT_RENDER_RESOLUTION=1024``.
    """
    _validate_template(req.template)
    _validate_preset(req.augraphy_preset)

    # Validate hdri_id up-front (cheap) so a typo doesn't burn a 30-60s
    # sidecar cold start before failing.
    if req.render_3d and req.hdri_id is not None:
        valid_hdris = _list_hdri_ids()
        if req.hdri_id not in valid_hdris:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unknown hdri_id {req.hdri_id!r}. "
                    f"Available: {valid_hdris} (or omit hdri_id to use the default)."
                ),
            )

    if req.start_stage is not None or req.cached_image_id is not None:
        # Forward-compat parameters for the stage cache; accepted but not yet
        # honoured, logged so callers know they were received.
        logger.debug(
            f"render: start_stage/cached_image_id ignored "
            f"(start_stage={req.start_stage!r}, cached_image_id={req.cached_image_id!r})"
        )

    image_id = uuid4().hex
    try:
        outcome = synthesize_one(
            req.seed,
            template=req.template,
            augraphy_preset=req.augraphy_preset,
            sample_id=image_id,
        )
    except Exception as exc:
        logger.error(f"render failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"pipeline error: {exc}") from exc

    # Stages that produce no image (layout, content) report null; the rest
    # report the image as it stood when that stage finished.
    stages: list[StageOutput] = []
    final_b64: str | None = None
    for timing in outcome.stages:
        stage_image = outcome.stage_images.get(timing.stage)
        image_b64 = None if stage_image is None else _pil_to_png_b64(stage_image)
        if image_b64 is not None:
            final_b64 = image_b64
        stages.append(
            StageOutput(
                stage=timing.stage,  # type: ignore[arg-type]
                image_b64=image_b64,
                parameters=timing.parameters,
                elapsed_ms=timing.elapsed_ms,
            )
        )

    if final_b64 is None:  # pragma: no cover — raster always runs
        raise HTTPException(status_code=500, detail="pipeline produced no image")

    # The 3D stage below predates the v0.4 refactor and was written against
    # loose locals; bind them from the outcome so both features compose.
    final_image = outcome.image
    raster_image = outcome.stage_images.get("raster", outcome.image)

    # --- Stage 4: 3d_render (optional, v0.3d) -----------------------------------
    if req.render_3d:
        t3 = time.perf_counter()
        try:
            three_d_image, three_d_b64 = _run_3d_stage(
                texture_image=final_image,
                ground_truth=outcome.ground_truth,
                raster_size=raster_image.size,
                seed=req.seed,
                hdri_id=req.hdri_id,
                curl_strength=req.curl_strength,
            )
        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"3d_render stage failed: {exc}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"3d_render stage error: {exc}") from exc
        stages.append(
            StageOutput(
                stage="3d_render",
                image_b64=three_d_b64,
                parameters={
                    "hdri_id": req.hdri_id,
                    "curl_strength": req.curl_strength,
                    "resolution": list(_get_3d_resolution()),
                },
                elapsed_ms=_elapsed_ms(t3),
            )
        )
        final_image = three_d_image
        final_b64 = three_d_b64

    logger.info(
        f"render: image_id={image_id} template={req.template} seed={req.seed} "
        f"preset={req.augraphy_preset!r} render_3d={req.render_3d} "
        f"stages={[s.stage for s in stages]} size={final_image.size}"
    )

    return ReceiptRenderResponse(
        image_id=image_id,
        final_image_b64=final_b64,
        ground_truth=outcome.ground_truth,
        stages=stages,
        pipeline_version=PIPELINE_VERSION,
    )


def _elapsed_ms(start: float) -> int:
    """Milliseconds since a ``perf_counter`` timestamp.

    Kept local rather than imported from ``batch`` -- that module's copy is
    private, and the 3D stage is the router's own orchestration.
    """
    return int((time.perf_counter() - start) * 1000)


def _run_3d_stage(
    *,
    texture_image: Image.Image,
    ground_truth,
    raster_size: tuple[int, int],
    seed: int,
    hdri_id: str | None,
    curl_strength: float,
) -> tuple[Image.Image, str]:
    """Run the v0.3d 3D render path entirely inside the sidecar worker.

    Steps:
        1. V-flip the texture (PIL top-left -> Blender bottom-left UV) and
           encode as PNG bytes for the IPC boundary.
        2. Serialize the GT tokens to JSON-friendly dicts.
        3. Submit a single render-and-project job to the bpy sidecar. The
           worker builds the scene once, attaches the texture, deforms the
           paper, runs ``render_eevee``, then projects every token through
           ``project_token_full`` against that exact mesh + scene + UV/depth
           passes. Returns the rendered image + projected token dicts.
        4. Replace ``ground_truth.tokens`` with the projected versions
           (rehydrated through Pydantic for schema validation).

    Why one job and not "render then project"? bpy is a global mutable state
    machine. If the parent process imports bpy to run the projector after
    the sidecar has been used, we get a segfault on macOS (re-init collides
    with the worker's spawn-time bpy init). Doing both render + project in
    the worker keeps the parent bpy-free, which is the entire point of the
    sidecar pattern.
    """
    # --- 1. V-flip + encode the texture for the worker ---------------------
    tex_bytes = _vflip_png_bytes(texture_image)
    render_size = _get_3d_resolution()

    # --- 2. Serialize GT tokens for IPC ------------------------------------
    tokens_json = [t.model_dump(mode="json") for t in ground_truth.tokens]

    # --- 3. Submit one render-and-project job to the sidecar --------------
    sidecar = _get_sidecar()
    result = sidecar.render(
        seed=seed,
        hdri_id=hdri_id,
        curl_strength=curl_strength,
        fold_count=1,
        resolution=render_size,
        timeout=_SIDECAR_RENDER_TIMEOUT,
        texture_png_bytes=tex_bytes,
        tokens_json=tokens_json,
        raster_size=raster_size,
    )
    assert isinstance(
        result, tuple
    ), "sidecar must return (image, projected_tokens) when tokens_json is supplied"
    rendered_image, projected_token_dicts = result

    # --- 4. Rehydrate the projected tokens into the GT --------------------
    from document_simulator.synthesis.receipts.schema import TokenGroundTruth

    ground_truth.tokens = [TokenGroundTruth.model_validate(t) for t in projected_token_dicts]

    return rendered_image, _pil_to_png_b64(rendered_image)


@router.get("/templates", response_model=TemplateListResponse)
def list_templates() -> TemplateListResponse:
    """List all available templates with display metadata for the UI dropdown."""
    items = []
    for tid in TEMPLATE_IDS:
        name, description = _TEMPLATE_DISPLAY.get(
            tid, (tid.replace("_", " ").title(), f"Receipt template {tid!r}.")
        )
        items.append(
            TemplateInfo(
                id=tid,
                name=name,
                description=description,
                sample_token_count=_estimate_token_count(tid),
            )
        )
    return TemplateListResponse(templates=items)


@router.get("/augraphy-presets", response_model=AugraphyPresetListResponse)
def list_augraphy_presets() -> AugraphyPresetListResponse:
    """List all Augraphy preset names supported by the post-render stage."""
    return AugraphyPresetListResponse(presets=list(SUPPORTED_PRESETS))


@lru_cache(maxsize=1)
def _hdri_thumbnails_payload() -> HDRIListResponse:
    """Compute the HDRI thumbnail payload once and cache for the process lifetime.

    Reads ``data/hdri/*.thumbnail.png`` (pre-baked at v0.3a build time),
    base64-encodes each, and returns the list keyed by HDRI id (file stem).
    A missing thumbnail file for a given HDR is logged and skipped — we'd
    rather degrade gracefully than 500 the whole UI when one thumbnail is
    AWOL.
    """
    items: list[HDRIInfo] = []
    for hdri_id in _list_hdri_ids():
        thumb_path = _HDRI_DIR / f"{hdri_id}.thumbnail.png"
        if not thumb_path.exists():
            logger.warning(
                "hdri_id={} has no thumbnail at {}; skipping in /hdri-thumbnails",
                hdri_id,
                thumb_path,
            )
            continue
        b64 = base64.b64encode(thumb_path.read_bytes()).decode("ascii")
        items.append(
            HDRIInfo(
                id=hdri_id,
                # Pretty-name: snake_case -> Title Case (e.g. "office_warm" -> "Office Warm").
                name=hdri_id.replace("_", " ").title(),
                thumbnail_b64=b64,
            )
        )
    return HDRIListResponse(hdris=items)


@router.get("/hdri-thumbnails", response_model=HDRIListResponse)
def list_hdri_thumbnails() -> HDRIListResponse:
    """List bundled HDRIs with base64 thumbnails (FDD #29 v0.3d AC-5d).

    Thumbnails are pre-baked 128x128 PNGs in ``data/hdri/{id}.thumbnail.png``.
    The payload is computed once per process and cached via ``lru_cache``,
    so repeated calls cost only a dict lookup.
    """
    return _hdri_thumbnails_payload()

# ---------------------------------------------------------------------------
# Batch endpoints (v0.4)
#
# `api/jobs.py` covers the lifecycle we need (status / progress / error) so it
# is reused rather than forked. It has no field for a structured result, and it
# is not this stage's file to change, so the BatchResult is parked in a
# module-level side table keyed by the same job id.
# ---------------------------------------------------------------------------

_BATCH_META: dict[str, dict[str, str]] = {}
_BATCH_RESULTS: dict[str, BatchResult] = {}


def _dataset_dir(dataset: str) -> Path:
    """Resolve a dataset name to its directory under :data:`BATCH_ROOT`.

    ``ReceiptBatchRequest.dataset`` is pattern-validated to a single path
    segment, but resolve-and-compare anyway: this is the boundary where a
    request decides where the server writes, and a defence that does not depend
    on a regex staying correct is worth the three lines.
    """
    root = BATCH_ROOT.resolve()
    candidate = (root / dataset).resolve()
    if candidate != root and root not in candidate.parents:
        raise HTTPException(status_code=400, detail=f"Invalid dataset name {dataset!r}")
    return candidate


def _run_batch_job(job_id: str, req: ReceiptBatchRequest, out_dir: Path) -> None:
    """Background task: run the batch and record its result against the job."""
    update_job(job_id, status="running")

    def _on_progress(progress: BatchProgress) -> None:
        update_job(job_id, progress=progress.fraction)

    try:
        result = run_batch(
            req.n,
            req.seed,
            out_dir,
            workers=req.workers,
            augraphy_preset=req.augraphy_preset,
            template=req.template,
            resume=req.resume,
            progress=_on_progress,
        )
    except Exception as exc:
        logger.error(f"receipt batch job {job_id} failed: {exc}", exc_info=True)
        update_job(job_id, status="failed", error=str(exc))
        return

    _BATCH_RESULTS[job_id] = result
    # A batch with per-sample failures still *ran*; the failures are reported in
    # the status body. "failed" is reserved for a run that produced nothing.
    status = "done" if result.n_written or result.n_skipped else "failed"
    error = None if result.ok else f"{result.n_failed} of {result.n_requested} samples failed"
    update_job(job_id, status=status, progress=1.0, error=error)
    logger.info(
        f"receipt batch job {job_id}: written={result.n_written} "
        f"skipped={result.n_skipped} failed={result.n_failed}"
    )


@router.post("/batch", response_model=ReceiptBatchStartResponse, status_code=202)
def start_batch(
    req: ReceiptBatchRequest, background_tasks: BackgroundTasks
) -> ReceiptBatchStartResponse:
    """Start a resumable batch generation job.

    The job is planned entirely from ``(n, seed)``, so re-posting the same
    request against the same dataset resumes it: already-persisted samples are
    skipped rather than duplicated.
    """
    if req.template is not None:
        _validate_template(req.template)
    _validate_preset(req.augraphy_preset)

    out_dir = _dataset_dir(req.dataset)
    job_id = create_job()
    _BATCH_META[job_id] = {"dataset": req.dataset, "out_dir": str(out_dir)}

    background_tasks.add_task(_run_batch_job, job_id, req, out_dir)
    logger.info(
        f"receipt batch job {job_id} queued: n={req.n} seed={req.seed} "
        f"dataset={req.dataset!r} out={out_dir}"
    )
    return ReceiptBatchStartResponse(
        job_id=job_id, n=req.n, seed=req.seed, dataset=req.dataset, out_dir=str(out_dir)
    )


def _require_job(job_id: str) -> tuple[object, dict[str, str]]:
    """Fetch a batch job and its metadata, or 404."""
    job = get_job(job_id)
    meta = _BATCH_META.get(job_id)
    if job is None or meta is None:
        raise HTTPException(status_code=404, detail=f"Batch job {job_id!r} not found.")
    return job, meta


@router.get("/batch/{job_id}", response_model=ReceiptBatchStatusResponse)
def get_batch_status(job_id: str) -> ReceiptBatchStatusResponse:
    """Return progress and, once finished, the per-sample failure report."""
    job, meta = _require_job(job_id)
    result = _BATCH_RESULTS.get(job_id)

    response = ReceiptBatchStatusResponse(
        job_id=job_id,
        status=job.status,  # type: ignore[attr-defined]
        progress=job.progress,  # type: ignore[attr-defined]
        dataset=meta["dataset"],
        out_dir=meta["out_dir"],
        error=job.error,  # type: ignore[attr-defined]
    )
    if result is not None:
        response.n_requested = result.n_requested
        response.n_written = result.n_written
        response.n_skipped = result.n_skipped
        response.n_failed = result.n_failed
        response.elapsed_s = result.elapsed_s
        response.failures = [
            ReceiptBatchFailure(
                index=f.index,
                sample_id=f.sample_id,
                seed=f.seed,
                spec_id=f.spec_id,
                error=f.error,
            )
            for f in result.failures
        ]
    return response


@router.get("/batch/{job_id}/samples", response_model=ReceiptBatchSampleListResponse)
def list_batch_samples(
    job_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> ReceiptBatchSampleListResponse:
    """Page through the dataset manifest for a batch job.

    Reads the manifest rather than the in-memory result so a resumed dataset
    lists every sample it contains, not only the ones this job wrote.
    """
    _, meta = _require_job(job_id)
    entries = read_manifest(Path(meta["out_dir"]))
    window = entries[offset : offset + limit]
    return ReceiptBatchSampleListResponse(
        job_id=job_id,
        dataset=meta["dataset"],
        total=len(entries),
        offset=offset,
        samples=[
            ReceiptBatchSample(
                image_id=e["image_id"],
                image_path=str(e.get("image_path", f"images/{e['image_id']}.png")),
                gt_path=str(e.get("gt_path", f"ground_truth/{e['image_id']}.gt.json")),
                n_tokens=int(e.get("n_tokens", 0)),
                generated_at=e.get("generated_at"),
                pipeline_version=e.get("pipeline_version"),
            )
            for e in window
        ],
    )


@router.get("/batch/{job_id}/download")
def download_batch(job_id: str) -> StreamingResponse:
    """Download a finished batch's dataset (images + GT + manifest) as a ZIP."""
    job, meta = _require_job(job_id)
    if job.status not in {"done", "failed"}:  # type: ignore[attr-defined]
        raise HTTPException(
            status_code=409,
            detail=f"Batch job {job_id!r} is still running (status={job.status}).",  # type: ignore[attr-defined]
        )

    out_dir = Path(meta["out_dir"])
    if not out_dir.is_dir():
        raise HTTPException(status_code=404, detail=f"Dataset {meta['dataset']!r} not on disk.")

    members = sorted(p for p in out_dir.rglob("*") if p.is_file())
    total = sum(p.stat().st_size for p in members)
    if total > _MAX_ZIP_BYTES:
        raise HTTPException(
            status_code=413,
            detail=(
                f"Dataset is {total / 1e6:.0f} MB, above the "
                f"{_MAX_ZIP_BYTES / 1e6:.0f} MB download limit; copy it from {out_dir} instead."
            ),
        )

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in members:
            zf.write(path, arcname=str(path.relative_to(out_dir)))
    buf.seek(0)

    return StreamingResponse(
        iter([buf.read()]),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{meta["dataset"]}_receipts.zip"'},
    )
