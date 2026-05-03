"""Photoreal receipt synthesis — 3D scene module (FDD #29 v0.3a).

Public API:
    build_scene(seed, hdri_id=None) -> bpy.types.Scene
        Programmatically construct a Blender scene: subdivided receipt plane
        with identity UV unwrap, top-down camera, sun light + HDRI environment.
    deform_paper(mesh, curl_strength, fold_count, seed) -> None
        Apply procedural curl + sparse fold lines to a flat receipt mesh
        in place. UV coordinates are NEVER modified.
    render_eevee(scene, resolution) -> tuple[PIL.Image, np.ndarray, np.ndarray]
        Render with Eevee Next for the photoreal RGB plus a Cycles 1-sample
        pass for UV + depth (Eevee 4.2 does not support the UV pass).
    list_hdris() -> list[str]
        IDs of HDRI files bundled in data/hdri/.

Heavy imports (``bpy``, ``bmesh``, ``mathutils``, ``cv2``) happen lazily inside
the implementation modules so importing
``document_simulator.synthesis.receipts`` on a non-bpy interpreter (3.10/3.12)
does not fail.

Important: this module must be imported BEFORE cv2 anywhere else in the
process. cv2's OpenEXR codec is gated on the ``OPENCV_IO_ENABLE_OPENEXR``
environment variable, which we set on import. Once cv2 is loaded the gate
freezes — set the env var on the shell side (``OPENCV_IO_ENABLE_OPENEXR=1
uv run pytest …``) for full safety.
"""

from __future__ import annotations

import os

# Must be set before cv2 is imported anywhere in the process. See module
# docstring above.
os.environ.setdefault("OPENCV_IO_ENABLE_OPENEXR", "1")

from document_simulator.synthesis.receipts.scene.builder import (  # noqa: E402
    build_scene,
    list_hdris,
)
from document_simulator.synthesis.receipts.scene.mesh import deform_paper  # noqa: E402
from document_simulator.synthesis.receipts.scene.render import render_eevee  # noqa: E402

__all__ = [
    "build_scene",
    "deform_paper",
    "list_hdris",
    "render_eevee",
]
