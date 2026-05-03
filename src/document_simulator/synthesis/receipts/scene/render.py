"""Eevee render + Cycles UV/depth passes for the receipt scene (v0.3a AC-6a).

Returns ``(rgb_image, uv_pass, depth_pass)``:

    - ``rgb_image``:  PIL.Image, the Eevee Next photoreal render.
    - ``uv_pass``:    np.ndarray of shape ``(H, W, 2)``, per-pixel UV from the
                     surface visible at that pixel. Background pixels are 0.
    - ``depth_pass``: np.ndarray of shape ``(H, W)``, per-pixel camera-space
                     distance. Background pixels carry Cycles' "infinity"
                     sentinel (~1e10).

Why two engines?
    bpy 4.2's ``BLENDER_EEVEE_NEXT`` engine does NOT expose the UV pass on the
    View Layer (the ``UV`` socket on ``CompositorNodeRLayers`` stays disabled
    even when ``view_layer.use_pass_uv = True`` is set). Cycles does, and at
    1 sample (the UV pass is deterministic per ray-hit) it renders a 1024x1024
    UV+depth pass in well under a second.

    So: photoreal RGB on Eevee Next; UV + depth on a 1-sample Cycles pass.
    Both rendered to OpenEXR through the compositor's OutputFile node, then
    read back via OpenCV. The compositor approach is simpler than the
    in-memory render-result API and works identically headless.

The function takes care of restoring the scene state (engine + view layer
passes + compositor) it mutates so callers can reuse the scene for further
operations.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import numpy as np

# Important: setting OPENCV_IO_ENABLE_OPENEXR before cv2 imports lets cv2 read
# the EXR files we write through the compositor.
os.environ.setdefault("OPENCV_IO_ENABLE_OPENEXR", "1")

import cv2  # noqa: E402
from loguru import logger  # noqa: E402
from PIL import Image  # noqa: E402


def render_eevee(
    scene,
    resolution: tuple[int, int] = (1024, 1024),
) -> tuple[Image.Image, np.ndarray, np.ndarray]:
    """Render the scene and return ``(rgb, uv_pass, depth_pass)``.

    Args:
        scene: ``bpy.types.Scene`` produced by
            :func:`document_simulator.synthesis.receipts.scene.builder.build_scene`.
            Must have ``scene.camera`` set.
        resolution: ``(width, height)`` in pixels for both the RGB and the
            UV/depth passes. The passes are sampled at exactly the same grid
            so the v0.3b bbox projector can index them by camera-space pixel.

    Returns:
        ``(rgb_image, uv_pass, depth_pass)`` — see module docstring for shapes
        and value conventions.
    """
    width, height = resolution
    if width <= 0 or height <= 0:
        raise ValueError(f"resolution must be positive, got {resolution}")
    if scene.camera is None:
        raise RuntimeError("scene.camera must be set before rendering")

    with tempfile.TemporaryDirectory(prefix="document_simulator_render_") as tmp:
        tmp_path = Path(tmp)

        rgb = _render_rgb_eevee(scene, width, height, tmp_path)
        uv_pass, depth_pass = _render_uv_depth_cycles(scene, width, height, tmp_path)

    logger.debug(
        "render_eevee resolution={} uv_hit_pixels={} depth_min={:.4f}",
        resolution,
        int(((uv_pass[..., 0] > 0) | (uv_pass[..., 1] > 0)).sum()),
        float(depth_pass.min()),
    )
    return rgb, uv_pass, depth_pass


# ---------------------------------------------------------------------------
# RGB pass (Eevee Next)
# ---------------------------------------------------------------------------


def _render_rgb_eevee(scene, width: int, height: int, tmp_path: Path) -> Image.Image:
    """Render the photoreal RGB image with Eevee Next; return as PIL.Image."""
    import bpy

    saved_engine = scene.render.engine
    saved_filepath = scene.render.filepath
    saved_format = scene.render.image_settings.file_format
    saved_use_nodes = scene.use_nodes
    saved_x = scene.render.resolution_x
    saved_y = scene.render.resolution_y
    saved_pct = scene.render.resolution_percentage
    try:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
        scene.render.resolution_x = width
        scene.render.resolution_y = height
        scene.render.resolution_percentage = 100
        scene.render.image_settings.file_format = "PNG"
        scene.use_nodes = False  # straight to filepath, no compositor

        rgb_path = tmp_path / "rgb.png"
        scene.render.filepath = str(rgb_path)
        bpy.ops.render.render(write_still=True)

        if not rgb_path.exists():
            raise RuntimeError(f"Eevee render produced no file at {rgb_path}")
        return Image.open(rgb_path).convert("RGB").copy()
    finally:
        scene.render.engine = saved_engine
        scene.render.filepath = saved_filepath
        scene.render.image_settings.file_format = saved_format
        scene.use_nodes = saved_use_nodes
        scene.render.resolution_x = saved_x
        scene.render.resolution_y = saved_y
        scene.render.resolution_percentage = saved_pct


# ---------------------------------------------------------------------------
# UV + depth passes (Cycles 1-sample)
# ---------------------------------------------------------------------------


def _render_uv_depth_cycles(
    scene,
    width: int,
    height: int,
    tmp_path: Path,
) -> tuple[np.ndarray, np.ndarray]:
    """Render UV pass + depth pass via Cycles 1-sample; return numpy arrays."""
    import bpy

    saved_engine = scene.render.engine
    saved_use_nodes = scene.use_nodes
    saved_use_pass_uv = scene.view_layers["ViewLayer"].use_pass_uv
    saved_use_pass_z = scene.view_layers["ViewLayer"].use_pass_z
    saved_x = scene.render.resolution_x
    saved_y = scene.render.resolution_y
    saved_pct = scene.render.resolution_percentage
    try:
        scene.render.engine = "CYCLES"
        scene.cycles.samples = 1
        scene.cycles.use_denoising = False
        scene.render.resolution_x = width
        scene.render.resolution_y = height
        scene.render.resolution_percentage = 100

        vl = scene.view_layers["ViewLayer"]
        vl.use_pass_uv = True
        vl.use_pass_z = True

        # Build a fresh compositor tree owning UV and Depth output files.
        scene.use_nodes = True
        ct = scene.node_tree
        for node in list(ct.nodes):
            ct.nodes.remove(node)
        rl = ct.nodes.new("CompositorNodeRLayers")
        # The Composite node is required by Blender even though we don't read
        # its output (otherwise the compositor short-circuits).
        comp = ct.nodes.new("CompositorNodeComposite")
        ct.links.new(rl.outputs["Image"], comp.inputs["Image"])

        uv_socket = _find_socket(rl, "UV")
        z_socket = _find_socket(rl, "Depth")
        if uv_socket is None or z_socket is None:
            raise RuntimeError(
                "Cycles RLayers does not expose UV/Depth sockets — "
                f"available: {[o.name for o in rl.outputs]}"
            )

        # UV pass: ``Vector(u, v, w)`` from Cycles. Wired straight into a
        # 3-channel EXR (cv2 reads it back as BGR -> R=u, G=v, B=0).
        out_uv = ct.nodes.new("CompositorNodeOutputFile")
        out_uv.base_path = str(tmp_path)
        out_uv.file_slots[0].path = "uv_"
        out_uv.format.file_format = "OPEN_EXR"
        out_uv.format.color_mode = "RGB"
        out_uv.format.color_depth = "32"
        ct.links.new(uv_socket, out_uv.inputs[0])

        # Depth pass: Cycles' Z socket is single-channel. cv2's OpenEXR
        # reader cannot decode single-channel EXRs reliably, so we splat
        # Z into all 3 channels via CombineColor before saving.
        comb = ct.nodes.new("CompositorNodeCombineColor")
        comb.mode = "RGB"
        ct.links.new(z_socket, comb.inputs[0])  # R
        ct.links.new(z_socket, comb.inputs[1])  # G
        ct.links.new(z_socket, comb.inputs[2])  # B
        out_depth = ct.nodes.new("CompositorNodeOutputFile")
        out_depth.base_path = str(tmp_path)
        out_depth.file_slots[0].path = "depth_"
        out_depth.format.file_format = "OPEN_EXR"
        out_depth.format.color_mode = "RGB"
        out_depth.format.color_depth = "32"
        ct.links.new(comb.outputs["Image"], out_depth.inputs[0])

        # Cycles writes with a frame suffix; track the current frame.
        frame = scene.frame_current
        bpy.ops.render.render(write_still=False)

        uv_file = tmp_path / f"uv_{frame:04d}.exr"
        depth_file = tmp_path / f"depth_{frame:04d}.exr"
        if not uv_file.exists() or not depth_file.exists():
            raise RuntimeError(
                f"Cycles compositor pass missing files: "
                f"uv={uv_file.exists()} depth={depth_file.exists()}"
            )

        uv_pass = _read_exr_uv(uv_file)
        depth_pass = _read_exr_depth(depth_file)

        # Verify shapes against requested resolution.
        if uv_pass.shape[:2] != (height, width):
            raise RuntimeError(f"uv_pass shape {uv_pass.shape} != requested ({height}, {width})")
        if depth_pass.shape != (height, width):
            raise RuntimeError(
                f"depth_pass shape {depth_pass.shape} != requested ({height}, {width})"
            )
        return uv_pass, depth_pass
    finally:
        scene.render.engine = saved_engine
        scene.use_nodes = saved_use_nodes
        scene.view_layers["ViewLayer"].use_pass_uv = saved_use_pass_uv
        scene.view_layers["ViewLayer"].use_pass_z = saved_use_pass_z
        scene.render.resolution_x = saved_x
        scene.render.resolution_y = saved_y
        scene.render.resolution_percentage = saved_pct


def _find_socket(node, name: str):
    """Return the (sometimes index-only-addressable) socket by name.

    Compositor RLayers sometimes refuses ``rl.outputs[name]`` lookups for
    sockets that are *technically* enabled by passes but not yet refreshed.
    We iterate to be safe.
    """
    for socket in node.outputs:
        if socket.name == name:
            return socket
    return None


def _read_exr_uv(path: Path) -> np.ndarray:
    """Read an OpenEXR UV pass into shape ``(H, W, 2)`` float32.

    Cycles' UV pass writes ``(u, v, w)`` per pixel into RGB channels (w is
    always 0 for surfaces). We drop the third channel.
    """
    img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if img is None:
        raise RuntimeError(f"cv2 could not read {path} (is OpenEXR support enabled?)")
    if img.ndim == 2:
        # Single-channel — pad to (H, W, 2)
        return np.stack([img, np.zeros_like(img)], axis=-1).astype(np.float32)
    # cv2 reads as BGR(A); for UV channels the visual ordering is
    # B=u, G=v, R=0 in Cycles — but cv2 reorders to BGR -> R=u, G=v, B=0.
    # We slice the first two channels in OpenCV's BGR order: index 2 is "R"
    # (== u in Cycles), index 1 is "G" (== v in Cycles).
    if img.shape[2] >= 3:
        u = img[..., 2].astype(np.float32)
        v = img[..., 1].astype(np.float32)
        return np.stack([u, v], axis=-1)
    return img.astype(np.float32)


def _read_exr_depth(path: Path) -> np.ndarray:
    """Read an OpenEXR depth pass into shape ``(H, W)`` float32."""
    img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if img is None:
        raise RuntimeError(f"cv2 could not read {path}")
    if img.ndim == 3:
        # All channels carry the same depth — pick channel 0.
        img = img[..., 0]
    return img.astype(np.float32)
