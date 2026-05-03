# Coordinate Tracking Design — UV → World → Camera → Final

This document is the **prerequisite design spec for v0.3** of the photoreal receipt synthesis pipeline (FDD #29). It traces one specific token through every coordinate space the bbox projector must handle, with concrete numbers, so the implementation has a worked example to validate against.

The bbox projector is the engineering crux of the whole project (plan §4, both judge agents). 600–900 LoC budget, 1–2 week debug horizon. The cheapest insurance against discovering at 800 LoC that step 4 has a Y-flip is to trace one token end-to-end first.

---

## Setup

We render a `restaurant_tip.html.j2` receipt at seed=99 (matches the v0.2 demo). Pick the `total` token — it's near the bottom of the receipt, so any Y-axis bug will be visible.

After v0.2's raster step, the GT for the `total` token looks like:

```python
TokenGroundTruth(
    token_id="total",
    text="$24.50",
    semantic_role="total",
    coords=[
        CoordSnapshot(stage="raster", polygon=[
            (245.5, 720.0),  # top-left   in CSS px
            (310.2, 720.0),  # top-right
            (310.2, 738.5),  # bottom-right
            (245.5, 738.5),  # bottom-left
        ])
    ],
)
```

The rendered raster image is **333 × 832** pixels. Top-left origin, X right, Y down. CSS px = image px (because we render PDF at zoom = 96/72 per FDD #27 decision #6).

---

## Stage chain

### 1. `raster` → `uv`

Trivial when the receipt plane is flat-unwrapped (which our `.blend` template guarantees). Each (x_px, y_px) → (u, v) ∈ [0, 1]²:

```
u = x_px / W = 245.5 / 333 = 0.7372
v = y_px / H = 720.0 / 832 = 0.8654
```

For the `total` token's polygon corners:

```python
CoordSnapshot(stage="uv", polygon=[
    (245.5/333, 720.0/832),   # (0.7372, 0.8654)
    (310.2/333, 720.0/832),   # (0.9315, 0.8654)
    (310.2/333, 738.5/832),   # (0.9315, 0.8876)
    (245.5/333, 738.5/832),   # (0.7372, 0.8876)
])
```

**Failure modes at this stage:**
- The `.blend` file's UV unwrap is not identity (the artist used `Smart UV Project` instead of a planar projection). **Mitigation:** v0.3 ships a programmatically-generated `.blend` with explicit identity UV; the unit test `test_uv_is_identity` asserts every mesh vertex's UV equals `(world_xy_pre_deform - mesh_origin) / mesh_size`.
- DPI mismatch: if the raster image is computed at a different zoom than the renderer's CSS px, the division above is wrong. **Mitigation:** assert `image_size == (W, H)` matches the WeasyPrint `Document.pages[0].width / height` × `(zoom)`.

### 2. `uv` → `world` (the curved-mesh part)

This is where it gets interesting. The receipt mesh is a subdivided plane with curl + fold deformations (procedural, not Doc3D — per plan §2 stack table). For each polygon corner in UV space, we need its 3D world position.

**Algorithm**:
1. Find the mesh face (triangle) whose UV-space triangle contains the input UV point. Mesh has ~50×80 = 4000 quads = 8000 triangles. Linear scan is fine for hundreds of token-corners; a UV-spatial-hash makes it O(1) for thousands.
2. Compute barycentric coordinates of the UV point within that triangle.
3. Apply the same barycentric weights to the triangle's 3 *world*-space vertices to get the 3D position.

For the `total` token's top-left corner at UV (0.7372, 0.8654):

Suppose this UV falls inside triangle T whose vertices are:
```
v0_uv = (0.72, 0.85),  v0_world = (-0.0014, -0.0085, 0.0023)
v1_uv = (0.74, 0.85),  v1_world = ( 0.0006, -0.0085, 0.0019)
v2_uv = (0.72, 0.87),  v2_world = (-0.0014, -0.0105, 0.0028)
```

Barycentric weights for input UV (0.7372, 0.8654):
```
b0 + b1 + b2 = 1
b0 * v0_uv + b1 * v1_uv + b2 * v2_uv = (0.7372, 0.8654)
```

Solving (concrete numbers):
```
b1 = 0.86, b0 = 0.13, b2 = 0.01   (approximate)
```

World position:
```
world = b0*v0_world + b1*v1_world + b2*v2_world
      = 0.13*(-0.0014, -0.0085, 0.0023) + 0.86*(0.0006, -0.0085, 0.0019) + 0.01*(-0.0014, -0.0105, 0.0028)
      ≈ (0.00033, -0.00853, 0.00197)   meters in world space
```

Z is ~2mm — the receipt is curled enough that this point sits ~2mm above the desk plane.

**Critical**: do this **per polygon corner**, not just the centroid. A bbox is straight in UV but **curved** in world (when the mesh is curved). Approximating with the centroid alone hides the curvature.

**Critical-er**: when the bbox edge in UV crosses multiple triangles (which it usually does for a long horizontal text bbox), **subdivide the bbox edge in UV before mapping**. Otherwise the world-space polygon is a flat 4-gon that ignores the surface curvature between the corners. Suggested: 4–8 intermediate points per edge depending on curvature.

```python
CoordSnapshot(
    stage="world",
    polygon=[(world.x, world.y) for world in projected_corners_2d],  # 2D dropped — kept in polygon_3d below
    polygon_3d=[
        (0.00033, -0.00853, 0.00197),   # top-left in world
        (0.00226, -0.00857, 0.00161),   # top-right
        (0.00226, -0.00879, 0.00163),   # bottom-right
        (0.00033, -0.00875, 0.00198),   # bottom-left
        # plus subdivided intermediate points along each edge (~16 extra points for 4 edges × 4 subdiv)
    ],
)
```

`polygon_3d` is set; `polygon` (2D) holds the polygon_3d's xy with z dropped — it's not directly useful but we keep it for schema consistency. (Alternative: leave `polygon` empty / set to a sentinel for the world stage. Decision: populate with xy projection for completeness; consumer code reads `polygon_3d` for the world stage.)

**Failure modes:**
- Triangle search returns no hit (UV point lies outside mesh, e.g. near a UV seam). **Mitigation:** clamp UV to [ε, 1-ε] before search; log a warning and skip the corner if still no hit.
- Barycentric coords negative (numerical precision near triangle edges). **Mitigation:** snap to nearest valid baryentric (clamp each component to [0, 1] and renormalize).
- Mesh has multiple UV islands (Smart UV Project) and the same UV point exists on multiple triangles. **Mitigation:** ship a single-island identity unwrap in v0.3; document the constraint; v1.0 can lift it if needed.

### 3. `world` → `camera_2d`

Use `bpy_extras.object_utils.world_to_camera_view(scene, camera, world_point) → Vector3D` which returns NDC `(x, y, z)` where `x, y ∈ [0, 1]` if the point is in frustum, and `z` is the negated camera-space depth (positive = in front of camera).

Convert NDC to image px:

```
image_x = ndc.x * render_resolution_x
image_y = (1.0 - ndc.y) * render_resolution_y   # ← Y FLIP
```

The Y-flip is the bug everyone hits. Blender's NDC Y-axis is bottom-up; our image px Y-axis is top-down (per PIL / standard image convention).

For the `total` token's top-left world corner (0.00033, -0.00853, 0.00197), assume the camera is at (0, -0.05, 0.08) looking down at -45°, fov=50°, render_res=(1024, 1024):

`world_to_camera_view` returns approximately `Vector((0.484, 0.232, 0.046))`:
- ndc.x = 0.484 → image_x = 0.484 * 1024 = **495.6** px
- ndc.y = 0.232 → image_y = (1 - 0.232) * 1024 = 0.768 * 1024 = **786.4** px

So the corner that was at raster-px (245.5, 720.0) on a 333×832 receipt is now at camera-px (495.6, 786.4) on a 1024×1024 photo. That makes sense: the receipt is in the bottom half of the photo (it's lying on a desk, photographed from above), and the `total` token is in the lower-right area.

```python
CoordSnapshot(stage="camera_2d", polygon=[
    (495.6, 786.4),   # top-left of total bbox in camera image px
    (538.2, 786.1),   # top-right
    (538.5, 802.7),   # bottom-right
    (495.9, 803.0),   # bottom-left
    # + subdivided intermediates (the whole quadrilateral may bend slightly under perspective)
])
```

**Failure modes:**
- Y-flip applied wrong direction (or to ndc.x). **Mitigation:** `test_camera_projection_known_point` — pass in the known-corner of the receipt mesh (e.g. the mesh origin), assert it lands within ±2 px of the expected image-px position computed by hand.
- World point behind camera (`ndc.z < 0`). **Mitigation:** mark the polygon `visible=False`, skip downstream stages, log warning.
- Polygon partially out of frustum (some corners inside, some outside). **Mitigation:** clip in 3D before projecting via Sutherland-Hodgman in NDC. **Do NOT just clamp pixel coords — that creates incorrect bboxes.**

### 4. Visibility / occlusion

For each token, sample N points (we use 4 corners + 4 edge midpoints + 1 centroid = 9) inside the polygon at this stage. For each sample:
1. Read the **UV pass** at that pixel — get the (u, v) of whatever surface point is visible at that pixel.
2. Read the **depth pass** at that pixel — get the camera-space distance to that visible surface point.
3. Compare the visible UV against the token's expected UV (from the `uv` stage CoordSnapshot). If they match within ε (e.g. 0.01 in UV space ≈ ~3 receipt-px), the token is visible at that sample.

```python
visible_count = 0
for sample_uv in sampled_uv_points:
    px = uv_to_camera_px(sample_uv)
    visible_uv_at_px = uv_pass[px.y, px.x]   # what surface is rendered at this pixel
    if uv_distance(sample_uv, visible_uv_at_px) < 0.01:
        visible_count += 1
occlusion_ratio = 1.0 - (visible_count / N)
visible = occlusion_ratio < 0.7  # token is "visible" if ≥30% of sample points are unoccluded
```

For our `total` token with no hand or other occluder in the scene, all 9 samples should pass → `occlusion_ratio = 0.0`, `visible = True`.

If the user adds a hand mesh that covers the right half of the receipt, samples on the right side would fail (the visible UV at those pixels would be from the hand mesh's UV, not the receipt's UV). We'd see e.g. 4/9 visible → `occlusion_ratio = 0.555`.

**Failure modes:**
- UV pass is at a different resolution than the final render. **Mitigation:** force both passes at full render resolution.
- Per-pixel UV is anti-aliased at glyph edges, returning interpolated nonsense. **Mitigation:** sample only interior points (avoid corners); for a 4×4 px glyph, use the centroid only.
- Hand mesh has its own UV that happens to match the receipt's UV space. **Mitigation:** check the visible surface's *object ID* via the segmentation pass instead of UV alone. (Implement if false positives become a problem; not part of v0.3.)

### 5. `camera_2d` → `camera_fx`

In v0.3 there are no camera FX yet — `camera_fx == camera_2d` (the snapshot is duplicated for schema consistency). v1.0 adds lens distortion (non-affine — needs `cv2.undistortPoints`), motion blur (no coord shift), DoF (no coord shift), JPEG (no coord shift).

When v1.0 ships lens distortion with intrinsics K and distortion coeffs D:

```python
import cv2
distorted_polygon = cv2.undistortPoints(
    polygon.reshape(-1, 1, 2),
    cameraMatrix=K, distCoeffs=D,
    P=K,  # output in same pixel coords
).reshape(-1, 2)
```

Note: `cv2.undistortPoints` is the *forward* operation when used with a camera-to-undistorted-image direction. We want the inverse — points in the rendered image projected forward through the simulated lens distortion. That's `cv2.projectPoints` with translation/rotation = identity, applied to the polygon corners as 3D points at z=1.

**Decision deferred to v1.0**: pick the right OpenCV call once the distortion model is locked.

### 6. `camera_fx` → `final_crop`

The user specifies an output resolution (e.g. 1024×1024). The render may be at a different resolution (e.g. 1920×1080 with the receipt centered). Final crop:

```python
crop_x = (render_w - output_w) / 2
crop_y = (render_h - output_h) / 2

final_polygon = [(x - crop_x, y - crop_y) for x, y in input_polygon]
```

Then **clip to image bounds with Sutherland-Hodgman** (not just min/max — see plan §4.2):

```python
clipped = sutherland_hodgman(final_polygon, [(0,0), (output_w,0), (output_w,output_h), (0,output_h)])
if not clipped:
    visible = False
elif len(clipped) < 4:
    # partial — keep as-is; downstream consumers handle non-quad polygons
    pass
```

For the `total` token at camera_2d (495.6, 786.4 → 538.5, 803.0), if output is 1024×1024 and render was 1024×1024 (no crop), `final_polygon == camera_2d.polygon`. Clipping is a no-op (all in bounds).

If output were 1024×768 with crop_y=128, the polygon Y values become (786.4 - 128, ...) = (658.4, ...) — still in bounds, no clip.

---

## End-to-end summary for the `total` token

| Stage | Polygon corners (top-left only shown) | Notes |
|---|---|---|
| raster | (245.5, 720.0) px | from WeasyPrint text_lines |
| uv | (0.7372, 0.8654) | direct division |
| world | xy=(0.00033, -0.00853), z=0.00197 m | barycentric on curved mesh |
| camera_2d | (495.6, 786.4) px on 1024² image | bpy_extras + Y-flip |
| visibility | visible=True, occlusion=0.0 | UV pass match |
| camera_fx | (495.6, 786.4) px | identity in v0.3 |
| final_crop | (495.6, 786.4) px | identity (no crop in this example) |

The `coords` list on the token after v0.3 has 6 snapshots (raster + uv + world + camera_2d + camera_fx + final_crop). The visibility info lives on the TokenGroundTruth itself (`visible`, `occlusion_ratio` fields), not as a CoordSnapshot.

---

## Validation strategy (no OCR, per plan §4.5)

1. **Round-trip identity test**: with mesh deformation = 0 (flat plane), camera looking straight down, no crop, output_size == raster_size: assert `final_crop polygon == raster polygon` within ±1 px. If this fails, the chain has a sign error.
2. **Single-point sanity test**: hand-pick one corner of the mesh (e.g. the top-left vertex), trace it through the chain, assert the camera_2d projection matches a hand-computed expected position within ±2 px.
3. **Pixel-content statistical test (gate #3 from plan §4.5)**: for each visible token's `final_crop` polygon, sample 20 pixels inside vs outside; assert `mean(inside) < mean(outside) - threshold`. If the projected polygon doesn't actually contain text pixels, the chain is wrong somewhere.
4. **Visual overlay test**: extend `synthesis.receipts.overlay.draw_overlay()` to accept any stage (`stage="world"` would draw the polygon_3d xy projection; `stage="camera_2d"` would draw on the camera-rendered image). Manual eyeball.
5. **Stage selector in the UI**: the React inspector's stage dropdown lets the dev visualize any intermediate `CoordSnapshot` over its corresponding image. This is the **debugging tool** that justifies the append-only coords list design.

---

## Implementation skeleton (Python, ~600 LoC)

```python
# synthesis.receipts.bbox_projector

def project_token_through_pipeline(
    token: TokenGroundTruth,
    mesh: bpy.types.Mesh,
    scene: bpy.types.Scene,
    camera: bpy.types.Object,
    uv_pass: np.ndarray,         # (H, W, 2) per-pixel UV
    depth_pass: np.ndarray,      # (H, W) per-pixel camera-space depth
    render_size: tuple[int, int],
    output_size: tuple[int, int],
    distortion: dict | None = None,  # v1.0
) -> TokenGroundTruth:
    """Append uv → world → camera_2d → camera_fx → final_crop snapshots,
    plus populate visible / occlusion_ratio."""
    
    raster_snap = next(c for c in token.coords if c.stage == "raster")
    raster_polygon = raster_snap.polygon

    # 1. raster → uv (trivial)
    raster_W, raster_H = inferred_from_token_or_passed_in
    uv_polygon = [(x / raster_W, y / raster_H) for x, y in raster_polygon]
    token.coords.append(CoordSnapshot(stage="uv", polygon=uv_polygon))

    # 2. uv → world (the hard part)
    uv_polygon_subdivided = subdivide_polygon(uv_polygon, segments=4)
    world_polygon_3d = [uv_to_world(uv, mesh) for uv in uv_polygon_subdivided]
    token.coords.append(CoordSnapshot(
        stage="world",
        polygon=[(p[0], p[1]) for p in world_polygon_3d],  # xy slice
        polygon_3d=world_polygon_3d,
    ))

    # 3. world → camera_2d
    camera_polygon = []
    for world_pt in world_polygon_3d:
        ndc = bpy_extras.object_utils.world_to_camera_view(
            scene, camera, mathutils.Vector(world_pt))
        if ndc.z < 0:  # behind camera
            continue
        px_x = ndc.x * render_size[0]
        px_y = (1.0 - ndc.y) * render_size[1]   # Y FLIP
        camera_polygon.append((px_x, px_y))
    
    if not camera_polygon:
        token.visible = False
        return token
    
    token.coords.append(CoordSnapshot(stage="camera_2d", polygon=camera_polygon))

    # 4. visibility + occlusion
    samples = sample_polygon_interior(camera_polygon, n=9)
    visible_count = 0
    for sample_px in samples:
        if not in_bounds(sample_px, render_size):
            continue
        visible_uv = uv_pass[int(sample_px[1]), int(sample_px[0])]
        # find this sample's expected uv from the uv-stage snapshot
        expected_uv = sample_polygon_uv(uv_polygon, sample_px, camera_polygon)
        if uv_distance(expected_uv, visible_uv) < 0.01:
            visible_count += 1
    token.occlusion_ratio = 1.0 - (visible_count / len(samples))
    token.visible = token.occlusion_ratio < 0.7

    # 5. camera_2d → camera_fx (v0.3 = identity; v1.0 applies lens distortion)
    fx_polygon = camera_polygon
    if distortion is not None:
        fx_polygon = apply_lens_distortion(camera_polygon, distortion)
    token.coords.append(CoordSnapshot(stage="camera_fx", polygon=fx_polygon))

    # 6. camera_fx → final_crop
    crop_x = (render_size[0] - output_size[0]) / 2
    crop_y = (render_size[1] - output_size[1]) / 2
    cropped_polygon = [(x - crop_x, y - crop_y) for x, y in fx_polygon]
    image_bounds = [(0, 0), (output_size[0], 0), (output_size[0], output_size[1]), (0, output_size[1])]
    final_polygon = sutherland_hodgman_clip(cropped_polygon, image_bounds)
    if not final_polygon:
        token.visible = False
    else:
        token.coords.append(CoordSnapshot(stage="final_crop", polygon=final_polygon))

    return token


# Helpers — each is its own ~50–150 LoC, with its own unit tests:
def subdivide_polygon(poly: list[tuple], segments: int) -> list[tuple]: ...
def uv_to_world(uv: tuple, mesh: bpy.types.Mesh) -> tuple[float, float, float]: ...
    # build UV-spatial-hash → triangle lookup; barycentric interpolation
def sample_polygon_interior(poly: list[tuple], n: int) -> list[tuple]: ...
def sutherland_hodgman_clip(subject: list[tuple], clip: list[tuple]) -> list[tuple]: ...
def apply_lens_distortion(poly: list[tuple], distortion: dict) -> list[tuple]: ...   # v1.0
```

---

## Done criteria for the design

This doc is "done" when:
- A new contributor can read it once and correctly implement `project_token_through_pipeline` without surprises
- The Y-flip is called out three times (it's the bug everyone hits)
- The barycentric-interpolation-on-curved-mesh detail is in the doc, not in some commit message later
- The visibility test's UV-pass-match strategy is specified with a numeric threshold
- The Sutherland-Hodgman requirement (vs naive min/max) is on the page

If any of these are missing on the next read, edit this doc before the next change to `bbox_projector.py`.
