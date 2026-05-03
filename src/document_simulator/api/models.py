"""Pydantic request/response models for the Document Simulator API."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from document_simulator.synthesis.receipts.schema import ImageGroundTruth


class TemplateResponse(BaseModel):
    """Response model for POST /api/template."""

    image_b64: str
    width_px: int
    height_px: int
    dpi: int = 150
    is_pdf: bool = False
    page_count: int = 1
    template_id: str | None = None  # server-side key for raw PDF bytes


class PreviewSample(BaseModel):
    """A single preview sample with seed and base64-encoded image."""

    seed: int
    image_b64: str


class PreviewRequest(BaseModel):
    """Request model for POST /api/preview."""

    synthesis_config: dict
    seeds: list[int] = [42, 43, 44]
    show_overlays: bool = False
    template_b64: str | None = None  # base64 PNG of the current page
    current_page: int = 0  # which PDF page the preview is for; filters zones


class PreviewResponse(BaseModel):
    """Response model for POST /api/preview."""

    samples: list[PreviewSample]


class GenerateRequest(BaseModel):
    """Request model for POST /api/generate."""

    synthesis_config: dict
    n: int = 10
    template_b64: str | None = None  # base64 PNG of a single rendered page
    template_pdf_b64: str | None = None  # raw PDF bytes as base64; enables multi-page generation
    template_id: str | None = None  # server-side key returned by /api/template (preferred)


class GenerateResponse(BaseModel):
    """Response model for POST /api/generate."""

    job_id: str


class JobStatusResponse(BaseModel):
    """Response model for GET /api/jobs/{job_id}."""

    job_id: str
    status: str  # pending | running | done | failed
    progress: float = 0.0
    error: str | None = None


# ── Augmentation ──────────────────────────────────────────────────────────────


class AugmentMetadata(BaseModel):
    """Metadata returned alongside an augmented image."""

    preset: str
    width: int
    height: int
    filename: str


class AugmentResponse(BaseModel):
    """Response model for POST /api/augmentation/augment."""

    original_b64: str
    augmented_b64: str
    metadata: AugmentMetadata


class PresetsResponse(BaseModel):
    """Response model for GET /api/augmentation/presets."""

    presets: list[str]


# ── OCR ───────────────────────────────────────────────────────────────────────


class OcrResponse(BaseModel):
    """Response model for POST /api/ocr/recognize."""

    text: str
    boxes: list[list[list[float]]]
    scores: list[float]
    mean_confidence: float
    n_regions: int
    annotated_b64: str


# ── Batch ─────────────────────────────────────────────────────────────────────


class BatchJobResponse(BaseModel):
    """Response model for POST /api/batch/process."""

    job_id: str


class BatchStatusResponse(BaseModel):
    """Response model for GET /api/batch/jobs/{job_id}."""

    job_id: str
    status: str
    progress: float = 0.0
    error: str | None = None


# ── Evaluation ────────────────────────────────────────────────────────────────


class EvalJobResponse(BaseModel):
    """Response model for POST /api/evaluation/run."""

    job_id: str


class EvalStatusResponse(BaseModel):
    """Response model for GET /api/evaluation/jobs/{job_id}/status."""

    job_id: str
    status: str
    progress: float = 0.0
    error: str | None = None
    results: dict | None = None


# ── RL Training ───────────────────────────────────────────────────────────────


class RlJobResponse(BaseModel):
    """Response model for POST /api/rl/train."""

    job_id: str


class RlStatusResponse(BaseModel):
    """Response model for GET /api/rl/jobs/{job_id}/status."""

    job_id: str
    status: str
    progress: float = 0.0
    error: str | None = None
    step: int = 0
    reward: float = 0.0
    model_path: str | None = None


class RlMetricsResponse(BaseModel):
    """Response model for GET /api/rl/jobs/{job_id}/metrics."""

    job_id: str
    reward_curve: list[dict]


# ── Receipt Synthesis (FDD #28) ───────────────────────────────────────────────


class ReceiptRenderRequest(BaseModel):
    """Request model for POST /api/receipt-synthesis/render.

    ``start_stage`` and ``cached_image_id`` are accepted for forward-compat
    with v0.3+ (resume-from-stage caching) but are ignored in v0.2.

    v0.3d adds the 3D-render trio:

      * ``render_3d`` toggles the bpy scene + Eevee render stage. When False
        (default), the endpoint behaves exactly as v0.2.
      * ``hdri_id`` selects which HDRI from ``data/hdri/`` drives the world
        background. Ignored when ``render_3d=False``. ``None`` falls back
        to the first bundled HDRI.
      * ``curl_strength`` controls procedural paper curl in
        :func:`document_simulator.synthesis.receipts.scene.deform_paper`.
        Bounded ``[0.0, 0.5]`` so a fat-fingered slider can't crinkle the
        receipt off-camera.
    """

    template: str
    seed: int
    augraphy_preset: str | None = None
    start_stage: str | None = None
    cached_image_id: str | None = None
    # v0.3d additions
    render_3d: bool = False
    hdri_id: str | None = None
    curl_strength: float = Field(0.1, ge=0.0, le=0.5)


class StageOutput(BaseModel):
    """One pipeline stage's output, returned by the /render endpoint.

    The ``stage`` literal widens with each pipeline phase. v0.3d adds
    ``3d_render`` (Eevee output of the textured 3D receipt scene) and
    ``visibility`` (placeholder for a future stage that renders only the
    visibility mask — populated as a coord-trail field on TokenGroundTruth
    in v0.3c, but reserved here as a literal so the response schema is
    stable across the v0.3 series).
    """

    stage: Literal["content", "raster", "augraphy", "3d_render", "visibility"]
    image_b64: str | None  # null for "content" stage (no image yet)
    parameters: dict[str, Any]
    elapsed_ms: int


class ReceiptRenderResponse(BaseModel):
    """Response model for POST /api/receipt-synthesis/render."""

    image_id: str
    final_image_b64: str
    ground_truth: ImageGroundTruth
    stages: list[StageOutput]
    pipeline_version: str


class TemplateInfo(BaseModel):
    """Metadata for one template entry returned by GET /templates."""

    id: str
    name: str
    description: str
    sample_token_count: int  # estimated token count, used in dropdown UX


class TemplateListResponse(BaseModel):
    """Response model for GET /api/receipt-synthesis/templates."""

    templates: list[TemplateInfo]


class AugraphyPresetListResponse(BaseModel):
    """Response model for GET /api/receipt-synthesis/augraphy-presets."""

    presets: list[str]


class HDRIInfo(BaseModel):
    """Metadata for one HDRI returned by GET /hdri-thumbnails (FDD #29 AC-5d).

    The ``thumbnail_b64`` is a base64 PNG (no ``data:`` prefix) of the
    pre-rendered 128×128 thumbnail bundled alongside each ``.hdr`` file in
    ``data/hdri/``.
    """

    id: str
    name: str
    thumbnail_b64: str


class HDRIListResponse(BaseModel):
    """Response model for GET /api/receipt-synthesis/hdri-thumbnails."""

    hdris: list[HDRIInfo]
