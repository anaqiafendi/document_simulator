"""Unit tests for ``synthesis.receipts.scene.mesh.deform_paper``.

Covers FDD #29 v0.3a AC-5a (procedural curl + folds preserve UV layout while
displacing z; deformations are seeded reproducibly).
"""

from __future__ import annotations

import pytest

bpy = pytest.importorskip("bpy")  # noqa: F811

from document_simulator.synthesis.receipts.scene import build_scene, deform_paper  # noqa: E402


def _bpy_reset() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=False)


def _snapshot_uvs(mesh) -> list[tuple[float, float]]:
    uv_layer = mesh.uv_layers.active
    return [(uv_layer.data[i].uv.x, uv_layer.data[i].uv.y) for i in range(len(uv_layer.data))]


def _snapshot_zs(mesh) -> list[float]:
    return [v.co.z for v in mesh.vertices]


def test_deform_paper_preserves_uv() -> None:
    """AC-5a critical: UV is a 2D parameterization of the surface; deforming
    the surface in 3D MUST NOT touch the UV coordinates. The bbox projector
    relies on this invariant.
    """
    _bpy_reset()
    scene = build_scene(seed=42, hdri_id=None)
    mesh = scene.objects["receipt"].data
    uv_before = _snapshot_uvs(mesh)

    deform_paper(mesh, curl_strength=0.2, fold_count=2, seed=42)

    uv_after = _snapshot_uvs(mesh)
    assert uv_before == uv_after, "deform_paper must not modify UV coordinates"


def test_deform_paper_changes_z_coords() -> None:
    """AC-5a: with non-zero curl_strength some vertices must end up off the
    z=0 plane, otherwise the deformation is a no-op.
    """
    _bpy_reset()
    scene = build_scene(seed=42, hdri_id=None)
    mesh = scene.objects["receipt"].data
    z_before = _snapshot_zs(mesh)
    assert all(abs(z) < 1e-9 for z in z_before), "starting plane must be flat (z=0)"

    deform_paper(mesh, curl_strength=0.1, fold_count=0, seed=42)

    z_after = _snapshot_zs(mesh)
    assert any(
        abs(z) > 1e-6 for z in z_after
    ), "curl_strength > 0 should introduce non-zero z displacements"


def test_deform_paper_seeded_determinism() -> None:
    """AC-5a: same seed -> bit-identical z-displacement field.

    Without this, downstream snapshot tests (test_render_eevee_*) wouldn't be
    reproducible.
    """
    _bpy_reset()
    scene_a = build_scene(seed=42, hdri_id=None)
    mesh_a = scene_a.objects["receipt"].data
    deform_paper(mesh_a, curl_strength=0.15, fold_count=2, seed=42)
    z_a = _snapshot_zs(mesh_a)

    _bpy_reset()
    scene_b = build_scene(seed=42, hdri_id=None)
    mesh_b = scene_b.objects["receipt"].data
    deform_paper(mesh_b, curl_strength=0.15, fold_count=2, seed=42)
    z_b = _snapshot_zs(mesh_b)

    assert len(z_a) == len(z_b)
    for za, zb in zip(z_a, z_b, strict=True):
        assert za == pytest.approx(zb, abs=1e-9)
