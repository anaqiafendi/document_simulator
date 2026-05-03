"""Token projector orchestrator (FDD #29 v0.3b AC-4b, v0.3c AC-1c..AC-3c).

The v0.3b ``project_token`` walks a single ``TokenGroundTruth`` through:

    raster (already present) -> uv -> world -> camera_2d

The v0.3c ``project_token_full`` extends that chain with:

    -> visibility (mutates token.visible / token.occlusion_ratio)
    -> camera_fx (identity copy of camera_2d in v0.3)
    -> final_crop (Sutherland-Hodgman clipped to output image bounds)

Each stage *appends* a ``CoordSnapshot`` (never overwrites — the chain is
append-only by FDD design). The visibility step does not produce a
CoordSnapshot; it populates fields on ``TokenGroundTruth`` directly.

**Why two entry points?** The v0.3b round-trip test (AC-5b) projects through
``camera_2d`` only and asserts ``raster == camera_2d`` within ±2 px. Adding
``camera_fx`` and ``final_crop`` snapshots there would mean the test has to
look past them; keeping ``project_token`` strictly v0.3b preserves the test
as-is. Production callers that want the full chain (visibility + crop) call
``project_token_full`` and pass in the rendered UV pass + depth pass + the
cropped output size.

Polygon edges are subdivided BEFORE projecting so the resulting world /
camera-space polygon hugs the deformed surface (per design doc §2 critical
note: "subdivide bbox edges before projection — straight UV line becomes
curved on a deformed mesh").

For batch projection across many tokens against the same mesh, build a
single ``UVSpatialHash`` and pass it via the ``spatial_hash`` kwarg to
amortize hash construction. (Default behavior builds one per call.)
"""

from __future__ import annotations

from typing import Any

import numpy as np
from loguru import logger

from document_simulator.synthesis.receipts.bbox_projector.camera_fx import (
    apply_identity,
)
from document_simulator.synthesis.receipts.bbox_projector.clip import (
    apply_final_crop,
)
from document_simulator.synthesis.receipts.bbox_projector.subdivide import (
    subdivide_polygon,
)
from document_simulator.synthesis.receipts.bbox_projector.uv_to_world import (
    UVSpatialHash,
    uv_to_world,
)
from document_simulator.synthesis.receipts.bbox_projector.visibility import (
    compute_visibility,
)
from document_simulator.synthesis.receipts.bbox_projector.world_to_camera import (
    world_to_camera_2d,
)
from document_simulator.synthesis.receipts.schema import (
    CoordSnapshot,
    TokenGroundTruth,
)

# Number of equal sub-segments each polygon edge is split into before
# projection. 4 means each edge gains 3 intermediates -> a 4-corner bbox
# becomes 16 points after subdivision. Per FDD AC-2b.
_DEFAULT_EDGE_SEGMENTS = 4


def project_token(
    token: TokenGroundTruth,
    mesh: Any,
    scene: Any,
    camera: Any,
    render_size: tuple[int, int],
    raster_size: tuple[int, int],
    *,
    spatial_hash: UVSpatialHash | None = None,
    edge_segments: int = _DEFAULT_EDGE_SEGMENTS,
) -> TokenGroundTruth:
    """Append uv -> world -> camera_2d snapshots to ``token.coords`` in place.

    Args:
        token: A token whose ``coords`` already contains a ``raster``-stage
            snapshot (produced by ``render_receipt`` in v0.1). Mutated in
            place — the same object is also returned for fluent chaining.
        mesh: ``bpy.types.Mesh`` to barycentric-interpolate against (e.g.
            ``scene.objects["receipt"].data``). Must have an active UV layer.
        scene: ``bpy.types.Scene`` containing the camera.
        camera: ``bpy.types.Object`` of type CAMERA. Usually ``scene.camera``.
        render_size: ``(width, height)`` of the camera-space image in pixels.
            Used to scale NDC into pixel coords.
        raster_size: ``(width, height)`` of the raster-stage source image.
            Used to convert raster px to UV.
        spatial_hash: Optional pre-built ``UVSpatialHash`` to amortize across
            many tokens. If None, a new one is built per call (slow on big
            meshes — pass one in for production batch projection).
        edge_segments: Polygon-edge subdivision factor (per AC-2b). Default 4.

    Returns:
        The same ``token`` (mutated). Subsequent stages can be appended by
        v0.3c (visibility, camera_fx, final_crop).
    """
    raster_snap = next((c for c in token.coords if c.stage == "raster"), None)
    if raster_snap is None:
        raise ValueError(
            f"token {token.token_id!r} has no raster-stage CoordSnapshot — "
            f"available: {[c.stage for c in token.coords]}"
        )
    raster_polygon = raster_snap.polygon
    raster_w, raster_h = raster_size

    # 1. raster -> uv (trivial division by image dimensions). The receipt
    #    template renders at zoom = 96/72 so CSS px == image px.
    uv_polygon = [(x / raster_w, y / raster_h) for x, y in raster_polygon]
    token.coords.append(CoordSnapshot(stage="uv", polygon=uv_polygon))

    # 2. uv -> world. Subdivide the corners FIRST so the world polygon hugs
    #    surface curvature (per design doc §2 critical note).
    if spatial_hash is None:
        spatial_hash = UVSpatialHash(mesh)

    uv_polygon_subdivided = subdivide_polygon(uv_polygon, segments=edge_segments)
    world_polygon_3d: list[tuple[float, float, float]] = []
    for uv in uv_polygon_subdivided:
        world = uv_to_world(uv, mesh, spatial_hash=spatial_hash)
        if world is None:
            # Defensive: uv_to_world's _nearest_vertex_world fallback should
            # always return something for a single-island UV mesh, but if it
            # ever doesn't, we drop the corner rather than crash.
            logger.warning(
                "uv_to_world returned None for token={} uv={}; dropping corner",
                token.token_id,
                uv,
            )
            continue
        world_polygon_3d.append(world)

    token.coords.append(
        CoordSnapshot(
            stage="world",
            polygon=[(p[0], p[1]) for p in world_polygon_3d],  # xy slice
            polygon_3d=world_polygon_3d,
        )
    )

    # 3. world -> camera_2d via Y-flipped NDC.
    camera_polygon: list[tuple[float, float]] = []
    for world_pt in world_polygon_3d:
        px = world_to_camera_2d(world_pt, scene, camera, render_size)
        if px is None:
            # Behind camera — drop. v0.3c will handle full-polygon visibility
            # (a token with all corners behind the camera will have an empty
            # camera_polygon and downstream visibility marks it invisible).
            continue
        camera_polygon.append(px)

    token.coords.append(CoordSnapshot(stage="camera_2d", polygon=camera_polygon))
    return token


def project_token_full(
    token: TokenGroundTruth,
    mesh: Any,
    scene: Any,
    camera: Any,
    uv_pass: np.ndarray,
    depth_pass: np.ndarray,
    render_size: tuple[int, int],
    raster_size: tuple[int, int],
    output_size: tuple[int, int],
    *,
    spatial_hash: UVSpatialHash | None = None,
    edge_segments: int = _DEFAULT_EDGE_SEGMENTS,
    crop_origin: tuple[float, float] | None = None,
) -> TokenGroundTruth:
    """Run the full v0.3c chain on a single token, in place.

    Pipeline:

        1. ``project_token`` — appends ``uv``, ``world``, ``camera_2d``.
        2. ``compute_visibility`` — populates ``token.visible`` and
           ``token.occlusion_ratio`` based on the rendered UV pass.
        3. ``apply_identity`` — appends a ``camera_fx`` snapshot (identity
           copy of ``camera_2d`` in v0.3; non-trivial FX defer to v1.0).
        4. ``apply_final_crop`` — appends a ``final_crop`` snapshot with the
           Sutherland-Hodgman clipped polygon, OR sets ``visible=False`` and
           skips the snapshot if the polygon is fully off the cropped image.

    Visibility is computed against the ``camera_2d`` polygon (not the cropped
    one) on purpose: visibility is "is this surface rendered into the camera
    frame", which happens before the user-side crop.

    Args:
        token: Token with a ``raster`` snapshot. Mutated in place.
        mesh: ``bpy.types.Mesh`` with active UV layer.
        scene: ``bpy.types.Scene`` with a configured camera.
        camera: ``bpy.types.Object`` of type CAMERA.
        uv_pass: Per-pixel UV ``(H, W, 2)`` from ``render_eevee``.
        depth_pass: Per-pixel depth ``(H, W)`` from ``render_eevee``. Passed
            through to ``compute_visibility`` (currently unused in v0.3 —
            see visibility.py docstring).
        render_size: ``(width, height)`` of the camera-space image, must
            match the UV/depth pass shape.
        raster_size: ``(width, height)`` of the raster-stage source image.
        output_size: ``(width, height)`` of the cropped output image. Equal
            to ``render_size`` for "no crop".
        spatial_hash: Optional pre-built ``UVSpatialHash`` for batch reuse.
        edge_segments: Polygon-edge subdivision factor. Default 4 (per AC-2b).
        crop_origin: ``(x, y)`` offset of the crop window in render-space px.
            Defaults to centering the output inside the render:
            ``((render_w - output_w) / 2, (render_h - output_h) / 2)``.

    Returns:
        The same ``token`` (mutated). After this call ``token.coords`` has
        either 6 snapshots (raster + uv + world + camera_2d + camera_fx +
        final_crop) when visible, or 5 snapshots when fully off-frame.
    """
    if crop_origin is None:
        crop_origin = (
            (render_size[0] - output_size[0]) / 2.0,
            (render_size[1] - output_size[1]) / 2.0,
        )

    project_token(
        token,
        mesh=mesh,
        scene=scene,
        camera=camera,
        render_size=render_size,
        raster_size=raster_size,
        spatial_hash=spatial_hash,
        edge_segments=edge_segments,
    )
    compute_visibility(token, uv_pass, depth_pass, render_size)
    apply_identity(token)
    apply_final_crop(token, output_size=output_size, crop_origin=crop_origin)
    return token
