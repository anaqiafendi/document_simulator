"""FastAPI router for the photoreal receipt synthesis pipeline (FDD #28 + #29).

Endpoints, all under ``/api/receipt-synthesis``:

  * ``POST /render``            — run the full pipeline once, return base64
                                   images per stage + the consolidated
                                   ImageGroundTruth. v0.3d adds optional 3D
                                   Eevee render via the bpy sidecar.
  * ``GET  /templates``         — list the 5 v0.2 templates with metadata.
  * ``GET  /augraphy-presets``  — list the available Augraphy preset names.
  * ``GET  /hdri-thumbnails``   — list bundled HDRIs with base64 thumbnails
                                   (FDD #29 v0.3d AC-5d).

The router intentionally mirrors the per-stage shape from
``docs/PHOTOREAL_RECEIPT_UI_DESIGN.md §3``; v0.3+ extends ``StageOutput.stage``
with new literals as the 3D and Camera FX stages land.
"""

from __future__ import annotations

import base64
import io
import os
import time
from functools import cache, lru_cache
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from loguru import logger
from PIL import Image, ImageOps

from document_simulator.api.models import (
    AugraphyPresetListResponse,
    HDRIInfo,
    HDRIListResponse,
    ReceiptRenderRequest,
    ReceiptRenderResponse,
    StageOutput,
    TemplateInfo,
    TemplateListResponse,
)
from document_simulator.synthesis.receipts.augraphy_pretreat import (
    SUPPORTED_PRESETS,
    apply_post_render,
)
from document_simulator.synthesis.receipts.content import make_receipt
from document_simulator.synthesis.receipts.render import render_receipt

router = APIRouter(prefix="/api/receipt-synthesis", tags=["receipt-synthesis"])

# Bumped from 0.2.0 once the 3D render path landed.
PIPELINE_VERSION = "0.3.0"

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

# ---------------------------------------------------------------------------
# Template registry (v0.2). Adding a 6th template is a code change here +
# a Jinja2 file + a SKU corpus binding in `content._TEMPLATE_REGISTRY`.
# ---------------------------------------------------------------------------

# (id, jinja2 filename, display name, description)
_TEMPLATES: tuple[tuple[str, str, str, str], ...] = (
    (
        "thermal_minimal",
        "thermal_minimal.html.j2",
        "Thermal Single-Column",
        "Classic 80mm thermal printer receipt with merchant header, line items, and totals.",
    ),
    (
        "restaurant_tip",
        "restaurant_tip.html.j2",
        "Restaurant w/ Tip Lines",
        "Sit-down restaurant receipt: server name, table, tip suggestions (15/18/20%).",
    ),
    (
        "retail_multicol",
        "retail_multicol.html.j2",
        "Retail Multi-Column",
        "Big-box retail receipt with a 3-column SKU / description / price grid.",
    ),
    (
        "a4_invoice",
        "a4_invoice.html.j2",
        "A4 Invoice",
        "Full-page A4 invoice layout with billing block, item table, and grand total.",
    ),
    (
        "taxi_stub",
        "taxi_stub.html.j2",
        "Taxi / Parking Stub",
        "Narrow rideshare or parking stub: driver, route, fare breakdown, tip line.",
    ),
)

_TEMPLATE_FILE_BY_ID: dict[str, str] = {tid: tfile for tid, tfile, _, _ in _TEMPLATES}
_VALID_TEMPLATE_IDS: frozenset[str] = frozenset(_TEMPLATE_FILE_BY_ID)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _elapsed_ms(start: float) -> int:
    """Convert a perf_counter start timestamp to elapsed integer milliseconds."""
    return int((time.perf_counter() - start) * 1000)


def _pil_to_png_b64(img: Image.Image) -> str:
    """Encode a PIL image as a base64 PNG string (no data: prefix)."""
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


@cache
def _sample_token_count(template_id: str) -> int:
    """Render the template once with seed=0 and report its token count.

    Memoised so the dropdown metadata is computed at most once per process.
    """
    receipt = make_receipt(seed=0, template=template_id)
    _, gt = render_receipt(receipt, seed=0, template_name=_TEMPLATE_FILE_BY_ID[template_id])
    return len(gt.tokens)


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
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/render", response_model=ReceiptRenderResponse)
def render(req: ReceiptRenderRequest) -> ReceiptRenderResponse:
    """Run the receipt synthesis pipeline once and return all stage outputs.

    Pipeline:
        content -> raster -> augraphy (if preset given) -> 3d_render (if
        ``render_3d=True``)

    Returns base64 PNGs per executed stage plus the consolidated
    ImageGroundTruth. The first ``content`` stage's image_b64 is always null
    (no image yet at that stage).

    **3D render latency note**: the first call with ``render_3d=True`` triggers
    the bpy sidecar cold start (~30-60s). Subsequent calls in the same process
    reuse the warm worker (~1-2s). The HF-friendly default render resolution
    is 384x384; override locally via ``RECEIPT_RENDER_RESOLUTION=1024``.
    """
    if req.template not in _VALID_TEMPLATE_IDS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown template {req.template!r}. Valid: {sorted(_VALID_TEMPLATE_IDS)}",
        )

    if req.augraphy_preset is not None and req.augraphy_preset not in SUPPORTED_PRESETS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unknown augraphy_preset {req.augraphy_preset!r}. "
                f"Supported: {list(SUPPORTED_PRESETS)}"
            ),
        )

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
        # Forward-compat parameters for v0.3+; ignored in v0.2 but logged so
        # callers know they were received.
        logger.debug(
            f"render: start_stage/cached_image_id ignored in v0.2 "
            f"(start_stage={req.start_stage!r}, cached_image_id={req.cached_image_id!r})"
        )

    image_id = uuid4().hex
    stages: list[StageOutput] = []

    # --- Stage 1: content (Faker) ------------------------------------------------
    t0 = time.perf_counter()
    try:
        receipt = make_receipt(seed=req.seed, template=req.template)
    except ValueError as exc:
        # Should never happen given the up-front validation above, but defend
        # against drift between the registries.
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.error(f"content stage failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"content stage error: {exc}") from exc
    stages.append(
        StageOutput(
            stage="content",
            image_b64=None,
            parameters={
                "template": req.template,
                "seed": req.seed,
                "n_items": len(receipt.items),
                "tax_rate": receipt.tax_rate,
            },
            elapsed_ms=_elapsed_ms(t0),
        )
    )

    # --- Stage 2: raster (WeasyPrint) -------------------------------------------
    t1 = time.perf_counter()
    try:
        image, ground_truth = render_receipt(
            receipt,
            seed=req.seed,
            template_name=_TEMPLATE_FILE_BY_ID[req.template],
        )
    except Exception as exc:
        logger.error(f"raster stage failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"raster stage error: {exc}") from exc
    raster_b64 = _pil_to_png_b64(image)
    stages.append(
        StageOutput(
            stage="raster",
            image_b64=raster_b64,
            parameters={
                "template_file": _TEMPLATE_FILE_BY_ID[req.template],
                "image_size": list(image.size),
                "n_tokens": len(ground_truth.tokens),
            },
            elapsed_ms=_elapsed_ms(t1),
        )
    )

    final_image = image
    final_b64 = raster_b64

    # --- Stage 3: augraphy (optional) -------------------------------------------
    if req.augraphy_preset is not None:
        t2 = time.perf_counter()
        try:
            degraded = apply_post_render(image, preset=req.augraphy_preset, seed=req.seed)
        except Exception as exc:
            logger.error(f"augraphy stage failed: {exc}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"augraphy stage error: {exc}") from exc
        degraded_b64 = _pil_to_png_b64(degraded)
        stages.append(
            StageOutput(
                stage="augraphy",
                image_b64=degraded_b64,
                parameters={"preset": req.augraphy_preset, "seed": req.seed},
                elapsed_ms=_elapsed_ms(t2),
            )
        )
        final_image = degraded
        final_b64 = degraded_b64

    # --- Stage 4: 3d_render (optional, v0.3d) -----------------------------------
    if req.render_3d:
        t3 = time.perf_counter()
        try:
            three_d_image, three_d_b64 = _run_3d_stage(
                texture_image=final_image,
                ground_truth=ground_truth,
                raster_size=image.size,
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
        ground_truth=ground_truth,
        stages=stages,
        pipeline_version=PIPELINE_VERSION,
    )


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
    items = [
        TemplateInfo(
            id=tid,
            name=name,
            description=description,
            sample_token_count=_sample_token_count(tid),
        )
        for tid, _, name, description in _TEMPLATES
    ]
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
