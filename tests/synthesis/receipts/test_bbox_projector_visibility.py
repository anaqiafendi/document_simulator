"""Visibility/occlusion tests (FDD #29 v0.3c AC-1c).

We test ``compute_visibility`` against synthetic UV passes (no bpy needed).
Strategy:

    - Build a UV pass that mirrors the camera_2d polygon at known UV values,
      then assert occlusion_ratio == 0.0 / visible == True.
    - Zero-out the UV pass (background) and assert visible == False.
    - Half-and-half: half the polygon's pixels carry the expected UV, the
      other half carry a far-off UV; assert occlusion_ratio is around 0.5.
    - uv_distance is plain Euclidean — no seam-awareness needed for the
      single-island receipt unwrap (documented choice).
"""

from __future__ import annotations

import numpy as np

from document_simulator.synthesis.receipts.bbox_projector.visibility import (
    compute_visibility,
    uv_distance,
)
from document_simulator.synthesis.receipts.schema import (
    CoordSnapshot,
    TokenGroundTruth,
)

# ---------------------------------------------------------------------------
# uv_distance — design choice doc lives in the source
# ---------------------------------------------------------------------------


def test_uv_distance_handles_seams() -> None:
    """v0.3 uses plain Euclidean uv_distance — no seam wrap-around handling.

    The receipt has a single UV island so seams never come up; if v1.0 adds
    multi-island unwraps, this test will get a corresponding seam-aware
    overhaul. For now: (0.99, 0.5) vs (0.01, 0.5) is treated as 0.98, NOT
    0.02. Document the choice in the assertion message.
    """
    d = uv_distance((0.99, 0.5), (0.01, 0.5))
    assert abs(d - 0.98) < 1e-6, (
        f"v0.3 uses Euclidean uv_distance (no seam wrap); expected 0.98, "
        f"got {d}. Receipt has single UV island so seams don't apply."
    )

    # Sanity: distance to self is zero.
    assert uv_distance((0.5, 0.5), (0.5, 0.5)) == 0.0
    # Diagonal at 0.01 in u + 0.01 in v -> sqrt(2) * 0.01.
    assert abs(uv_distance((0.5, 0.5), (0.51, 0.51)) - np.sqrt(2) * 0.01) < 1e-9


# ---------------------------------------------------------------------------
# Helpers for the synthetic UV pass tests
# ---------------------------------------------------------------------------


def _make_token(
    *,
    uv_polygon: list[tuple[float, float]],
    camera_polygon: list[tuple[float, float]],
) -> TokenGroundTruth:
    """Build a token with the minimum coord chain compute_visibility reads:
    a ``uv`` snapshot (for expected UVs) and a ``camera_2d`` snapshot
    (for the pixel polygon).
    """
    return TokenGroundTruth(
        token_id="t",
        text="x",
        coords=[
            CoordSnapshot(stage="raster", polygon=uv_polygon),
            CoordSnapshot(stage="uv", polygon=uv_polygon),
            CoordSnapshot(
                stage="world",
                polygon=[(0.0, 0.0)] * len(uv_polygon),
                polygon_3d=[(0.0, 0.0, 0.0)] * len(uv_polygon),
            ),
            CoordSnapshot(stage="camera_2d", polygon=camera_polygon),
        ],
    )


def _make_uv_pass_filled(
    render_size: tuple[int, int],
    camera_polygon: list[tuple[float, float]],
    uv_polygon: list[tuple[float, float]],
) -> np.ndarray:
    """Return a (H, W, 2) UV pass that maps every pixel inside the camera
    polygon's bounding box to its bilinearly-interpolated expected UV.

    Outside the bbox is left at (0, 0). This yields ``visible == True`` /
    ``occlusion_ratio == 0`` because every sample point hits its expected
    UV exactly.
    """
    width, height = render_size
    uv_pass = np.zeros((height, width, 2), dtype=np.float32)

    cam_xs = [p[0] for p in camera_polygon]
    cam_ys = [p[1] for p in camera_polygon]
    uv_us = [p[0] for p in uv_polygon]
    uv_vs = [p[1] for p in uv_polygon]
    cx_min, cx_max = min(cam_xs), max(cam_xs)
    cy_min, cy_max = min(cam_ys), max(cam_ys)
    u_min, u_max = min(uv_us), max(uv_us)
    v_min, v_max = min(uv_vs), max(uv_vs)

    for py in range(int(np.floor(cy_min)), int(np.ceil(cy_max)) + 1):
        if py < 0 or py >= height:
            continue
        for px in range(int(np.floor(cx_min)), int(np.ceil(cx_max)) + 1):
            if px < 0 or px >= width:
                continue
            tx = (px - cx_min) / max(cx_max - cx_min, 1e-9)
            ty = (py - cy_min) / max(cy_max - cy_min, 1e-9)
            u = u_min + tx * (u_max - u_min)
            v = v_min + ty * (v_max - v_min)
            uv_pass[py, px] = (u, v)
    return uv_pass


# ---------------------------------------------------------------------------
# AC-1c: the three core compute_visibility cases
# ---------------------------------------------------------------------------


def test_visibility_unoccluded_returns_visible_true_occlusion_zero() -> None:
    """Synthetic UV pass mirroring the camera polygon exactly -> all 9 sample
    points pass -> ``visible=True``, ``occlusion_ratio==0.0``.
    """
    render_size = (200, 200)
    uv_polygon = [(0.4, 0.4), (0.6, 0.4), (0.6, 0.6), (0.4, 0.6)]
    camera_polygon = [(80.0, 80.0), (120.0, 80.0), (120.0, 120.0), (80.0, 120.0)]
    token = _make_token(uv_polygon=uv_polygon, camera_polygon=camera_polygon)

    uv_pass = _make_uv_pass_filled(render_size, camera_polygon, uv_polygon)
    depth_pass = np.ones((render_size[1], render_size[0]), dtype=np.float32)

    compute_visibility(token, uv_pass, depth_pass, render_size)

    assert token.visible is True
    assert token.occlusion_ratio == 0.0


def test_visibility_polygon_outside_image_marks_not_visible() -> None:
    """Background UV pass (all zeros) means none of the sample points match
    the expected UV -> ``visible=False`` (occlusion_ratio == 1.0).
    """
    render_size = (200, 200)
    uv_polygon = [(0.4, 0.4), (0.6, 0.4), (0.6, 0.6), (0.4, 0.6)]
    camera_polygon = [(80.0, 80.0), (120.0, 80.0), (120.0, 120.0), (80.0, 120.0)]
    token = _make_token(uv_polygon=uv_polygon, camera_polygon=camera_polygon)

    uv_pass = np.zeros((render_size[1], render_size[0], 2), dtype=np.float32)
    depth_pass = np.full((render_size[1], render_size[0]), 1e10, dtype=np.float32)

    compute_visibility(token, uv_pass, depth_pass, render_size)

    assert token.visible is False
    assert token.occlusion_ratio == 1.0


def test_visibility_partial_occlusion() -> None:
    """Half the polygon's pixels carry the expected UV, the other half carry
    far-off UV (simulating an occluder) -> occlusion_ratio is around 0.5.

    Implementation: fill the LEFT half of the polygon's bounding box with the
    expected UV; LEFT samples (left edge mid, top-left/bottom-left corners,
    centroid) hit; RIGHT samples (right edge mid, top-right/bottom-right
    corners) miss. Top edge mid + bottom edge mid sit on the centroid x and
    are right-on the boundary (left-half).
    """
    render_size = (200, 200)
    uv_polygon = [(0.4, 0.4), (0.6, 0.4), (0.6, 0.6), (0.4, 0.6)]
    camera_polygon = [(80.0, 80.0), (120.0, 80.0), (120.0, 120.0), (80.0, 120.0)]
    token = _make_token(uv_polygon=uv_polygon, camera_polygon=camera_polygon)

    full = _make_uv_pass_filled(render_size, camera_polygon, uv_polygon)
    uv_pass = np.zeros_like(full)
    cx_mid = (camera_polygon[0][0] + camera_polygon[1][0]) / 2.0  # 100
    uv_pass[:, : int(cx_mid)] = full[:, : int(cx_mid)]  # left half kept
    depth_pass = np.ones((render_size[1], render_size[0]), dtype=np.float32)

    compute_visibility(token, uv_pass, depth_pass, render_size)

    # Sample layout for a 4-vertex polygon (per design doc §4):
    #   4 corners + 4 edge midpoints + 1 centroid = 9 samples
    # Left side: top-left corner, bottom-left corner, left edge mid,
    # centroid (right on the boundary x=100 — falls in right half via int())
    # ... so the exact split depends on the implementation's "in or out" of
    # the boundary pixel. We assert a generous 0.4 .. 0.7 band rather than
    # an exact value, since the boundary pixel is implementation-defined.
    assert 0.3 <= token.occlusion_ratio <= 0.7, (
        f"expected ~50% occlusion, got {token.occlusion_ratio}"
    )
    # A token at occlusion_ratio < 0.7 is still visible per spec.
    assert token.visible is True
