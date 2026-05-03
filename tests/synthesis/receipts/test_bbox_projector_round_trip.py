"""Round-trip identity test (FDD #29 v0.3b AC-5b — THE GATE).

If this test fails, the entire bbox-projection chain has a sign error and
nothing downstream (visibility, camera_fx, final_crop) can be trusted.

Setup:
    - Render a thermal_minimal receipt at seed=42 to get raster-stage tokens.
    - Build a 3D scene with curl_strength=0.0, fold_count=0 (FLAT plane).
    - Reposition the camera to look straight down at the receipt center.
    - Project every token with render_size == raster_size.

Assertion:
    For every token, the projected ``camera_2d.polygon`` matches that token's
    ``raster.polygon`` corner-by-corner within +/- 2 px.

The match proves:
    - The raster -> uv mapping divides by the right (W, H)
    - The uv -> world barycentric is consistent with the planar identity
    - The world -> camera_2d Y-flip is in the right direction
    - The render-size scaling is consistent
"""

from __future__ import annotations

import pytest

bpy = pytest.importorskip("bpy")  # noqa: F811

from document_simulator.synthesis.receipts.bbox_projector import project_token  # noqa: E402
from document_simulator.synthesis.receipts.content import make_minimal_receipt  # noqa: E402
from document_simulator.synthesis.receipts.render import render_receipt  # noqa: E402
from document_simulator.synthesis.receipts.scene import (  # noqa: E402
    build_scene,
    deform_paper,
)


def _bpy_reset() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=False)


def _set_camera_straight_down_filling_receipt(scene, raster_size: tuple[int, int]) -> None:
    """Position the camera straight down with the receipt filling the frame.

    The receipt is 80 mm x 200 mm. To keep the round-trip identity test
    purely aspect-ratio-aware (so that an 80x200 receipt rendered at e.g.
    303x756 raster lands corner-to-corner on a 303x756 camera image), we
    set up an orthographic camera framing the receipt exactly.

    Orthographic projection avoids the perspective foreshortening that a
    perspective camera introduces — for the round-trip test we want pure
    coordinate-system gymnastics, not optics.

    Blender's ``ortho_scale`` is the *longer* image dimension's framed-world
    size: when the render is portrait (H > W), ortho_scale == framed world
    height; landscape (W > H), ortho_scale == framed world width. For a
    receipt whose own aspect matches the raster aspect (within float32
    tolerance) we just set ortho_scale to the receipt's longer dimension.
    """
    cam = scene.camera
    cam.location = (0.0, 0.0, 0.30)
    cam.rotation_euler = (0.0, 0.0, 0.0)
    cam.data.type = "ORTHO"

    # Receipt physical bounds, queried from the mesh so this is robust to any
    # future change in builder._RECEIPT_*_M.
    mesh = scene.objects["receipt"].data
    xs = [v.co.x for v in mesh.vertices]
    ys = [v.co.y for v in mesh.vertices]
    receipt_w = max(xs) - min(xs)
    receipt_h = max(ys) - min(ys)

    # ortho_scale is the longer-side framed world distance. The receipt's
    # aspect (W/H) matches the raster's by template construction, so the
    # short side falls into place.
    raster_w, raster_h = raster_size
    if raster_w >= raster_h:
        cam.data.ortho_scale = receipt_w
    else:
        cam.data.ortho_scale = receipt_h

    # Configure render resolution to exactly match the raster.
    scene.render.resolution_x = raster_w
    scene.render.resolution_y = raster_h
    scene.render.resolution_percentage = 100

    bpy.context.view_layer.update()


def test_round_trip_identity_flat_plane() -> None:
    """AC-5b — THE GATE: flat mesh + straight-down ortho camera + matched
    sizes -> projected camera_2d.polygon == raster.polygon within +/- 2 px.
    """
    # 1. Render the receipt to get the raster-stage tokens.
    receipt = make_minimal_receipt(seed=42)
    image, gt = render_receipt(receipt, seed=42)
    raster_size = image.size  # (W, H)

    # 2. Build a flat 3D scene framed exactly to the receipt.
    _bpy_reset()
    scene = build_scene(seed=42, hdri_id=None)
    mesh = scene.objects["receipt"].data
    deform_paper(mesh, curl_strength=0.0, fold_count=0, seed=42)
    _set_camera_straight_down_filling_receipt(scene, raster_size)

    # 3. Project every token.
    for token in gt.tokens:
        project_token(
            token,
            mesh=mesh,
            scene=scene,
            camera=scene.camera,
            render_size=raster_size,
            raster_size=raster_size,
        )

    # 4. Assert raster.polygon == camera_2d.polygon corner-by-corner.
    tol_px = 2.0
    for token in gt.tokens:
        raster_snap = next(c for c in token.coords if c.stage == "raster")
        cam_snap = next((c for c in token.coords if c.stage == "camera_2d"), None)
        assert cam_snap is not None, (
            f"token {token.token_id!r} missing camera_2d snapshot — "
            f"available stages: {[c.stage for c in token.coords]}"
        )

        # The camera_2d polygon includes the 4 corners + subdivided
        # intermediates. We only compare the first 4 (corners) to the raster
        # quad.
        cam_corners = cam_snap.polygon[:4]
        for (rx, ry), (cx, cy) in zip(raster_snap.polygon, cam_corners, strict=True):
            assert abs(rx - cx) <= tol_px and abs(ry - cy) <= tol_px, (
                f"token {token.token_id!r} corner mismatch: "
                f"raster=({rx:.2f}, {ry:.2f}) camera_2d=({cx:.2f}, {cy:.2f}) "
                f"delta=({cx - rx:.2f}, {cy - ry:.2f}) > +/- {tol_px}px"
            )
