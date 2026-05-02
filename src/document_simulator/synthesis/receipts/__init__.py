"""Photoreal receipt synthesis (v0.1 tracer bullet).

Public API:
    Receipt, LineItem, CoordSnapshot, TokenGroundTruth, ImageGroundTruth
        Pydantic models that lock the on-disk ground-truth schema.
    render_receipt(receipt, seed=0) -> (PIL.Image, ImageGroundTruth)
        Render a receipt to PNG with per-token raster bboxes.
    persist_sample(image, gt, dataset_root) -> None
        Write image + GT JSON + manifest line atomically.
    draw_overlay(image, gt, stage="raster") -> PIL.Image
        Annotate an image with token polygon outlines for visual inspection.

The schema is bumped manually via `PIPELINE_VERSION` on any stage-output-affecting change.
"""

from document_simulator.synthesis.receipts.overlay import draw_overlay
from document_simulator.synthesis.receipts.persist import persist_sample
from document_simulator.synthesis.receipts.render import render_receipt
from document_simulator.synthesis.receipts.schema import (
    CoordSnapshot,
    ImageGroundTruth,
    LineItem,
    Receipt,
    TokenGroundTruth,
)

PIPELINE_VERSION = "0.1.0"

__all__ = [
    "PIPELINE_VERSION",
    "CoordSnapshot",
    "ImageGroundTruth",
    "LineItem",
    "Receipt",
    "TokenGroundTruth",
    "draw_overlay",
    "persist_sample",
    "render_receipt",
]
