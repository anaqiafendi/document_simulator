"""Pydantic request/response models for the Document Simulator API."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel

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
    """

    template: str
    seed: int
    augraphy_preset: str | None = None
    start_stage: str | None = None
    cached_image_id: str | None = None


class StageOutput(BaseModel):
    """One pipeline stage's output, returned by the /render endpoint.

    The ``stage`` literal is intentionally narrow in v0.2; v0.3+ will widen
    it to include ``"3d_scene"``, ``"camera_fx"``, and ``"final_crop"``.
    """

    stage: Literal["content", "raster", "augraphy"]
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
