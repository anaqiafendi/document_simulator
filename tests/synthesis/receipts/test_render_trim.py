"""Tests for cutting a spec-driven receipt down to its printed length."""

from __future__ import annotations

import random

import numpy as np
from PIL import Image

from document_simulator.synthesis.receipts.content import make_receipt
from document_simulator.synthesis.receipts.layout import sample_spec, stratified_specs
from document_simulator.synthesis.receipts.render import (
    _RECEIPT_TAIL_PX,
    _trim_trailing_blank,
    render_receipt,
)


def _ink_rows(image: Image.Image) -> np.ndarray:
    """Row indices containing any non-white pixel."""
    return np.where((np.array(image.convert("L")) < 200).any(axis=1))[0]


def test_trim_removes_blank_tail_but_keeps_a_margin() -> None:
    image = Image.new("RGB", (100, 500), "white")
    for y in range(10, 40):
        for x in range(10, 90):
            image.putpixel((x, y), (0, 0, 0))

    trimmed = _trim_trailing_blank(image)

    assert trimmed.width == 100
    assert trimmed.height == 39 + _RECEIPT_TAIL_PX + 1


def test_trim_leaves_a_full_page_alone() -> None:
    """Nothing to cut when ink reaches the bottom."""
    image = Image.new("RGB", (50, 50), "black")
    assert _trim_trailing_blank(image).size == (50, 50)


def test_trim_leaves_a_blank_page_alone() -> None:
    """A page with no ink must not collapse to zero height."""
    image = Image.new("RGB", (50, 80), "white")
    assert _trim_trailing_blank(image).size == (50, 80)


def test_spec_driven_pages_are_cut_to_length() -> None:
    """AC: a spec-driven receipt is mostly print, not blank paper.

    The composable template renders onto a deliberately over-tall page so a
    block-heavy layout cannot overflow to page 2. Without trimming, a short
    receipt is ~80% white, and augraphy / the 3D scene / the camera all spend
    their budget photographing empty paper.
    """
    utilisation = []
    for spec in stratified_specs(12, seed=42):
        receipt = make_receipt(seed=42, spec=spec)
        image, _ = render_receipt(receipt, seed=42, template_name="composable.html.j2")
        rows = _ink_rows(image)
        assert len(rows) > 0, "receipt rendered blank"
        utilisation.append((rows.max() - rows.min() + 1) / image.height)

    assert min(utilisation) > 0.5, f"worst page is {min(utilisation):.0%} print"


def test_trimming_keeps_every_token_inside_the_image() -> None:
    """The crop must not orphan ground truth outside the image bounds."""
    for seed in range(6):
        spec = sample_spec(random.Random(seed))
        receipt = make_receipt(seed=seed, spec=spec)
        image, gt = render_receipt(receipt, seed=seed, template_name="composable.html.j2")

        assert gt.image_size == list(image.size) or tuple(gt.image_size) == image.size
        for token in gt.tokens:
            for x, y in token.coords[-1].polygon:
                assert -1 <= x <= image.width + 1, f"{token.token_id} x={x}"
                assert -1 <= y <= image.height + 1, f"{token.token_id} y={y}"


def test_receipt_length_varies_with_content() -> None:
    """Cut-to-length means page height carries information, as on real paper."""
    heights = set()
    for spec in stratified_specs(12, seed=7):
        receipt = make_receipt(seed=7, spec=spec)
        image, _ = render_receipt(receipt, seed=7, template_name="composable.html.j2")
        heights.add(image.height)
    assert len(heights) > 3, f"only {len(heights)} distinct heights"


def test_legacy_templates_keep_their_fixed_geometry() -> None:
    """The five hand-written templates must not change size."""
    receipt = make_receipt(seed=42, template="thermal_minimal")
    assert not receipt.sections  # no spec -> no trim path
    image, _ = render_receipt(receipt, seed=42, template_name="thermal_minimal.html.j2")
    rows = _ink_rows(image)
    assert rows.max() < image.height - 50, "expected untrimmed trailing whitespace"
