"""Sutherland-Hodgman polygon clipping + final_crop stage (FDD #29 v0.3c AC-3c).

The classic Sutherland-Hodgman algorithm clips a *subject* polygon against a
*convex clip* polygon by walking the clip's edges and, for each edge, keeping
only the portion of the subject polygon on the inside half-plane (with new
vertices inserted at edge intersections).

Why not naive ``min/max`` bbox clamping? A bbox-clamp on a polygon that
straddles the image boundary collapses the off-frame vertices onto the image
edge — turning a triangle into a degenerate sliver instead of a true clipped
quad. Sutherland-Hodgman keeps the geometry honest: a partially-off-frame
quad becomes a (typically) 5-vertex polygon (the original 3 in-bound corners
plus 2 edge-intersection points).

The image bounds polygon is built CCW: ``[(0,0), (W,0), (W,H), (0,H)]``. The
"inside" test for each edge is the standard left-of-line cross-product check;
this is correct for any convex CCW clip polygon, image-shaped or otherwise.

This module is pure-Python and bpy-free so it can be exercised on any
interpreter (3.10/3.11/3.12).
"""

from __future__ import annotations

from document_simulator.synthesis.receipts.schema import (
    CoordSnapshot,
    TokenGroundTruth,
)


def sutherland_hodgman_clip(
    subject_polygon: list[tuple[float, float]],
    clip_polygon: list[tuple[float, float]],
) -> list[tuple[float, float]]:
    """Clip ``subject_polygon`` against the convex CCW ``clip_polygon``.

    Args:
        subject_polygon: Vertices of the polygon to clip, in any winding order.
        clip_polygon: Vertices of the *convex* clip region in **CCW** order.
            For image-bounds clipping pass
            ``[(0, 0), (W, 0), (W, H), (0, H)]``.

    Returns:
        The clipped polygon's vertices, or ``[]`` if the subject is entirely
        outside the clip region. The result is a list of ``(x, y)`` tuples in
        the same winding direction as the input subject; vertex count is
        bounded by ``len(subject) + len(clip)`` in the worst case.

    Notes:
        - The "inside" test uses the cross product
          ``(p1 - p0) x (q - p0) >= 0`` which holds for points on the *left*
          of the directed edge p0 -> p1. CCW clip polygons therefore have
          their interior on the inside half-plane of every edge — the
          standard Sutherland-Hodgman convention.
        - Floating-point ties (point exactly on a clip edge) are treated as
          inside (`>= 0`), which keeps shared-edge vertices in the output
          and avoids accidentally dropping a clip-aligned subject corner.
    """
    if not subject_polygon:
        return []
    if len(clip_polygon) < 3:
        raise ValueError(
            f"clip_polygon must have at least 3 vertices, got {len(clip_polygon)}"
        )

    output: list[tuple[float, float]] = list(subject_polygon)

    n_clip = len(clip_polygon)
    for i in range(n_clip):
        if not output:
            return []
        edge_start = clip_polygon[i]
        edge_end = clip_polygon[(i + 1) % n_clip]
        input_list = output
        output = []

        prev = input_list[-1]
        prev_inside = _is_inside(prev, edge_start, edge_end)
        for curr in input_list:
            curr_inside = _is_inside(curr, edge_start, edge_end)
            if curr_inside:
                if not prev_inside:
                    output.append(_intersect(prev, curr, edge_start, edge_end))
                output.append(curr)
            elif prev_inside:
                output.append(_intersect(prev, curr, edge_start, edge_end))
            prev = curr
            prev_inside = curr_inside

    return output


def apply_final_crop(
    token: TokenGroundTruth,
    output_size: tuple[int, int],
    crop_origin: tuple[float, float] = (0.0, 0.0),
) -> None:
    """Append a ``final_crop`` snapshot (or mark token invisible) in place.

    Reads the token's most recent CoordSnapshot polygon (typically
    ``camera_fx`` after :func:`apply_identity` runs), shifts every vertex by
    ``-crop_origin`` to translate into output-image pixel space, then clips
    the result against the output image bounds with Sutherland-Hodgman.

    Args:
        token: Token with at least one prior CoordSnapshot. Mutated in place:
            on success a ``final_crop`` snapshot is appended; on full-off-frame
            ``token.visible`` is set to ``False`` and NO snapshot is appended.
        output_size: ``(width, height)`` in pixels of the cropped output image.
        crop_origin: ``(x, y)`` offset (in pre-crop pixel coords) of the crop
            window's top-left corner. Defaults to ``(0, 0)`` for "no crop".

    Raises:
        IndexError: If ``token.coords`` is empty (no prior stage to crop).
    """
    if not token.coords:
        raise IndexError(
            f"token {token.token_id!r} has no CoordSnapshots to crop from"
        )

    prior_polygon = token.coords[-1].polygon
    output_w, output_h = output_size
    cx, cy = crop_origin

    shifted = [(x - cx, y - cy) for x, y in prior_polygon]
    image_bounds = [
        (0.0, 0.0),
        (float(output_w), 0.0),
        (float(output_w), float(output_h)),
        (0.0, float(output_h)),
    ]
    clipped = sutherland_hodgman_clip(shifted, image_bounds)

    if not clipped:
        token.visible = False
        return

    token.coords.append(CoordSnapshot(stage="final_crop", polygon=clipped))


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------


def _is_inside(
    point: tuple[float, float],
    edge_start: tuple[float, float],
    edge_end: tuple[float, float],
) -> bool:
    """True iff ``point`` is on the left of (or exactly on) edge_start->edge_end.

    Uses the 2D cross product ``(edge_end - edge_start) x (point - edge_start)``;
    >= 0 means CCW orientation (left side or on the line).
    """
    ex, ey = edge_start
    fx, fy = edge_end
    px, py = point
    return (fx - ex) * (py - ey) - (fy - ey) * (px - ex) >= 0.0


def _intersect(
    p0: tuple[float, float],
    p1: tuple[float, float],
    edge_start: tuple[float, float],
    edge_end: tuple[float, float],
) -> tuple[float, float]:
    """Intersection of segment p0->p1 with infinite line edge_start->edge_end.

    The Sutherland-Hodgman caller only invokes this when p0 and p1 sit on
    *opposite* sides of the edge, so the parametric segment-line intersection
    is guaranteed to land in [0, 1]. We don't validate that here — if the
    denominator is degenerate (parallel lines) we fall back to p1 to keep the
    polygon non-empty rather than crash.
    """
    x1, y1 = p0
    x2, y2 = p1
    x3, y3 = edge_start
    x4, y4 = edge_end

    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if denom == 0.0:
        return p1

    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))
