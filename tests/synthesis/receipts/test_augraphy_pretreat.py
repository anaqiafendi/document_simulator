"""Unit tests for synthesis.receipts.augraphy_pretreat (FDD #28 AC-3).

Covers:
  - apply_post_render returns a same-size PIL image,
  - same seed yields visually identical output (deterministic),
  - unknown preset name raises a clear error.
"""

from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from document_simulator.synthesis.receipts.augraphy_pretreat import apply_post_render


def _white_image(w: int = 200, h: int = 280) -> Image.Image:
    """Plain white test image — Augraphy effects produce visible diffs against white."""
    return Image.new("RGB", (w, h), color=(255, 255, 255))


def test_apply_post_render_returns_same_size_image() -> None:
    """AC-3: pixel-only ops must preserve image size (so GT polygons stay valid)."""
    img = _white_image(220, 320)
    out = apply_post_render(img, preset="light", seed=0)

    assert isinstance(out, Image.Image), "apply_post_render must return PIL.Image"
    assert (
        out.size == img.size
    ), f"size changed: {img.size} -> {out.size} (would invalidate raster polygons)"


def test_apply_post_render_deterministic_for_same_seed() -> None:
    """AC-3 + AC-8: same (preset, seed) on same input must yield byte-identical output."""
    img = _white_image()
    a = apply_post_render(img, preset="light", seed=123)
    b = apply_post_render(img, preset="light", seed=123)

    arr_a = np.array(a)
    arr_b = np.array(b)
    assert arr_a.shape == arr_b.shape, "deterministic check needs same-shape arrays"
    assert np.array_equal(arr_a, arr_b), (
        "apply_post_render is not deterministic for the same seed — "
        "v0.2 AC-8 (determinism) requires reproducible output"
    )


def test_apply_post_render_unknown_preset_raises_clearly() -> None:
    """AC-3: unknown preset name must raise (not silently fall back) so the API
    layer can surface the mistake to the caller.
    """
    img = _white_image()
    with pytest.raises((KeyError, ValueError)):
        apply_post_render(img, preset="nonexistent_preset_xyz", seed=0)
