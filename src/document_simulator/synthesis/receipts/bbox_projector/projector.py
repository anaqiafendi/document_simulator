"""Token projector orchestrator (FDD #29 v0.3b AC-4b).

Walks a single ``TokenGroundTruth`` through the v0.3b coord chain:

    raster (already present) -> uv -> world -> camera_2d

For each new stage, a ``CoordSnapshot`` is appended to the token's ``coords``
list (never overwritten — the chain is append-only by FDD design).

The ``world`` snapshot carries both:
    - ``polygon`` — the xy slice (z dropped) for schema consistency, and
    - ``polygon_3d`` — the full 3D coords on the surface.

The ``camera_2d`` snapshot only carries ``polygon`` (image px).

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

from loguru import logger

from document_simulator.synthesis.receipts.bbox_projector.subdivide import (
    subdivide_polygon,
)
from document_simulator.synthesis.receipts.bbox_projector.uv_to_world import (
    UVSpatialHash,
    uv_to_world,
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
