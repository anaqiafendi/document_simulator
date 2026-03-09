"""Pydantic request/response models for the Document Simulator API."""

from __future__ import annotations

from pydantic import BaseModel


class TemplateResponse(BaseModel):
    """Response model for POST /api/template."""

    image_b64: str
    width_px: int
    height_px: int
    dpi: int = 150
    is_pdf: bool = False


class PreviewSample(BaseModel):
    """A single preview sample with seed and base64-encoded image."""

    seed: int
    image_b64: str


class PreviewRequest(BaseModel):
    """Request model for POST /api/preview."""

    synthesis_config: dict
    seeds: list[int] = [42, 43, 44]
    show_overlays: bool = False
    template_b64: str | None = None  # base64 PNG; when None, a blank canvas is used


class PreviewResponse(BaseModel):
    """Response model for POST /api/preview."""

    samples: list[PreviewSample]


class GenerateRequest(BaseModel):
    """Request model for POST /api/generate."""

    synthesis_config: dict
    n: int = 10


class GenerateResponse(BaseModel):
    """Response model for POST /api/generate."""

    job_id: str


class JobStatusResponse(BaseModel):
    """Response model for GET /api/jobs/{job_id}."""

    job_id: str
    status: str  # pending | running | done | failed
    progress: float = 0.0
    error: str | None = None
