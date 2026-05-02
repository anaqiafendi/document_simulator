"""Pydantic schema for the photoreal receipt synthesis pipeline (v0.1).

The schema is locked here — every later phase (v0.2 Faker variety, v0.3 3D rendering,
v1.0 camera FX) only *appends* `CoordSnapshot`s to the existing `TokenGroundTruth.coords`
chain rather than mutating prior fields.

See docs/features/feature_photoreal_receipt_synthesis.md §Design and
docs/PHOTOREALISTIC_RECEIPT_PIPELINE.md §4.1 for the design rationale.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, computed_field

# Stages of the coordinate-tracking chain. v0.1 only writes "raster"; later stages append.
CoordStage = Literal[
    "html",
    "raster",
    "uv",
    "world",
    "camera_2d",
    "camera_fx",
    "final_crop",
]


class LineItem(BaseModel):
    """One row in a receipt: SKU, quantity, unit price."""

    model_config = ConfigDict(frozen=False)

    sku: str
    qty: int
    unit_price: float

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total(self) -> float:
        """Line total (qty * unit_price), rounded to 2 decimal places."""
        return round(self.qty * self.unit_price, 2)


class Receipt(BaseModel):
    """Synthetic receipt content: merchant, items, tax, payment."""

    merchant: str
    address: str
    items: list[LineItem]
    tax_rate: float
    payment_last4: str

    @computed_field  # type: ignore[prop-decorator]
    @property
    def subtotal(self) -> float:
        """Sum of line totals."""
        return round(sum(item.total for item in self.items), 2)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def tax(self) -> float:
        """Tax computed from subtotal * tax_rate."""
        return round(self.subtotal * self.tax_rate, 2)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total(self) -> float:
        """Subtotal + tax."""
        return round(self.subtotal + self.tax, 2)


class CoordSnapshot(BaseModel):
    """One snapshot of a token's polygon at a specific pipeline stage.

    Each pipeline stage *appends* a snapshot to `TokenGroundTruth.coords`; prior
    snapshots are never overwritten. This makes intermediate-stage debugging
    tractable.
    """

    stage: CoordStage
    polygon: list[tuple[float, float]]
    polygon_3d: list[tuple[float, float, float]] | None = None


class TokenGroundTruth(BaseModel):
    """Ground truth for one text token in the rendered image."""

    token_id: str
    text: str
    semantic_role: str | None = None
    coords: list[CoordSnapshot]
    visible: bool = True
    occlusion_ratio: float = 0.0

    @property
    def final_polygon(self) -> list[tuple[float, float]]:
        """Polygon from the most recently appended CoordSnapshot."""
        return self.coords[-1].polygon


class ImageGroundTruth(BaseModel):
    """Per-image artifact, persisted as `{image_id}.gt.json`."""

    image_id: str
    image_path: Path
    image_size: tuple[int, int]
    tokens: list[TokenGroundTruth]
    receipt: Receipt
    seed: int
    pipeline_version: str
    # Placeholder for v0.3+ scene state (camera matrix, lights, mesh deform params).
    scene_state: None = None
