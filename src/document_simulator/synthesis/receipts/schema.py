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

from pydantic import BaseModel, ConfigDict, computed_field, model_validator

from document_simulator.synthesis.receipts.layout.spec import (
    BlockType,
    MoneyRole,
    ReceiptStyle,
)

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


# ---------------------------------------------------------------------------
# Layout blocks (v0.4)
#
# A receipt is an ordered stack of typed blocks. The content stage resolves
# every block to concrete labels and amounts so the Jinja template stays dumb --
# all arithmetic stays in Python where it is testable.
# ---------------------------------------------------------------------------


class MoneyRow(BaseModel):
    """One resolved money row: role, its printed label, and its value.

    ``amount`` is set for numeric rows (subtotal, tax, change). ``text`` is set
    for rows that print a code rather than a sum (auth reference, card entry).
    """

    model_config = ConfigDict(frozen=True)

    role: MoneyRole
    label: str
    amount: float | None = None
    text: str | None = None


class MetaField(BaseModel):
    """A two-column metadata pair, e.g. ``Table`` / ``14``."""

    model_config = ConfigDict(frozen=True)

    title: str
    value: str


class ReceiptBlock(BaseModel):
    """One stacked band of a receipt.

    A single model with optional per-type fields rather than a discriminated
    union: blocks are consumed by one Jinja loop that dispatches on ``type``,
    and a union would force the template to know seven model names.
    """

    model_config = ConfigDict(frozen=True)

    type: BlockType
    alignment: str = "CENTER"

    # HEADER
    logo_path: str | None = None
    business_details: str | None = None

    # ITEMS -- indices into Receipt.items, so the items stay single-sourced
    item_indices: tuple[int, ...] = ()
    money_rows: tuple[MoneyRow, ...] = ()
    show_quantity: bool = True

    # CUSTOM / DATE
    text: str | None = None

    # BARCODE
    barcode_value: str | None = None

    # META
    left_fields: tuple[MetaField, ...] = ()
    right_fields: tuple[MetaField, ...] = ()

    # Separator drawn below this block, in taxonomy vocabulary (DASHES, STARS,
    # EMPTY, NONE, ...). Resolved to CSS by the renderer.
    bottom_divider: str = "NONE"


class Receipt(BaseModel):
    """Synthetic receipt content: merchant, items, tax, payment."""

    merchant: str
    address: str
    items: list[LineItem]
    tax_rate: float
    payment_last4: str

    # --- optional money modifiers (v0.4) ------------------------------------
    # All default to None so a Receipt built the v0.2 way is arithmetically
    # identical: total stays subtotal + tax.
    discount: float | None = None
    tip: float | None = None
    tender: float | None = None
    currency: str = "USD"

    # --- layout (v0.4) ------------------------------------------------------
    # Empty by default so the five hand-written templates, which read only the
    # fields above, keep rendering unchanged.
    sections: tuple[ReceiptBlock, ...] = ()
    style: ReceiptStyle | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def subtotal(self) -> float:
        """Sum of line totals, before discount and tax."""
        return round(sum(item.total for item in self.items), 2)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def taxable_base(self) -> float:
        """Subtotal after discount -- the amount tax is actually charged on."""
        return round(self.subtotal - (self.discount or 0.0), 2)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def tax(self) -> float:
        """Tax on the discounted subtotal.

        With no discount this is ``subtotal * tax_rate``, matching v0.2.
        """
        return round(self.taxable_base * self.tax_rate, 2)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total(self) -> float:
        """Discounted subtotal + tax + tip."""
        return round(self.taxable_base + self.tax + (self.tip or 0.0), 2)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def change(self) -> float | None:
        """Cash returned, or None when no tender was recorded."""
        if self.tender is None:
            return None
        return round(self.tender - self.total, 2)

    @model_validator(mode="after")
    def _check_money_invariants(self) -> Receipt:
        """Reject receipts whose printed numbers would not add up.

        This data trains extraction models. A receipt whose tender is less than
        its total, or whose discount exceeds its subtotal, teaches the model
        arithmetic that is simply wrong -- worse than having no example at all.
        """
        if self.discount is not None:
            if self.discount < 0:
                raise ValueError("discount must not be negative")
            if self.discount > self.subtotal:
                raise ValueError(f"discount {self.discount} exceeds subtotal {self.subtotal}")
        if self.tip is not None and self.tip < 0:
            raise ValueError("tip must not be negative")
        if self.tender is not None and self.tender < self.total:
            raise ValueError(f"tender {self.tender} is less than total {self.total}")
        return self


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
