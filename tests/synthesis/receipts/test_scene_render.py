"""Unit tests for ``synthesis.receipts.scene.render.render_eevee``.

Covers FDD #29 v0.3a AC-6a:
    render_eevee returns (PIL.Image, np.ndarray UV pass, np.ndarray depth pass)
    with shapes (H, W, 3 RGB) (H, W, 2) (H, W) and the documented value ranges.

Note (deviation from FDD): bpy 4.2's "BLENDER_EEVEE_NEXT" engine does NOT
expose a UV pass on the View Layer (the ``UV`` socket on
``CompositorNodeRLayers`` stays disabled even when ``use_pass_uv = True``).
The UV + depth passes are produced by Cycles (1 sample, deterministic) while
the photoreal RGB stays on Eevee Next. See render.py docstring for details.
"""

from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

bpy = pytest.importorskip("bpy")  # noqa: F811

from document_simulator.synthesis.receipts.scene import (  # noqa: E402
    build_scene,
    render_eevee,
)


def _bpy_reset() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=False)


def test_render_eevee_returns_image_uv_depth() -> None:
    """AC-6a: render_eevee returns (PIL.Image, uv_pass[H,W,2], depth_pass[H,W])."""
    _bpy_reset()
    scene = build_scene(seed=42, hdri_id=None)
    rgb, uv_pass, depth_pass = render_eevee(scene, resolution=(128, 128))

    assert isinstance(rgb, Image.Image)
    assert rgb.size == (128, 128)

    assert isinstance(uv_pass, np.ndarray)
    assert uv_pass.shape == (128, 128, 2), f"expected (H,W,2), got {uv_pass.shape}"
    assert uv_pass.dtype.kind == "f"

    assert isinstance(depth_pass, np.ndarray)
    assert depth_pass.shape == (128, 128), f"expected (H,W), got {depth_pass.shape}"
    assert depth_pass.dtype.kind == "f"


def test_render_eevee_uv_pass_in_unit_square() -> None:
    """AC-6a: UV pass values must lie in [0,1] on receipt pixels.

    Background pixels (no mesh hit) are 0 by Cycles convention. Receipt
    pixels carry their (u, v). We assert: at least 5% of pixels have
    non-zero UV, and the maximum u and v are <= 1 + epsilon.
    """
    _bpy_reset()
    scene = build_scene(seed=42, hdri_id=None)
    _rgb, uv_pass, _depth = render_eevee(scene, resolution=(128, 128))

    # mask pixels that received a hit (UV != 0)
    hit_mask = (uv_pass[..., 0] > 0) | (uv_pass[..., 1] > 0)
    hit_fraction = hit_mask.mean()
    assert hit_fraction > 0.05, (
        f"expected the receipt to cover at least 5% of the frame, " f"got {hit_fraction:.3f}"
    )

    hit_uvs = uv_pass[hit_mask]
    assert hit_uvs.min() >= -1e-3
    assert hit_uvs.max() <= 1.0 + 1e-3, f"hit UVs out of unit square: max={hit_uvs.max()}"


def test_render_eevee_depth_pass_positive_finite() -> None:
    """AC-6a: depth pass on the receipt pixels must be positive and finite.

    Background depth is rendered as a very large value (Cycles convention:
    1e10 for "infinity"). Foreground depth must be a real, positive,
    finite distance from the camera.
    """
    _bpy_reset()
    scene = build_scene(seed=42, hdri_id=None)
    _rgb, uv_pass, depth_pass = render_eevee(scene, resolution=(128, 128))

    receipt_mask = (uv_pass[..., 0] > 0) | (uv_pass[..., 1] > 0)
    receipt_depth = depth_pass[receipt_mask]

    assert receipt_depth.size > 0, "no receipt pixels found"
    assert np.all(np.isfinite(receipt_depth)), "receipt depth must be finite"
    assert np.all(receipt_depth > 0), "receipt depth must be positive"
    assert receipt_depth.max() < 1e6, "receipt depth must not be the background sentinel"
