"""Unit tests for ``synthesis.receipts.bbox_projector.uv_to_world``.

Covers FDD #29 v0.3b AC-1b:
    uv_to_world(uv, mesh) performs barycentric interpolation across the mesh
    triangle containing ``uv``, with UV-spatial-hash for O(1) lookup, and
    handles UV seams via clamping.
"""

from __future__ import annotations

import random
import time

import pytest

bpy = pytest.importorskip("bpy")  # noqa: F811

from document_simulator.synthesis.receipts.bbox_projector import (  # noqa: E402
    UVSpatialHash,
    uv_to_world,
)
from document_simulator.synthesis.receipts.scene import (  # noqa: E402
    build_scene,
    deform_paper,
)


def _bpy_reset() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=False)


def test_uv_to_world_flat_plane_returns_xy_with_zero_z() -> None:
    """AC-1b: on a flat undeformed receipt, UV (0.5, 0.5) maps to world (0, 0, 0).

    The receipt mesh is centered at origin, identity-UV, and undeformed
    (z=0 everywhere). The center UV should map to (0, 0, 0) within
    floating-point tolerance.
    """
    _bpy_reset()
    scene = build_scene(seed=42, hdri_id=None)
    mesh = scene.objects["receipt"].data

    world = uv_to_world((0.5, 0.5), mesh)
    assert world is not None
    x, y, z = world
    assert x == pytest.approx(0.0, abs=1e-4)
    assert y == pytest.approx(0.0, abs=1e-4)
    assert z == pytest.approx(0.0, abs=1e-6)


def test_uv_to_world_clamps_uv_outside_unit_square() -> None:
    """AC-1b: UV outside [0, 1] must be clamped, not crash.

    A point at (1.1, -0.05) should be clamped to ~(1.0, 0.0) and project
    to the corresponding mesh corner. We assert it returns a finite tuple.
    """
    _bpy_reset()
    scene = build_scene(seed=42, hdri_id=None)
    mesh = scene.objects["receipt"].data

    world = uv_to_world((1.1, -0.05), mesh)
    assert world is not None, "UV out of range must clamp, not return None"
    x, y, z = world
    # On the flat plane this should be near the (x_max, y_max) corner since
    # v=0 maps to y=y_max per identity-UV.
    xs = [v.co.x for v in mesh.vertices]
    ys = [v.co.y for v in mesh.vertices]
    assert x == pytest.approx(max(xs), abs=1e-3)
    assert y == pytest.approx(max(ys), abs=1e-3)
    assert z == pytest.approx(0.0, abs=1e-6)


def test_uv_to_world_curved_plane_z_nonzero() -> None:
    """AC-1b: after curl deformation, a non-corner UV must have z != 0.

    Proves the spatial hash + barycentric is reading the deformed mesh
    state, not a stale flat copy.
    """
    _bpy_reset()
    scene = build_scene(seed=42, hdri_id=None)
    mesh = scene.objects["receipt"].data
    deform_paper(mesh, curl_strength=0.2, fold_count=0, seed=42)

    # The curl is a sin half-wave along y -> z is maximum at the middle.
    # Pick UV (0.5, 0.5) which is the receipt center.
    world = uv_to_world((0.5, 0.5), mesh)
    assert world is not None
    _, _, z = world
    assert abs(z) > 1e-4, f"expected curl-displaced z, got z={z}"


def test_uv_to_world_spatial_hash_O1_perf() -> None:
    """AC-1b: 1000 random UV queries against the receipt mesh complete in <1s.

    The receipt has ~50x80 quads = ~8000 triangles. Linear scan would be
    ~8M comparisons; the spatial hash should drop that to <100ms range.
    We use a generous 1s ceiling to absorb CI jitter while still failing
    catastrophically if the hash regresses.
    """
    _bpy_reset()
    scene = build_scene(seed=42, hdri_id=None)
    mesh = scene.objects["receipt"].data

    # Pre-build the hash so the timing measures only the lookups.
    hash_idx = UVSpatialHash(mesh)
    rng = random.Random(0)
    queries = [(rng.uniform(0.05, 0.95), rng.uniform(0.05, 0.95)) for _ in range(1000)]

    t0 = time.perf_counter()
    for uv in queries:
        result = uv_to_world(uv, mesh, spatial_hash=hash_idx)
        assert result is not None
    elapsed = time.perf_counter() - t0
    assert elapsed < 1.0, f"1000 lookups took {elapsed:.2f}s — spatial hash regressed?"
