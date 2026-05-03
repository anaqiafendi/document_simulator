"""Unit tests for ``synthesis.receipts.scene.builder``.

Covers FDD #29 v0.3a AC-4a (build_scene shape + named objects + identity UV +
HDRI loading + seeded determinism). The tests are skipped on interpreters that
do not have ``bpy`` installed (3.10/3.12 — bpy 4.2.0 ships only Python 3.11
wheels), keeping the synthesis-3d extra optional.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

bpy = pytest.importorskip("bpy")  # noqa: F811

from document_simulator.synthesis.receipts.scene import build_scene  # noqa: E402

_HDRI_DIR = Path(__file__).resolve().parents[3] / "data" / "hdri"


def _bpy_reset() -> None:
    """Clear any state from a previous test."""
    bpy.ops.wm.read_factory_settings(use_empty=False)


def test_build_scene_returns_scene_with_named_objects() -> None:
    """AC-4a: build_scene must expose 'receipt' (plane) and 'camera' objects.

    The bbox projector (v0.3b) reaches for them by name; build_scene is the
    contract that produces that name table.
    """
    _bpy_reset()
    scene = build_scene(seed=42, hdri_id=None)

    assert scene.objects.get("receipt") is not None, "scene must expose 'receipt'"
    receipt = scene.objects["receipt"]
    assert receipt.type == "MESH", "receipt object must be a MESH"

    assert scene.objects.get("camera") is not None, "scene must expose 'camera'"
    camera = scene.objects["camera"]
    assert camera.type == "CAMERA", "camera object must be a CAMERA"

    # And the scene's active camera should be that camera (so render_eevee picks it up).
    assert scene.camera is not None
    assert scene.camera.name == "camera"


def test_receipt_uv_is_identity() -> None:
    """AC-4a critical: the receipt mesh's UV must be planar identity.

    For each *loop* in the mesh (loops are per-face vertex incidences which
    own their UV coords), the UV must equal the vertex's xy normalized into
    [0, 1]. That property is what the v0.3b bbox projector relies on for
    raster->uv->world mapping.
    """
    _bpy_reset()
    scene = build_scene(seed=42, hdri_id=None)
    mesh = scene.objects["receipt"].data

    assert len(mesh.uv_layers) >= 1, "receipt mesh must have a UV layer"
    uv_layer = mesh.uv_layers.active

    # Compute mesh xy bounds to map vertex xy -> UV expectation.
    xs = [v.co.x for v in mesh.vertices]
    ys = [v.co.y for v in mesh.vertices]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    x_span = x_max - x_min
    y_span = y_max - y_min
    assert x_span > 0 and y_span > 0

    for poly in mesh.polygons:
        for loop_index in poly.loop_indices:
            loop = mesh.loops[loop_index]
            vertex = mesh.vertices[loop.vertex_index]
            uv = uv_layer.data[loop_index].uv

            expected_u = (vertex.co.x - x_min) / x_span
            # We pin v=0 at the TOP of the receipt (raster origin is top-left, +y down).
            # Mesh local +y is "up". Identity here means v = (y_max - y) / y_span.
            expected_v = (y_max - vertex.co.y) / y_span

            assert uv.x == pytest.approx(expected_u, abs=1e-5), (
                f"UV.x mismatch at loop {loop_index}: " f"got {uv.x} expected {expected_u}"
            )
            assert uv.y == pytest.approx(expected_v, abs=1e-5), (
                f"UV.y mismatch at loop {loop_index}: " f"got {uv.y} expected {expected_v}"
            )


def test_build_scene_loads_hdri() -> None:
    """AC-4a: when an hdri_id is given, the world's environment node carries an image.

    We bundle 3 CC0 HDRIs in data/hdri/. The builder should pick one of them
    when hdri_id is specified, wire it into the World node tree, and the
    Environment Texture node must have a non-None .image.
    """
    _bpy_reset()
    available = sorted(p.stem for p in _HDRI_DIR.glob("*.hdr"))
    if not available:
        pytest.skip("data/hdri/ has no .hdr files (placeholder mode)")

    hdri_id = available[0]
    scene = build_scene(seed=7, hdri_id=hdri_id)

    world = scene.world
    assert world is not None and world.use_nodes is True
    env_nodes = [n for n in world.node_tree.nodes if n.bl_idname == "ShaderNodeTexEnvironment"]
    assert env_nodes, "world must contain a ShaderNodeTexEnvironment"
    assert env_nodes[0].image is not None, "the environment node must reference a loaded HDRI"


def test_build_scene_seeded_determinism() -> None:
    """AC-4a: same seed + same hdri -> same scene topology.

    We assert vertex count + camera location agreement across two builds.
    Topology determinism gates the v0.3b projector's reproducibility tests.
    """
    _bpy_reset()
    scene_a = build_scene(seed=42, hdri_id=None)
    verts_a = len(scene_a.objects["receipt"].data.vertices)
    cam_loc_a = tuple(scene_a.objects["camera"].location)

    _bpy_reset()
    scene_b = build_scene(seed=42, hdri_id=None)
    verts_b = len(scene_b.objects["receipt"].data.vertices)
    cam_loc_b = tuple(scene_b.objects["camera"].location)

    assert verts_a == verts_b
    np.testing.assert_allclose(cam_loc_a, cam_loc_b, atol=1e-6)
