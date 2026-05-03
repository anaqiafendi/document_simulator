"""Procedural paper deformation for the receipt mesh (FDD #29 v0.3a AC-5a).

Applies cylindrical curl (low-frequency sin along the long axis) plus optional
sparse fold lines. The mesh's UV coordinates are NEVER touched — UV is a 2D
parameterization of the surface, and the bbox projector relies on that
invariant.

All randomness is driven by a passed-in seed for reproducibility. The
deformations modify only ``vertex.co.z`` in place.
"""

from __future__ import annotations

import math
import random


def deform_paper(
    mesh,
    curl_strength: float = 0.1,
    fold_count: int = 0,
    seed: int | None = None,
) -> None:
    """Apply procedural curl + fold deformations to a flat receipt mesh.

    Args:
        mesh: A ``bpy.types.Mesh`` (e.g. ``scene.objects["receipt"].data``).
            Must currently be planar (z=0); the function only mutates ``z``.
        curl_strength: Peak z-displacement (meters) of the cylindrical curl
            along the long (y) axis. ``0.1`` => ~10cm wave at the receipt's
            ends, which on an 80mm x 200mm receipt looks like a gentle natural
            curl. ``0.0`` disables the curl.
        fold_count: Number of sparse fold lines (hard z-displacement creases)
            placed at random y positions. Each fold is a ~2mm vertical kink.
        seed: Reproducibility seed. Same seed -> bit-identical deformation.

    Notes:
        UV coords are intentionally not touched. See FDD #29 §AC-5a (the
        v0.3b bbox projector relies on UV staying identity for the
        ``raster -> uv -> world`` mapping).
    """
    rng = random.Random(seed)

    # Receipt y-bounds (we curl along the long axis).
    ys = [v.co.y for v in mesh.vertices]
    y_min, y_max = min(ys), max(ys)
    y_span = y_max - y_min
    if y_span < 1e-9:
        return  # degenerate mesh

    # Pick fold y-positions up front so they're stable per seed.
    fold_positions: list[float] = []
    for _ in range(max(0, fold_count)):
        # Pick somewhere in the middle 70% of the receipt to avoid edges.
        t = rng.uniform(0.15, 0.85)
        fold_positions.append(y_min + t * y_span)
    # Each fold has its own (deterministic) magnitude.
    fold_magnitudes = [rng.uniform(0.001, 0.003) for _ in fold_positions]
    # Width (in y) over which the fold transitions.
    fold_widths = [rng.uniform(0.002, 0.005) for _ in fold_positions]

    for vert in mesh.vertices:
        z = 0.0

        # 1. Cylindrical curl: sin wave along y, scaled by curl_strength.
        if curl_strength != 0.0:
            # phase 0 at y_min, ~pi at y_max -> half-wave bowing the receipt up
            # at one end. Looks like a phone-photo'd receipt sitting half-flat.
            t = (vert.co.y - y_min) / y_span
            z += curl_strength * math.sin(math.pi * t) * 0.5
            # Add a subtle X-axis curl too so it isn't perfectly cylindrical.
            xs_max = max(abs(vv.co.x) for vv in mesh.vertices) or 1.0
            tx = vert.co.x / xs_max
            z += curl_strength * 0.05 * tx * tx  # gentle parabolic side curl

        # 2. Sparse folds: smooth-step kink at each fold y-position.
        for fy, fmag, fwidth in zip(fold_positions, fold_magnitudes, fold_widths, strict=True):
            dy = vert.co.y - fy
            # tanh smooths the kink so it isn't a discontinuity (which would
            # blow up barycentric interpolation in the projector).
            z += fmag * (math.tanh(dy / fwidth) - math.tanh((dy - fwidth) / fwidth)) * 0.5

        vert.co.z = z

    mesh.update()
