"""Unit tests for ``synthesis.receipts.bbox_projector.world_to_camera_2d``.

Covers FDD #29 v0.3b AC-3b: world_to_camera_2d wraps
``bpy_extras.object_utils.world_to_camera_view``, applies the Y-flip per
``docs/coordinate-tracking-design.md`` §3, and returns None for points
behind the camera.
"""

from __future__ import annotations

import math

import pytest

bpy = pytest.importorskip("bpy")  # noqa: F811

from document_simulator.synthesis.receipts.bbox_projector import (  # noqa: E402
    world_to_camera_2d,
)
from document_simulator.synthesis.receipts.scene import build_scene  # noqa: E402


def _bpy_reset() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=False)


def _set_camera_straight_down(scene, distance: float = 0.30) -> None:
    """Reposition the existing scene camera to look straight down at origin.

    Used by tests that need a deterministic ground-truth-aligned projection.
    The dependency-graph update is essential: bpy caches the camera's world
    matrix and ``world_to_camera_view`` reads from that cache, so without an
    explicit ``view_layer.update()`` the projection uses the *previous*
    camera pose.
    """
    cam = scene.camera
    cam.location = (0.0, 0.0, distance)
    cam.rotation_euler = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()


def test_world_to_camera_2d_origin_projects_to_image_center() -> None:
    """AC-3b: world (0, 0, 0) with camera straight down -> image center.

    Render is (1024, 1024). The camera looks straight down at the origin,
    so the world origin should land at (512, 512) within ~1 px tolerance
    (sub-pixel jitter from camera-jitter in build_scene is reset here).
    """
    _bpy_reset()
    scene = build_scene(seed=42, hdri_id=None)
    _set_camera_straight_down(scene)

    px = world_to_camera_2d((0.0, 0.0, 0.0), scene, scene.camera, (1024, 1024))
    assert px is not None
    x_px, y_px = px
    assert x_px == pytest.approx(512.0, abs=1.5)
    assert y_px == pytest.approx(512.0, abs=1.5)


def test_world_to_camera_2d_y_flip_correct() -> None:
    """AC-3b critical: world point at +y (toward the top of the receipt) lands
    in the *upper* half of the image (y < H/2).

    The Y-flip is the bug everyone hits. Per design doc §3:
        image_y = (1.0 - ndc.y) * render_size[1]
    With the camera looking straight down (-z) and aligned so that world +y
    is "up" in the camera frame, a world point at +y maps to a higher ndc.y,
    which after the (1 - ndc.y) flip lands in the *upper* half of the image
    (where y_px is small).
    """
    _bpy_reset()
    scene = build_scene(seed=42, hdri_id=None)
    _set_camera_straight_down(scene)

    # 5cm above the receipt origin (along world +y, on the receipt plane).
    px = world_to_camera_2d((0.0, 0.05, 0.0), scene, scene.camera, (1024, 1024))
    assert px is not None
    _x_px, y_px = px
    assert y_px < 512.0, (
        f"world +y should map to upper half of image (y < H/2); "
        f"got y_px={y_px}. The Y-flip is wrong."
    )


def test_world_to_camera_2d_returns_none_for_behind_camera() -> None:
    """AC-3b: a world point behind the camera returns None.

    Camera straight down at (0, 0, 0.30) looking toward -z (i.e. at origin).
    A point at (0, 0, +10) is way above (behind) the camera. The world-to-
    camera projection's z-component goes negative -> our wrapper must
    return None.
    """
    _bpy_reset()
    scene = build_scene(seed=42, hdri_id=None)
    _set_camera_straight_down(scene, distance=0.30)

    # (0, 0, +10) is far above the camera (which is at z=0.30 looking at -z).
    px = world_to_camera_2d((0.0, 0.0, 10.0), scene, scene.camera, (1024, 1024))
    assert px is None, f"behind-camera point must return None, got {px}"


def test_world_to_camera_2d_known_offset_lands_off_center() -> None:
    """Sanity: a +x offset moves the projection horizontally off-center.

    With camera straight down, no roll, world +x should map to image +x
    (x_px > W/2). This catches a sign error on the X axis the way the
    Y-flip test catches one on the Y axis.
    """
    _bpy_reset()
    scene = build_scene(seed=42, hdri_id=None)
    _set_camera_straight_down(scene)

    px = world_to_camera_2d((0.02, 0.0, 0.0), scene, scene.camera, (1024, 1024))
    assert px is not None
    x_px, _y_px = px
    assert x_px > 512.0, f"world +x should map to image +x; got x_px={x_px}"
    # Sanity: not unbounded
    assert math.isfinite(x_px)
