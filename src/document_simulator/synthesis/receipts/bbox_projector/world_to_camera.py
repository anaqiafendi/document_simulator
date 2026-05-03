"""World -> camera_2d (image px) projection (FDD #29 v0.3b AC-3b).

Wraps Blender's ``bpy_extras.object_utils.world_to_camera_view`` which
returns NDC ``(x, y, z)`` where:

    - ``x, y in [0, 1]`` if the point is inside the camera frustum
    - ``z`` is the *negated* camera-space depth — positive when the point is
      in front of the camera, negative when behind

We convert NDC to image pixels with the **Y-flip** per
``docs/coordinate-tracking-design.md`` §3:

    image_x = ndc.x * render_size[0]
    image_y = (1.0 - ndc.y) * render_size[1]

Blender NDC y is bottom-up; PIL / standard image px is top-down. The
``(1.0 - ndc.y)`` is the bug everyone hits — three different tests in
``test_bbox_projector_world_to_camera.py`` guard against it.
"""

from __future__ import annotations

from typing import Any


def world_to_camera_2d(
    world_pt: tuple[float, float, float],
    scene: Any,
    camera: Any,
    render_size: tuple[int, int],
) -> tuple[float, float] | None:
    """Project a world-space 3D point to image pixels via the active camera.

    Args:
        world_pt: ``(x, y, z)`` in world coordinates (meters).
        scene: ``bpy.types.Scene`` whose camera frame defines the projection.
        camera: ``bpy.types.Object`` of type CAMERA. Usually ``scene.camera``.
        render_size: ``(width_px, height_px)`` of the rendered image — used
            to scale NDC into pixel coords.

    Returns:
        ``(x_px, y_px)`` in image pixels (top-left origin, Y down), or None
        if the point is behind the camera (``ndc.z < 0`` per Blender's
        convention). Caller decides whether out-of-frustum-but-in-front points
        (ndc.x or ndc.y outside [0, 1]) should be kept; we return them with
        their (possibly negative or > render_size) px coords so downstream
        polygon clipping (v0.3c) can do the right thing.
    """
    import bpy_extras.object_utils
    import mathutils

    ndc = bpy_extras.object_utils.world_to_camera_view(scene, camera, mathutils.Vector(world_pt))
    # Behind-camera check. world_to_camera_view returns z < 0 when the point
    # is on the wrong side of the camera plane (i.e. behind it).
    if ndc.z < 0.0:
        return None

    width_px, height_px = render_size
    x_px = ndc.x * width_px
    # Y-FLIP — see module docstring + design doc §3.
    y_px = (1.0 - ndc.y) * height_px
    return (x_px, y_px)
