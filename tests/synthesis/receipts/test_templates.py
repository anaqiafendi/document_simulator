"""Unit tests for the 5 receipt templates (FDD #28 AC-2).

Each template is rendered once and checked for:
  - successful render (no exceptions, non-empty image),
  - >= MIN_TOKENS tagged tokens (template-specific threshold),
  - polygons are non-degenerate and inside image bounds.
"""

from __future__ import annotations

import pytest
from PIL import Image

from document_simulator.synthesis.receipts.content import make_receipt
from document_simulator.synthesis.receipts.render import render_receipt
from document_simulator.synthesis.receipts.schema import ImageGroundTruth

# Per-template configuration. Threshold of 8 is the FDD-spec minimum for the
# new templates; thermal_minimal is a known-good baseline at >=8 tokens.
_TEMPLATE_SPECS = (
    ("thermal_minimal", "thermal_minimal.html.j2", 8),
    ("restaurant_tip", "restaurant_tip.html.j2", 8),
    ("retail_multicol", "retail_multicol.html.j2", 8),
    ("a4_invoice", "a4_invoice.html.j2", 8),
    ("taxi_stub", "taxi_stub.html.j2", 8),
)


@pytest.mark.parametrize("template_id,template_file,min_tokens", _TEMPLATE_SPECS)
def test_template_renders_with_well_formed_tokens(
    template_id: str, template_file: str, min_tokens: int
) -> None:
    """AC-2: every template renders, emits >= min_tokens, polygons valid."""
    receipt = make_receipt(seed=42, template=template_id)
    image, gt = render_receipt(receipt, seed=42, template_name=template_file)

    # Render produced something usable.
    assert isinstance(image, Image.Image), f"{template_id}: image is not PIL.Image"
    assert isinstance(gt, ImageGroundTruth), f"{template_id}: gt is not ImageGroundTruth"
    width, height = image.size
    assert width > 0 and height > 0, f"{template_id}: degenerate image size {image.size}"

    # Token count threshold.
    assert (
        len(gt.tokens) >= min_tokens
    ), f"{template_id}: only {len(gt.tokens)} tokens (need >= {min_tokens})"

    # Every polygon: non-degenerate + inside image bounds (allow 2px slack
    # for sub-pixel rendering, matching v0.1's tolerance in test_render.py).
    for token in gt.tokens:
        polygon = token.coords[0].polygon
        assert len(polygon) >= 3, f"{template_id} {token.token_id}: polygon has <3 vertices"

        xs = [p[0] for p in polygon]
        ys = [p[1] for p in polygon]
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)

        assert x_max - x_min > 0, f"{template_id} {token.token_id}: zero width polygon"
        assert y_max - y_min > 0, f"{template_id} {token.token_id}: zero height polygon"

        assert -2 <= x_min and x_max <= width + 2, (
            f"{template_id} {token.token_id}: x out of bounds "
            f"[{x_min}, {x_max}] vs width {width}"
        )
        assert -2 <= y_min and y_max <= height + 2, (
            f"{template_id} {token.token_id}: y out of bounds "
            f"[{y_min}, {y_max}] vs height {height}"
        )
