"""Polygon edge subdivision (FDD #29 v0.3b AC-2b).

A bounding box for a token is straight in UV space (4 corners). When that
polygon is later projected through a curved 3D mesh, those 4 corners are
mapped through barycentric interpolation, but the *edges* between corners are
drawn as straight 2D lines in the camera image — even though the underlying
3D surface curves between them. The result is a polygon that "cuts across"
surface curvature instead of following it.

The fix is to add intermediate points along each UV-space edge BEFORE the
3D projection. Each intermediate point gets its own barycentric lookup, so
the resulting world / camera-space polygon hugs the surface.

This module is pure-Python and bpy-free so it can be exercised on any
Python interpreter (3.10/3.11/3.12).
"""

from __future__ import annotations


def subdivide_polygon(
    polygon: list[tuple[float, float]],
    segments: int = 4,
) -> list[tuple[float, float]]:
    """Add intermediate points along each polygon edge.

    Args:
        polygon: List of ``(x, y)`` corners in CCW order. Must have at least
            2 points.
        segments: Number of equal sub-segments each edge is split into. With
            ``segments=1`` no intermediates are added (output == input).
            With ``segments=4`` each edge gains 3 intermediates. Must be >= 1.

    Returns:
        ``[c0, c1, ..., cN-1, e0_inter_0, e0_inter_1, ..., e1_inter_0, ...]``
        — the original ``N`` corners first (preserving input order), then
        ``segments - 1`` intermediates per edge in CCW order. Total length is
        ``N + N * (segments - 1) = N * segments``.

    Raises:
        ValueError: If ``polygon`` has fewer than 2 points or ``segments < 1``.
    """
    if len(polygon) < 2:
        raise ValueError(f"polygon must have at least 2 points, got {len(polygon)}")
    if segments < 1:
        raise ValueError(f"segments must be >= 1, got {segments}")

    n = len(polygon)
    intermediates_per_edge = segments - 1
    out: list[tuple[float, float]] = list(polygon)  # corners first, in input order

    if intermediates_per_edge == 0:
        return out

    for edge_idx in range(n):
        c_start = polygon[edge_idx]
        c_end = polygon[(edge_idx + 1) % n]
        dx = c_end[0] - c_start[0]
        dy = c_end[1] - c_start[1]
        for k in range(1, segments):
            t = k / segments
            out.append((c_start[0] + dx * t, c_start[1] + dy * t))
    return out
