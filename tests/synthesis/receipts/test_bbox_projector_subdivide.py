"""Unit tests for ``synthesis.receipts.bbox_projector.subdivide.subdivide_polygon``.

Covers FDD #29 v0.3b AC-2b: subdivide_polygon adds intermediate points along
each edge so bboxes can follow surface curvature when later projected through
a deformed mesh, instead of straight corner-to-corner segments.
"""

from __future__ import annotations

import math

from document_simulator.synthesis.receipts.bbox_projector import subdivide_polygon


def test_subdivide_polygon_doubles_corners_to_quad_with_segments_2() -> None:
    """For a 4-corner input + segments=2, output has 4 corners + 4 edges * 1 = 8 points.

    With segments=2, each edge is split into 2 sub-segments, which means 1
    intermediate point per edge. 4 edges * 1 intermediate = 4 intermediates,
    plus the 4 originals = 8.
    """
    polygon = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    result = subdivide_polygon(polygon, segments=2)
    assert len(result) == 8, f"expected 8 points, got {len(result)}: {result}"


def test_subdivide_polygon_preserves_corner_order() -> None:
    """The 4 input corners must come first in the output, in CCW order;
    intermediates per edge follow each corner.

    Per AC-2b, the canonical layout for a 4-corner input + segments=4 is:
    [c0, c1, c2, c3, e0_0, e0_1, e0_2, e1_0, e1_1, e1_2, ...] for 16 points
    total. We assert the corners come first.
    """
    polygon = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    result = subdivide_polygon(polygon, segments=4)
    assert len(result) == 16, f"expected 16 points (4 + 4*3), got {len(result)}"
    # First 4 entries must be the input corners, in input order.
    for input_corner, output_corner in zip(polygon, result[:4], strict=True):
        assert (
            output_corner == input_corner
        ), f"corner order mismatch: expected {input_corner}, got {output_corner}"


def test_subdivide_polygon_intermediates_lie_on_edges() -> None:
    """Each intermediate point must be collinear with its source edge corners.

    For an axis-aligned unit square, edge 0 goes c0=(0,0) -> c1=(1,0), so
    intermediates on edge 0 must have y == 0 and 0 < x < 1. We check edge
    collinearity via cross-product == 0 within epsilon.
    """
    polygon = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    segments = 4
    result = subdivide_polygon(polygon, segments=segments)
    n_corners = len(polygon)
    intermediates_per_edge = segments - 1

    # Iterate each edge's intermediates and check collinearity.
    for edge_idx in range(n_corners):
        c_start = polygon[edge_idx]
        c_end = polygon[(edge_idx + 1) % n_corners]
        edge_vec = (c_end[0] - c_start[0], c_end[1] - c_start[1])
        for k in range(intermediates_per_edge):
            inter_idx = n_corners + edge_idx * intermediates_per_edge + k
            point = result[inter_idx]
            point_vec = (point[0] - c_start[0], point[1] - c_start[1])
            cross = edge_vec[0] * point_vec[1] - edge_vec[1] * point_vec[0]
            assert math.isclose(cross, 0.0, abs_tol=1e-9), (
                f"intermediate {point} on edge "
                f"({c_start} -> {c_end}) not collinear (cross={cross})"
            )
