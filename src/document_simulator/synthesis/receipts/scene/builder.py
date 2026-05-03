"""Programmatic Blender scene builder for photoreal receipt synthesis (v0.3a).

Builds a scene containing:
    - "receipt" — a subdivided plane (~50x80 verts) with identity UV unwrap
    - "camera" — positioned at a top-down ~30-45deg angle, framing the receipt
    - "sun"   — directional light for shadow definition
    - HDRI environment from ``data/hdri/`` driving the world background

The receipt's UV unwrap is *planar identity* by construction — each loop's UV
is ``(x_normalized, 1 - y_normalized)`` of its vertex's local-space xy. This
property is what the v0.3b bbox projector relies on for ``raster -> uv -> world``.
"""

from __future__ import annotations

import math
import random
from pathlib import Path

from loguru import logger

# Receipt physical dimensions (meters). Roughly an 80mm x 200mm thermal receipt.
_RECEIPT_WIDTH_M = 0.080
_RECEIPT_HEIGHT_M = 0.200

# Mesh subdivision granularity (~50 x ~80 verts as per FDD AC-4a).
_SUBDIVISIONS_X = 49  # plane is split into 49 cuts -> 50 verts wide
_SUBDIVISIONS_Y = 79  # 79 cuts -> 80 verts tall

# Camera placement — held just above the receipt, tilted ~35 deg from straight down.
_CAMERA_DISTANCE = 0.30  # meters from receipt origin
_CAMERA_TILT_DEG = 35.0  # tilt away from straight-down (0 deg = top-down)

# Directory holding bundled CC0 HDRIs.
_HDRI_DIR = Path(__file__).resolve().parents[5] / "data" / "hdri"


def list_hdris() -> list[str]:
    """Return the IDs (file stems) of bundled HDRIs in ``data/hdri/``.

    Returns:
        Sorted list of HDRI ids, e.g. ``["kitchen_bright", "office_warm",
        "outdoor_overcast"]``. Empty list if the directory is missing.
    """
    if not _HDRI_DIR.exists():
        return []
    return sorted(p.stem for p in _HDRI_DIR.glob("*.hdr"))


def build_scene(seed: int, hdri_id: str | None = None):
    """Construct a fresh Blender scene for a photoreal receipt render.

    Args:
        seed: Reproducibility seed. Controls camera jitter.
        hdri_id: HDRI filename stem (without ``.hdr``) from ``data/hdri/``.
            If None, picks the first available HDRI alphabetically. If no
            HDRIs are bundled, falls back to a flat sky (no environment image).

    Returns:
        ``bpy.types.Scene`` with named objects ``"receipt"`` and ``"camera"``,
        plus a ``"sun"`` light and (optionally) an HDRI-textured world.
    """
    import bpy  # local import — keeps non-bpy interpreters importable

    # Reset to a clean factory state. (Tests also call wm.read_factory_settings,
    # but we re-do it here so calling build_scene() in user code is self-contained.)
    bpy.ops.wm.read_factory_settings(use_empty=False)

    # Wipe everything from the default startup scene so we own the namespace.
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    scene = bpy.context.scene
    rng = random.Random(seed)

    receipt = _build_receipt_plane()
    camera = _build_camera(scene, rng)
    _build_sun(scene)
    _build_world(scene, hdri_id)

    logger.debug(
        "build_scene seed={} hdri_id={} receipt_verts={} camera_loc={}",
        seed,
        hdri_id,
        len(receipt.data.vertices),
        tuple(camera.location),
    )
    return scene


def _build_receipt_plane():
    """Add the subdivided receipt plane and ensure identity UV unwrap.

    Returns the bpy.types.Object (named "receipt").
    """
    import bmesh
    import bpy

    # Add a 1x1 plane, then resize to the receipt's physical dimensions.
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0.0, 0.0, 0.0))
    receipt = bpy.context.active_object
    receipt.name = "receipt"
    receipt.data.name = "receipt_mesh"
    receipt.scale = (_RECEIPT_WIDTH_M, _RECEIPT_HEIGHT_M, 1.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    # Subdivide via bmesh for explicit control (~50 x ~80 vertices).
    bm = bmesh.new()
    bm.from_mesh(receipt.data)
    bmesh.ops.subdivide_edges(
        bm,
        edges=[e for e in bm.edges if abs(e.verts[0].co.x - e.verts[1].co.x) > 1e-6],
        cuts=_SUBDIVISIONS_X - 1,
        use_grid_fill=True,
    )
    bmesh.ops.subdivide_edges(
        bm,
        edges=[e for e in bm.edges if abs(e.verts[0].co.y - e.verts[1].co.y) > 1e-6],
        cuts=_SUBDIVISIONS_Y - 1,
        use_grid_fill=True,
    )

    # Build identity UVs on a fresh layer.
    uv_layer = bm.loops.layers.uv.verify()
    xs = [v.co.x for v in bm.verts]
    ys = [v.co.y for v in bm.verts]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    x_span = x_max - x_min
    y_span = y_max - y_min
    for face in bm.faces:
        for loop in face.loops:
            v = loop.vert
            u = (v.co.x - x_min) / x_span
            # Top of the receipt (y_max) maps to v=0; bottom (y_min) to v=1.
            v_uv = (y_max - v.co.y) / y_span
            loop[uv_layer].uv = (u, v_uv)

    bm.to_mesh(receipt.data)
    bm.free()
    receipt.data.update()
    return receipt


def _build_camera(scene, rng: random.Random):
    """Add a camera tilted ~35 deg from top-down, framing the receipt."""
    import bpy

    # Camera lives along the -Y axis, looking back at the origin from above.
    # We jitter very slightly with the rng so determinism is testable but
    # not so much that the receipt leaves the frame.
    jitter = rng.uniform(-0.005, 0.005)
    tilt_rad = math.radians(_CAMERA_TILT_DEG)
    cam_x = jitter
    cam_y = -math.sin(tilt_rad) * _CAMERA_DISTANCE
    cam_z = math.cos(tilt_rad) * _CAMERA_DISTANCE

    bpy.ops.object.camera_add(location=(cam_x, cam_y, cam_z))
    cam = bpy.context.active_object
    cam.name = "camera"
    cam.data.name = "camera_data"

    # Point camera at the origin: rotate around X by tilt, no y/z tilt.
    cam.rotation_euler = (tilt_rad, 0.0, 0.0)
    cam.data.lens = 35.0  # mm, gentle wide-ish

    scene.camera = cam
    return cam


def _build_sun(scene):
    """Add a sun light with a fixed direction for shadow definition."""
    import bpy

    bpy.ops.object.light_add(type="SUN", location=(0.0, 0.0, 1.0))
    sun = bpy.context.active_object
    sun.name = "sun"
    sun.data.energy = 3.0
    # Tilt slightly so the receipt gets a visible directional shadow.
    sun.rotation_euler = (math.radians(20.0), math.radians(15.0), 0.0)
    return sun


def _build_world(scene, hdri_id: str | None):
    """Set up the world's environment background.

    If an HDRI is available, wires it through a ShaderNodeTexEnvironment ->
    Background -> World Output node chain. Otherwise leaves a flat sky.
    """
    import bpy

    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    nt = world.node_tree

    # Resolve which HDRI to load.
    hdri_path: Path | None = None
    if hdri_id is not None:
        candidate = _HDRI_DIR / f"{hdri_id}.hdr"
        if candidate.exists():
            hdri_path = candidate
        else:
            logger.warning("hdri_id={} not found at {}; falling back", hdri_id, candidate)
    if hdri_path is None:
        available = list_hdris()
        if available:
            hdri_path = _HDRI_DIR / f"{available[0]}.hdr"

    # Reset world tree to a known-good chain.
    for node in list(nt.nodes):
        nt.nodes.remove(node)
    bg = nt.nodes.new("ShaderNodeBackground")
    out = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])

    if hdri_path is not None and hdri_path.exists():
        env = nt.nodes.new("ShaderNodeTexEnvironment")
        env.image = bpy.data.images.load(str(hdri_path), check_existing=True)
        nt.links.new(env.outputs["Color"], bg.inputs["Color"])
        logger.debug("loaded HDRI {}", hdri_path.name)
    else:
        bg.inputs["Color"].default_value = (0.6, 0.6, 0.65, 1.0)
        bg.inputs["Strength"].default_value = 1.0
