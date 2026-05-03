"""Bbox projector — uv -> world -> camera_2d -> camera_fx -> final_crop chain.

(FDD #29 v0.3b + v0.3c)

Public API:
    subdivide_polygon(polygon, segments) -> list[(x, y)]
        Add intermediate points along each edge so polygons can follow
        surface curvature when projected through a deformed mesh.
    UVSpatialHash
        UV-grid index over a mesh's loop triangles for O(1) "which triangle
        contains this UV?" lookup.
    uv_to_world(uv, mesh, hash=None) -> (x, y, z)
        Barycentric interpolation of mesh world coords from a (u, v) point.
    world_to_camera_2d(world_pt, scene, camera, render_size) -> (x_px, y_px) | None
        Wraps ``bpy_extras.object_utils.world_to_camera_view`` and applies
        the Y-flip so output is in image-px (top-left origin, Y down).
    project_token(token, mesh, scene, camera, render_size, raster_size) -> token
        v0.3b orchestrator: appends ``uv``, ``world`` (with ``polygon_3d``),
        and ``camera_2d`` snapshots to the token's coord chain.
    project_token_full(token, mesh, scene, camera, uv_pass, depth_pass,
            render_size, raster_size, output_size) -> token
        v0.3c orchestrator: project_token + compute_visibility +
        apply_identity (camera_fx) + apply_final_crop.
    compute_visibility(token, uv_pass, depth_pass, render_size) -> None
        Sample the polygon, compare rendered UVs against expected, populate
        ``token.visible`` and ``token.occlusion_ratio``.
    uv_distance(uv_a, uv_b) -> float
        Euclidean UV-space distance (no seam wrap-around in v0.3).
    apply_identity(token) -> None
        v0.3 camera_fx stage — copies the prior polygon verbatim. Real FX
        in v1.0.
    sutherland_hodgman_clip(subject_polygon, clip_polygon) -> list[(x, y)]
        Polygon-on-polygon clipping. Empty list when fully outside.
    apply_final_crop(token, output_size, crop_origin=(0, 0)) -> None
        Subtract crop_origin, clip to output bounds, append final_crop
        snapshot OR set ``visible=False`` if fully off-frame.

The bpy-dependent symbols are imported lazily to keep ``import
document_simulator.synthesis.receipts.bbox_projector`` working on
interpreters without a bpy wheel (Python 3.10/3.12). The lazy resolver
overrides Python's default attribute lookup *only* if the symbol has not
been imported yet.
"""

from __future__ import annotations

# Pure-Python (bpy-free) symbols are safe to eager-import.
from document_simulator.synthesis.receipts.bbox_projector.camera_fx import (
    apply_identity as apply_identity,
)
from document_simulator.synthesis.receipts.bbox_projector.clip import (
    apply_final_crop as apply_final_crop,
)
from document_simulator.synthesis.receipts.bbox_projector.clip import (
    sutherland_hodgman_clip as sutherland_hodgman_clip,
)
from document_simulator.synthesis.receipts.bbox_projector.subdivide import (
    subdivide_polygon as subdivide_polygon,
)
from document_simulator.synthesis.receipts.bbox_projector.visibility import (
    compute_visibility as compute_visibility,
)
from document_simulator.synthesis.receipts.bbox_projector.visibility import (
    uv_distance as uv_distance,
)

__all__ = [
    "UVSpatialHash",
    "apply_final_crop",
    "apply_identity",
    "compute_visibility",
    "project_token",
    "project_token_full",
    "subdivide_polygon",
    "sutherland_hodgman_clip",
    "uv_distance",
    "uv_to_world",
    "world_to_camera_2d",
]


def __getattr__(name: str):
    """Lazy attribute resolution for bpy-dependent symbols.

    Importing the bpy-touching submodules at package import time would break
    importing on Python 3.10/3.12 (no bpy wheel). Resolve those symbols on
    first access and cache them in ``globals()`` so subsequent accesses are
    plain attribute lookups (Python skips ``__getattr__`` once the name is
    in the module dict).
    """
    if name in ("uv_to_world", "UVSpatialHash"):
        import importlib

        _uv_mod = importlib.import_module(
            "document_simulator.synthesis.receipts.bbox_projector.uv_to_world"
        )
        globals()["uv_to_world"] = _uv_mod.uv_to_world
        globals()["UVSpatialHash"] = _uv_mod.UVSpatialHash
        return globals()[name]
    if name == "world_to_camera_2d":
        import importlib

        _wc_mod = importlib.import_module(
            "document_simulator.synthesis.receipts.bbox_projector.world_to_camera"
        )
        globals()["world_to_camera_2d"] = _wc_mod.world_to_camera_2d
        return globals()["world_to_camera_2d"]
    if name in ("project_token", "project_token_full"):
        import importlib

        _proj_mod = importlib.import_module(
            "document_simulator.synthesis.receipts.bbox_projector.projector"
        )
        globals()["project_token"] = _proj_mod.project_token
        globals()["project_token_full"] = _proj_mod.project_token_full
        return globals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
