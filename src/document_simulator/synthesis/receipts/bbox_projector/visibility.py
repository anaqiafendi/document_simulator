"""Visibility / occlusion detection via UV-pass match (FDD #29 v0.3c AC-1c).

For each token, sample 9 points across its ``camera_2d`` polygon (4 corners
+ 4 edge midpoints + 1 centroid). For each sample:

    1. Read the rendered UV at that pixel from the UV pass.
    2. Compute the *expected* UV at the same sample by interpolating across
       the token's ``uv``-stage polygon (axis-aligned bilinear within the
       polygon's bounding box).
    3. The sample is "visible" iff the rendered UV is within ``UV_EPS`` of
       the expected UV (Euclidean — see design note below).

Then:

    occlusion_ratio = 1.0 - (visible_samples / 9)
    visible = occlusion_ratio < 0.7

**Design choice — uv_distance is plain Euclidean.** The receipt uses a
single UV island (per the v0.3a programmatic mesh), so seam wrap-around
never applies. (0.99, 0.5) vs (0.01, 0.5) is treated as 0.98 distance, not
0.02. If v1.0 introduces multi-island unwraps this becomes seam-aware.

**Design choice — sample layout.** A 4-vertex polygon gets the canonical
9-sample layout (corners + edge mids + centroid). Higher-vertex polygons
(e.g. post-subdivision world-space polygons projected back) fall back to the
**bounding-box** 9-point layout (bbox corners + bbox edge mids + bbox
centroid). This sacrifices some accuracy for a uniform sample count.

The depth pass parameter is accepted for API stability with v1.0 — it lets
us cross-check that the UV-pass hit's depth roughly matches the expected
camera-space depth, catching edge cases where two different surfaces happen
to share UV space (currently impossible with the single-island unwrap, so
the depth pass is unused in v0.3).
"""

from __future__ import annotations

import math

import numpy as np

from document_simulator.synthesis.receipts.schema import TokenGroundTruth

# Maximum UV distance (Euclidean in unit square) at which a sample is
# considered "visible". 0.01 ~= 1% of UV space ~= ~3 px on a 384 render.
UV_EPS = 0.01

# Visibility decision threshold. occlusion_ratio < this -> visible.
VISIBILITY_THRESHOLD = 0.7


def uv_distance(uv_a: tuple[float, float], uv_b: tuple[float, float]) -> float:
    """Euclidean distance between two UVs.

    Args:
        uv_a: ``(u, v)`` of the first point.
        uv_b: ``(u, v)`` of the second point.

    Returns:
        ``sqrt((u_a - u_b)^2 + (v_a - v_b)^2)`` — no seam wrap-around. Per
        v0.3 design choice (single UV island on the receipt).
    """
    du = uv_a[0] - uv_b[0]
    dv = uv_a[1] - uv_b[1]
    return math.sqrt(du * du + dv * dv)


def sample_polygon_interior(
    polygon: list[tuple[float, float]],
) -> list[tuple[float, float]]:
    """Return 9 sample points: 4 corners + 4 edge midpoints + 1 centroid.

    For 4-vertex polygons the corners and edge midpoints are taken directly.
    For polygons with more than 4 vertices (e.g. subdivided polygons) we
    fall back to the polygon's *bounding box* corners and edge midpoints, so
    every token gets exactly 9 samples regardless of vertex count.

    Args:
        polygon: At least 3 vertices in any winding order.

    Returns:
        Exactly 9 ``(x, y)`` sample points.

    Raises:
        ValueError: If the polygon has fewer than 3 vertices.
    """
    if len(polygon) < 3:
        raise ValueError(
            f"polygon must have at least 3 vertices, got {len(polygon)}"
        )

    if len(polygon) == 4:
        c0, c1, c2, c3 = polygon
        e01 = ((c0[0] + c1[0]) / 2.0, (c0[1] + c1[1]) / 2.0)
        e12 = ((c1[0] + c2[0]) / 2.0, (c1[1] + c2[1]) / 2.0)
        e23 = ((c2[0] + c3[0]) / 2.0, (c2[1] + c3[1]) / 2.0)
        e30 = ((c3[0] + c0[0]) / 2.0, (c3[1] + c0[1]) / 2.0)
        cx = sum(p[0] for p in polygon) / 4.0
        cy = sum(p[1] for p in polygon) / 4.0
        return [c0, c1, c2, c3, e01, e12, e23, e30, (cx, cy)]

    # Fallback for non-quad: 4 bbox corners + 4 bbox edge mids + bbox centroid.
    xs = [p[0] for p in polygon]
    ys = [p[1] for p in polygon]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    x_mid = (x_min + x_max) / 2.0
    y_mid = (y_min + y_max) / 2.0
    return [
        (x_min, y_min),
        (x_max, y_min),
        (x_max, y_max),
        (x_min, y_max),
        (x_mid, y_min),
        (x_max, y_mid),
        (x_mid, y_max),
        (x_min, y_mid),
        (x_mid, y_mid),
    ]


def compute_visibility(
    token: TokenGroundTruth,
    uv_pass: np.ndarray,
    depth_pass: np.ndarray,  # noqa: ARG001 — accepted for v1.0 API stability
    render_size: tuple[int, int],
) -> None:
    """Populate ``token.visible`` and ``token.occlusion_ratio`` in place.

    Args:
        token: Token with at least a ``uv`` and ``camera_2d`` snapshot. The
            ``camera_2d`` polygon is the source of the 9 sample points; the
            ``uv`` polygon is the source of the *expected* UV at each
            sample.
        uv_pass: Per-pixel rendered UV, shape ``(H, W, 2)``, float32. From
            ``render_eevee``'s second return value.
        depth_pass: Per-pixel camera-space depth, shape ``(H, W)``, float32.
            Currently unused in v0.3 (single-island unwrap means the UV
            comparison is sufficient); kept in the signature for v1.0
            two-surface-disambiguation.
        render_size: ``(width, height)`` in pixels — must match the UV pass
            shape ``(H, W)``.

    Raises:
        ValueError: If the token lacks a ``uv`` or ``camera_2d`` snapshot.
    """
    uv_snap = next((c for c in token.coords if c.stage == "uv"), None)
    cam_snap = next((c for c in token.coords if c.stage == "camera_2d"), None)
    if uv_snap is None or cam_snap is None:
        raise ValueError(
            f"token {token.token_id!r} requires both 'uv' and 'camera_2d' "
            f"snapshots before visibility — available stages: "
            f"{[c.stage for c in token.coords]}"
        )

    cam_polygon = cam_snap.polygon
    uv_polygon = uv_snap.polygon
    if not cam_polygon:
        # Polygon entirely behind the camera (all corners dropped by
        # world_to_camera_2d) -> definitionally invisible.
        token.visible = False
        token.occlusion_ratio = 1.0
        return

    width, height = render_size
    cam_samples = sample_polygon_interior(cam_polygon)

    # Expected-UV interpolation: bilinear within the polygon's bounding box.
    # We only need the bbox spans because the camera/uv polygons are
    # axis-aligned in the round-trip case and "close to" axis-aligned for
    # subdivided polygons. (Strictly correct barycentric mapping requires
    # solving for the corresponding UV via inverse projection, which is
    # too expensive here; bbox interpolation matches within UV_EPS for
    # nearly-rectangular polygons, which is what the receipt produces.)
    cam_xs = [p[0] for p in cam_polygon]
    cam_ys = [p[1] for p in cam_polygon]
    uv_us = [p[0] for p in uv_polygon]
    uv_vs = [p[1] for p in uv_polygon]
    cx_min, cx_max = min(cam_xs), max(cam_xs)
    cy_min, cy_max = min(cam_ys), max(cam_ys)
    u_min, u_max = min(uv_us), max(uv_us)
    v_min, v_max = min(uv_vs), max(uv_vs)
    cx_span = max(cx_max - cx_min, 1e-9)
    cy_span = max(cy_max - cy_min, 1e-9)

    visible_count = 0
    n_samples = len(cam_samples)
    for sx, sy in cam_samples:
        px = int(sx)
        py = int(sy)
        if px < 0 or px >= width or py < 0 or py >= height:
            continue  # off-frame sample = occluded
        rendered_uv = (float(uv_pass[py, px, 0]), float(uv_pass[py, px, 1]))

        # Background pixels in the UV pass are (0, 0) per render_eevee's
        # docs; the receipt's UV space is well away from the corner so this
        # disambiguates "no surface here" from "surface with UV ~(0,0)".
        if rendered_uv == (0.0, 0.0):
            continue

        tx = (sx - cx_min) / cx_span
        ty = (sy - cy_min) / cy_span
        expected_uv = (
            u_min + tx * (u_max - u_min),
            v_min + ty * (v_max - v_min),
        )
        if uv_distance(rendered_uv, expected_uv) < UV_EPS:
            visible_count += 1

    token.occlusion_ratio = 1.0 - (visible_count / n_samples)
    token.visible = token.occlusion_ratio < VISIBILITY_THRESHOLD
