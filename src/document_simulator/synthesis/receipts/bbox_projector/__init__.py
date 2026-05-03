"""Bbox projector — uv -> world -> camera_2d coordinate chain (FDD #29 v0.3b).

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
        Orchestrator: appends ``uv``, ``world`` (with ``polygon_3d``), and
        ``camera_2d`` ``CoordSnapshot``s to the token's coord chain.

The bpy-dependent symbols are imported lazily to keep ``import
document_simulator.synthesis.receipts.bbox_projector`` working on
interpreters without a bpy wheel (Python 3.10/3.12). The lazy resolver
overrides Python's default attribute lookup *only* if the symbol has not
been imported yet.
"""

from __future__ import annotations

# subdivide_polygon is pure-Python and bpy-free; safe to eager-import.
from document_simulator.synthesis.receipts.bbox_projector.subdivide import (
    subdivide_polygon as subdivide_polygon,
)

__all__ = [
    "UVSpatialHash",
    "project_token",
    "subdivide_polygon",
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
    if name == "project_token":
        import importlib

        _proj_mod = importlib.import_module(
            "document_simulator.synthesis.receipts.bbox_projector.projector"
        )
        globals()["project_token"] = _proj_mod.project_token
        return globals()["project_token"]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
