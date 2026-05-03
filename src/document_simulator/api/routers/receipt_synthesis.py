"""FastAPI router for the photoreal receipt synthesis pipeline (FDD #28).

Three endpoints, all under ``/api/receipt-synthesis``:

  * ``POST /render``           — run the full pipeline once, return base64
                                  images per stage + the consolidated ImageGroundTruth.
  * ``GET  /templates``        — list the 5 v0.2 templates with metadata.
  * ``GET  /augraphy-presets`` — list the available Augraphy preset names.

The router intentionally mirrors the per-stage shape from
``docs/PHOTOREAL_RECEIPT_UI_DESIGN.md §3``; v0.3+ extends ``StageOutput.stage``
with new literals as the 3D and Camera FX stages land.
"""

from __future__ import annotations

import base64
import io
import time
from functools import cache
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from loguru import logger
from PIL import Image

from document_simulator.api.models import (
    AugraphyPresetListResponse,
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

PIPELINE_VERSION = "0.2.0"

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


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/render", response_model=ReceiptRenderResponse)
def render(req: ReceiptRenderRequest) -> ReceiptRenderResponse:
    """Run the receipt synthesis pipeline once and return all stage outputs.

    Pipeline:
        content -> raster -> augraphy (if preset given)

    Returns base64 PNGs per executed stage plus the consolidated
    ImageGroundTruth. The first ``content`` stage's image_b64 is always null
    (no image yet at that stage).
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

    logger.info(
        f"render: image_id={image_id} template={req.template} seed={req.seed} "
        f"preset={req.augraphy_preset!r} stages={[s.stage for s in stages]} "
        f"size={final_image.size}"
    )

    return ReceiptRenderResponse(
        image_id=image_id,
        final_image_b64=final_b64,
        ground_truth=ground_truth,
        stages=stages,
        pipeline_version=PIPELINE_VERSION,
    )


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
