"""UV -> world projection via barycentric interpolation (FDD #29 v0.3b AC-1b).

Given a (u, v) point and a Blender mesh with an active UV layer, find the
mesh triangle whose UV-space triangle contains (u, v), compute barycentric
weights inside that triangle, and apply those weights to the triangle's
*world*-space vertex coordinates to get the 3D position on the (possibly
deformed) surface.

A naive linear scan over ~8000 receipt-mesh triangles is O(N x M) where M is
the number of token corners (typically 100-300 with edge subdivision). The
``UVSpatialHash`` indexes triangles by a 64x64 UV grid so each lookup checks
a handful of candidate triangles.

UV-seam handling: the input UV is clamped to ``[eps, 1-eps]`` before lookup,
which is correct for the v0.3a programmatic mesh that has a single planar
UV island.

This module imports ``bpy``-free types only at module-level; the bpy mesh
type is only referenced by name in the function signatures (no runtime
isinstance check).
"""

from __future__ import annotations

import math
from typing import Any

# Default UV-grid resolution. 64 cells per axis -> 4096 cells. Receipt has
# ~8000 triangles -> ~2 triangles per cell on average. Good ratio for O(1)-ish
# lookup without ballooning memory.
_DEFAULT_HASH_RESOLUTION = 64

# Margin off the unit-square edges when clamping out-of-range UV. Avoids
# numerical issues at exact 0 / 1 (where the loop triangle search may fall
# on a triangle edge).
_UV_CLAMP_EPS = 1e-6


class UVSpatialHash:
    """O(1)-ish "which triangle contains this UV?" index over a Blender mesh.

    The mesh's loop triangles are pre-computed (via ``mesh.calc_loop_triangles()``)
    and bucketed by the integer UV-grid cell each triangle's bounding box
    overlaps. A lookup at (u, v) reads the bucket at ``(int(u*N), int(v*N))``
    and runs a point-in-triangle test against just the candidates in that
    bucket.

    The hash is invalidated by mesh edits — *do not* mutate the mesh after
    constructing the hash. UV layout is not mutated by ``deform_paper`` (only
    z-coordinates change), so the hash remains valid across paper deformations.

    Attributes:
        resolution: Cells per axis. 64 means a 64x64 grid over the unit square.
        triangles: List of ``((uv0, uv1, uv2), (v0_idx, v1_idx, v2_idx))``
            entries — one per loop triangle.
    """

    def __init__(self, mesh: Any, resolution: int = _DEFAULT_HASH_RESOLUTION) -> None:
        """Build the hash from ``mesh.uv_layers.active`` and loop triangles.

        Args:
            mesh: ``bpy.types.Mesh`` with an active UV layer.
            resolution: UV-grid resolution. Default 64 is a good fit for the
                v0.3a receipt mesh.
        """
        if mesh.uv_layers.active is None:
            raise ValueError("mesh has no active UV layer")
        self.resolution = resolution
        self._mesh = mesh
        self._uv_layer = mesh.uv_layers.active
        # Make sure loop triangles exist; cheap if already computed.
        mesh.calc_loop_triangles()

        # Build the triangles list: per loop_triangle, store the 3 UV verts and
        # 3 vertex indices. We don't store world coords — they're read fresh
        # on each lookup so post-deform queries see the latest z.
        self.triangles: list[tuple[tuple[tuple[float, float], ...], tuple[int, ...]]] = []
        loops = mesh.loops
        uv_data = self._uv_layer.data
        for tri in mesh.loop_triangles:
            # tri.loops is a tuple of 3 loop indices into mesh.loops; each loop
            # owns its UV in uv_data and points to a vertex in mesh.vertices.
            l0, l1, l2 = tri.loops
            uv0 = (uv_data[l0].uv.x, uv_data[l0].uv.y)
            uv1 = (uv_data[l1].uv.x, uv_data[l1].uv.y)
            uv2 = (uv_data[l2].uv.x, uv_data[l2].uv.y)
            v0 = loops[l0].vertex_index
            v1 = loops[l1].vertex_index
            v2 = loops[l2].vertex_index
            self.triangles.append(((uv0, uv1, uv2), (v0, v1, v2)))

        # Bucket triangles by UV-grid cell. Each triangle is rasterized into
        # the cells covered by its UV-space bounding box.
        self._buckets: dict[tuple[int, int], list[int]] = {}
        for tri_idx, ((uv0, uv1, uv2), _) in enumerate(self.triangles):
            u_min = min(uv0[0], uv1[0], uv2[0])
            u_max = max(uv0[0], uv1[0], uv2[0])
            v_min = min(uv0[1], uv1[1], uv2[1])
            v_max = max(uv0[1], uv1[1], uv2[1])
            cu_min = max(0, int(u_min * resolution))
            cu_max = min(resolution - 1, int(u_max * resolution))
            cv_min = max(0, int(v_min * resolution))
            cv_max = min(resolution - 1, int(v_max * resolution))
            for cu in range(cu_min, cu_max + 1):
                for cv in range(cv_min, cv_max + 1):
                    self._buckets.setdefault((cu, cv), []).append(tri_idx)

    def candidates(self, uv: tuple[float, float]) -> list[int]:
        """Return triangle indices whose UV bbox contains the cell at ``uv``."""
        u, v = uv
        cu = max(0, min(self.resolution - 1, int(u * self.resolution)))
        cv = max(0, min(self.resolution - 1, int(v * self.resolution)))
        return self._buckets.get((cu, cv), [])


def uv_to_world(
    uv: tuple[float, float],
    mesh: Any,
    spatial_hash: UVSpatialHash | None = None,
) -> tuple[float, float, float] | None:
    """Project a UV point to world coordinates via the mesh's surface.

    Args:
        uv: ``(u, v)`` in the mesh's UV space. Out-of-range values are
            clamped to ``[eps, 1 - eps]`` (UV-seam mitigation per FDD §AC-1b).
        mesh: ``bpy.types.Mesh`` with an active UV layer. Must have called
            ``calc_loop_triangles()`` (handled internally by this function
            and by ``UVSpatialHash``).
        spatial_hash: Optional pre-built ``UVSpatialHash``. If None, a new
            one is built per call (slow — pass one in for batch projection).

    Returns:
        ``(x, y, z)`` world coords, or None if the UV point falls outside
        every triangle (shouldn't happen for a single-island identity-UV
        receipt mesh, but defensive).
    """
    # Clamp UV to the unit square. Per design doc §2 failure modes, UV
    # outside the unit square arises from token bboxes near the receipt
    # edge or from upstream rounding.
    u = min(max(uv[0], _UV_CLAMP_EPS), 1.0 - _UV_CLAMP_EPS)
    v = min(max(uv[1], _UV_CLAMP_EPS), 1.0 - _UV_CLAMP_EPS)
    clamped_uv = (u, v)

    if spatial_hash is None:
        spatial_hash = UVSpatialHash(mesh)

    candidates = spatial_hash.candidates(clamped_uv)
    if not candidates:
        # Bucket empty -> fall back to a linear scan over all triangles.
        # This catches any edge-rounding case where the bucket misses but
        # an adjacent triangle should have hit.
        candidates = list(range(len(spatial_hash.triangles)))

    vertices = mesh.vertices
    for tri_idx in candidates:
        (uv0, uv1, uv2), (v0_idx, v1_idx, v2_idx) = spatial_hash.triangles[tri_idx]
        bary = _barycentric(clamped_uv, uv0, uv1, uv2)
        if bary is None:
            continue
        b0, b1, b2 = bary
        # Inside-triangle: all three weights in [0, 1] (with small tol for
        # near-edge points).
        tol = 1e-6
        if b0 >= -tol and b1 >= -tol and b2 >= -tol:
            # Snap weights to [0, 1] and renormalize so the world output
            # is a true convex combination (per §2 failure mode).
            b0 = max(0.0, min(1.0, b0))
            b1 = max(0.0, min(1.0, b1))
            b2 = max(0.0, min(1.0, b2))
            s = b0 + b1 + b2
            if s == 0:
                continue
            b0, b1, b2 = b0 / s, b1 / s, b2 / s
            v0 = vertices[v0_idx].co
            v1 = vertices[v1_idx].co
            v2 = vertices[v2_idx].co
            x = b0 * v0.x + b1 * v1.x + b2 * v2.x
            y = b0 * v0.y + b1 * v1.y + b2 * v2.y
            z = b0 * v0.z + b1 * v1.z + b2 * v2.z
            return (x, y, z)

    # No triangle contained the point. Return the nearest-triangle's
    # closest-vertex projection as a last-ditch fallback.
    return _nearest_vertex_world(clamped_uv, mesh, spatial_hash)


def _barycentric(
    p: tuple[float, float],
    a: tuple[float, float],
    b: tuple[float, float],
    c: tuple[float, float],
) -> tuple[float, float, float] | None:
    """Compute barycentric weights of ``p`` inside triangle ``(a, b, c)``.

    Standard 2D barycentric via the cross-product / determinant formula.
    Returns None if the triangle is degenerate (collinear vertices).
    """
    # Vectors along two triangle edges and from a to p.
    v0x = b[0] - a[0]
    v0y = b[1] - a[1]
    v1x = c[0] - a[0]
    v1y = c[1] - a[1]
    v2x = p[0] - a[0]
    v2y = p[1] - a[1]

    den = v0x * v1y - v1x * v0y
    if abs(den) < 1e-18:
        return None

    inv_den = 1.0 / den
    b1 = (v2x * v1y - v1x * v2y) * inv_den
    b2 = (v0x * v2y - v2x * v0y) * inv_den
    b0 = 1.0 - b1 - b2
    return (b0, b1, b2)


def _nearest_vertex_world(
    uv: tuple[float, float],
    mesh: Any,
    spatial_hash: UVSpatialHash,
) -> tuple[float, float, float] | None:
    """Last-ditch fallback: return the world coord of the UV-nearest vertex.

    Used when no triangle's barycentric test passes (rare, only from extreme
    edge clamping). Walks the active UV layer once to find the vertex whose
    UV is closest to the query point.
    """
    uv_data = mesh.uv_layers.active.data
    loops = mesh.loops
    best_idx = -1
    best_dist = math.inf
    for i, loop_uv in enumerate(uv_data):
        du = loop_uv.uv.x - uv[0]
        dv = loop_uv.uv.y - uv[1]
        d = du * du + dv * dv
        if d < best_dist:
            best_dist = d
            best_idx = loops[i].vertex_index
    if best_idx < 0:
        return None
    co = mesh.vertices[best_idx].co
    return (co.x, co.y, co.z)
