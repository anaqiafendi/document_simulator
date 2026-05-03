# Feature: Receipt Synthesis — 3D Scene + Bbox Projector (v0.3)

> **GitHub Issue:** `TBD`
> **Status:** `in-progress`
> **Module:** `document_simulator.synthesis.receipts.scene` + `document_simulator.synthesis.receipts.bbox_projector` + `webapp/.../ReceiptSynthesis` (3D card activation)

---

## Summary

Phase v0.3 of the photoreal receipt synthesis pipeline. Adds **3D scene rendering** (programmatic Blender scene via `bpy==4.2.0`, procedural paper mesh, HDRI lighting), the **bbox projector** through `uv → world → camera_2d → visibility → camera_fx → final_crop` chain (the engineering crux from plan §4 — 600–900 LoC budget), and **activates the 3D card** in the React UI with HDRI picker + stage selector.

**Sub-phase delivery** — 4 sequential PRs against this single FDD:

- **v0.3a** — bpy install + Dockerfile + programmatic scene + procedural mesh + Eevee render (no GT projection yet); proves the rendering pipeline runs on both HF and local
- **v0.3b** — bbox projector through `uv → world → camera_2d` per `docs/coordinate-tracking-design.md`
- **v0.3c** — visibility test (UV pass + depth pass) + `camera_fx` identity stage + `final_crop` with Sutherland-Hodgman
- **v0.3d** — React UI: 3D card activates, HDRI picker, stage selector for any CoordSnapshot

Each sub-phase is independently shippable and tests-green.

**Out of scope** (deferred): batch generation (v0.4), photoreal camera FX (lens distortion, motion blur, DoF — v1.0), Doc3D meshes (procedural is sufficient).

---

## Motivation

### Problem Statement

v0.2 ships realistic 2D receipts with bbox GT but no real perspective, real shadows, or real depth-of-field. Phone photos of real receipts have all of those. Without 3D rendering, the dataset doesn't actually achieve the photorealism goal stated in `docs/PHOTOREALISTIC_RECEIPT_PIPELINE.md` §1.

The bbox-projection chain through a curved 3D mesh is the project's biggest engineering risk per both judge agents (plan §4). The coordinate-tracking design doc (`docs/coordinate-tracking-design.md`) is a v0.3 prereq — already committed (a7970f0).

### Value Delivered

- Phone-photo-quality renders: real perspective + real soft shadows + HDRI bounce light + slight surface curl on the receipt
- GT polygons survive the 3D transform — verified by the pixel-content statistical test (gate #3 from plan §4.5)
- Stage-selector UX in the React inspector: visualize any intermediate `CoordSnapshot` overlaid on its corresponding intermediate render — the debug tool that justifies the append-only coords design
- HF-compatible deploy: single FastAPI app, same React tab, env-var resolution to handle CPU-only HF vs local M-series

---

## User Stories

| Role | Goal | So That |
|------|------|---------|
| Pipeline developer | I switch from Augraphy to 3D Scene in the React UI | I see the receipt rendered as a phone photo with real perspective and shadows |
| Pipeline developer | I pick a different HDRI from the thumbnail picker | The lighting changes meaningfully and bbox polygons stay aligned |
| Pipeline developer | I pick a stage (e.g. "world", "camera_2d") in the inspector dropdown | I see that intermediate stage's polygons over the corresponding intermediate image — for debugging the projector |
| Reviewer (HF Spaces) | I open the deployed app's Receipt Synthesis tab | The 3D card works (just slower than local — 5–15s render) |
| Pipeline developer | The bpy worker process crashes mid-render | The FastAPI app stays up, the user sees an error banner, the worker is recycled |

---

## Acceptance Criteria

All criteria must be verifiable by an automated test, a manual reproducible step, or the integration smoke check.

### v0.3a — bpy install + scene + Eevee render

- [ ] AC-1a: `Dockerfile` adds bpy system libs (`libxrender1 libxi6 libxxf86vm1 libxfixes3 libgl1 libgomp1 libegl1 libglib2.0-0`)
- [ ] AC-2a: `pyproject.toml` adds `synthesis-3d = ["bpy==4.2.0"]` extra
- [ ] AC-3a: CI step `import bpy` succeeds in the HF Spaces Docker image
- [ ] AC-4a: `synthesis.receipts.scene.build_scene(seed: int) -> bpy.types.Scene` programmatically constructs a scene: subdivided plane (~50×80 verts), camera at top-down 30–45° angle, sun light + HDRI environment from `data/hdri/`
- [ ] AC-5a: `synthesis.receipts.scene.deform_paper(mesh, curl_strength: float = 0.1, fold_count: int = 0)` applies procedural curl + sparse fold lines via `bmesh`
- [ ] AC-6a: `synthesis.receipts.scene.render_eevee(scene, resolution: tuple[int, int]) -> tuple[PIL.Image, np.ndarray, np.ndarray]` returns (rendered RGB image, UV pass `(H, W, 2)` float, depth pass `(H, W)` float)
- [ ] AC-7a: 3 small CC0 HDRIs bundled in `data/hdri/` (e.g. `office_warm.hdr`, `kitchen_bright.hdr`, `outdoor_overcast.hdr`)
- [ ] AC-8a: All v0.3a tests pass: `pytest tests/synthesis/receipts/test_scene*.py`

### v0.3b — bbox projector (uv → world → camera_2d)

- [ ] AC-1b: `synthesis.receipts.bbox_projector.uv_to_world(uv, mesh) -> tuple[float, float, float]` performs barycentric interpolation across the mesh triangle containing `uv`, with UV-spatial-hash for O(1) lookup. Handles UV seams via clamping.
- [ ] AC-2b: `subdivide_polygon(polygon, segments=4)` adds intermediate points along edges so bboxes follow surface curvature, not just corner-to-corner
- [ ] AC-3b: `world_to_camera_2d(world_pt, scene, camera, render_size)` wraps `bpy_extras.object_utils.world_to_camera_view`, applies the Y-flip per coord-tracking design doc §3
- [ ] AC-4b: `project_token(token, mesh, scene, camera, render_size)` appends `uv`, `world` (with `polygon_3d`), and `camera_2d` `CoordSnapshot`s in order
- [ ] AC-5b: Round-trip identity test: with mesh deformation = 0, camera straight-down, output_size == raster_size, projected `camera_2d.polygon == raster.polygon` within ±2 px (from coord-tracking design §Validation)
- [ ] AC-6b: All v0.3b tests pass

### v0.3c — visibility + camera_fx + final_crop

- [ ] AC-1c: `synthesis.receipts.bbox_projector.compute_visibility(token, uv_pass, depth_pass, render_size)` samples 9 points per polygon, populates `token.visible` and `token.occlusion_ratio` per coord-tracking design §4
- [ ] AC-2c: `camera_fx` stage in v0.3 is identity (`camera_fx.polygon == camera_2d.polygon`) — non-trivial FX deferred to v1.0
- [ ] AC-3c: `final_crop` uses `sutherland_hodgman_clip(polygon, image_bounds)` (NOT naive min/max). Tokens fully off-frame get `visible=False`.
- [ ] AC-4c: Pixel-content statistical test (gate #3 from plan §4.5): for each visible token's `final_crop` polygon, `mean(pixels_inside) < mean(pixels_outside) - 30` (8-bit grayscale, accounts for dark text on lighter paper)
- [ ] AC-5c: All v0.3c tests pass

### v0.3d — React UI activation

- [ ] AC-1d: 3D Scene card in the stage strip is **active** (no longer disabled placeholder); clicking it opens the inspector with the 3D rendered image
- [ ] AC-2d: New `HDRIPicker` component in `webapp/src/components/receipt-synthesis/`: thumbnail grid backed by `GET /api/receipt-synthesis/hdri-thumbnails`. Clicking selects an HDRI; the choice is added to `ReceiptRenderRequest`.
- [ ] AC-3d: Stage selector dropdown in `StageInspector` lets the user choose which `CoordSnapshot` stage's polygons to overlay on the 3D image (`raster` / `uv` / `world` / `camera_2d` / `camera_fx` / `final_crop`). Selecting `world` shows the polygon's xy projection.
- [ ] AC-4d: `useReceiptSynthesis` hook handles the longer 3D render times (5–15s on HF, 1–2s local) with a visible spinner; render-button stays disabled during the call.
- [ ] AC-5d: New backend endpoint `GET /api/receipt-synthesis/hdri-thumbnails` returns `{hdris: [{id, name, thumbnail_b64}]}`. Thumbnails are pre-computed at module import (or lazy-cached after first request).
- [ ] AC-6d: `webapp` build (`npm run build`) clean.

### Integration

- [ ] AC-final: Manual demo per `/tmp/demo_script_v03.md`: starting both servers, clicking through to the 3D card, picking an HDRI, hitting Render Preview yields a rendered phone-photo with bbox polygons aligned to text on the curved paper.

### Sidecar / Robustness

- [ ] AC-sidecar: bpy renders happen in a `multiprocessing.Process` started at FastAPI startup. Worker crash returns a 503 to the client; FastAPI keeps running; worker is recycled on next request. (Per plan §v0.3 — ~80 LoC.)

---

## Design

### Public API (Python)

```python
from document_simulator.synthesis.receipts.scene import build_scene, deform_paper, render_eevee
from document_simulator.synthesis.receipts.bbox_projector import project_token

scene = build_scene(seed=42, hdri_id="office_warm")
deform_paper(scene.objects["receipt"].data, curl_strength=0.1, fold_count=1)
image, uv_pass, depth_pass = render_eevee(scene, resolution=(1024, 1024))

for token in gt.tokens:
    project_token(
        token, mesh=scene.objects["receipt"].data, scene=scene,
        camera=scene.camera, uv_pass=uv_pass, depth_pass=depth_pass,
        render_size=(1024, 1024), output_size=(1024, 1024),
    )
```

### Public API (HTTP)

```http
POST /api/receipt-synthesis/render
{
  "template": "restaurant_tip",
  "seed": 99,
  "augraphy_preset": "medium",
  "render_3d": true,            # NEW in v0.3
  "hdri_id": "office_warm",     # NEW in v0.3, ignored if render_3d=false
  "curl_strength": 0.1          # NEW in v0.3
}
→ 200 ReceiptRenderResponse with stages: ["content", "raster", "augraphy", "3d_render"]
   (camera_fx and final_crop snapshots populated on the GT tokens; not separate stages)

GET /api/receipt-synthesis/hdri-thumbnails    # NEW in v0.3d
→ 200 { "hdris": [{id, name, thumbnail_b64}] }
```

### Data Flow

```
v0.2 pipeline (content → raster → augraphy)
    ↓ degraded receipt PIL.Image
build_scene + deform_paper                                 ← v0.3a
    ↓ bpy.types.Scene with receipt as UV-mapped texture
render_eevee → (image, uv_pass, depth_pass)                ← v0.3a
    ↓
project_token per token in gt.tokens                       ← v0.3b, v0.3c
  appends uv → world → camera_2d → camera_fx → final_crop
  populates visible / occlusion_ratio
    ↓
ReceiptRenderResponse.stages.append(StageOutput(stage="3d_render", image_b64=...))
    ↓
React StageInspector with stage selector dropdown          ← v0.3d
```

### Key Architectural Decisions

1. **HF-compatible single app, no split** — per plan §3.5. Same FastAPI process, same Docker image, env vars control resolution + asset count. Future cloud-GPU upgrade is a config flip, not a refactor.
2. **Programmatic `.blend` (no checked-in binary)** — `build_scene()` constructs the scene at runtime via the bpy Python API. Reasons: reproducibility (scene-graph diffs are reviewable as code), no binary file in git, no Blender desktop needed for contributors, easier to parameterize.
3. **Procedural paper meshes (no Doc3D)** — per plan §2 stack table. ~50 LoC of `bmesh` does subdivision + Bezier curl + sparse fold. Doc3D is 88GB, ships .mat files, license is research-only — not worth the dependency.
4. **Sidecar bpy via `multiprocessing.Process`** — bpy can segfault under load (per pragmatist judge). Worker pool of size 1 (HF) or 2–4 (local), `max_tasks_per_child=10` to recycle. Keeps FastAPI resilient.
5. **UV-spatial-hash for `uv_to_world`** — naive per-token linear scan over 8000 triangles is O(N×M). With 30 tokens per receipt × 8000 triangles = 240k checks per render. Spatial hash on UV grid (e.g. 64×64 cells) cuts this to ~30 lookups. ~50 LoC, big win.
6. **Subdivide bbox edges before projection** — straight UV line becomes curved on a deformed mesh. Subdividing each edge into 4 segments before projection captures curvature; output polygon has up to 16 vertices instead of 4. Downstream consumers (the bbox overlay, future OCR adapters) handle non-quad polygons.
7. **Stage selector in React inspector** — the debug tool that justifies the entire append-only coords design from FDD #27. Without this UI, the coords trail is dead weight in the JSON. With it, debugging a misprojected polygon takes seconds (visualize each stage in turn) instead of hours (write a one-off script per debug session).
8. **Camera FX is identity in v0.3** — non-trivial FX (lens distortion, DoF, motion blur) all defer to v1.0. The `camera_fx` snapshot is populated for schema consistency so v1.0 only changes one function.
9. **HDRI thumbnails generated at build time** — saved as 128×128 PNGs alongside the .hdr files. The `/hdri-thumbnails` endpoint just lists files. No runtime conversion cost.

### Known Edge Cases & Constraints

- **bpy on HF Spaces**: requires Linux x86_64 wheel (~600MB) + system libs. If the wheel install fails on the HF builder, fall back to writing a "renderer service URL" abstraction (the architecture I floated and rejected — but the rejection is conditional on bpy actually installing on HF).
- **CPU-only Eevee on HF**: ~5–15s per 384² render. Acceptable for POC; worth surfacing in the UI as "rendering on shared CPU, this takes ~10s".
- **HDRI count vs Docker image size**: bundle 3 small (~5MB each) HDRIs to keep image lean. Local users can drop more `.hdr` files into `data/hdri/` and they auto-populate the picker.
- **Procedural mesh non-determinism**: `bmesh.ops.subdivide` and Bezier curl ops must be seeded reproducibly. Use the receipt's seed.
- **macOS DYLD env var** (from v0.1 + v0.2) persists.

---

## Implementation

### Files (cumulative across sub-phases)

| Path | Sub-phase | Role |
|------|-----------|------|
| `Dockerfile` | v0.3a | Add bpy system libs |
| `.github/workflows/*.yml` | v0.3a | Add `import bpy` smoke step in CI |
| `pyproject.toml` | v0.3a | Add `synthesis-3d` extra (`bpy==4.2.0`) |
| `src/document_simulator/synthesis/receipts/scene/__init__.py` | v0.3a | Public exports |
| `src/document_simulator/synthesis/receipts/scene/builder.py` | v0.3a | `build_scene(seed, hdri_id)` |
| `src/document_simulator/synthesis/receipts/scene/mesh.py` | v0.3a | `deform_paper(mesh, curl, folds)` |
| `src/document_simulator/synthesis/receipts/scene/render.py` | v0.3a | `render_eevee(scene, resolution)` returns RGB+UV+depth |
| `src/document_simulator/synthesis/receipts/scene/sidecar.py` | v0.3a | `multiprocessing.Process` bpy worker + queue interface |
| `data/hdri/office_warm.hdr` + 2 more | v0.3a | CC0 HDRIs from Poly Haven |
| `data/hdri/*.thumbnail.png` | v0.3a | Pre-computed 128² PNGs |
| `src/document_simulator/synthesis/receipts/bbox_projector/__init__.py` | v0.3b | Public exports |
| `src/document_simulator/synthesis/receipts/bbox_projector/uv_to_world.py` | v0.3b | Spatial hash + barycentric |
| `src/document_simulator/synthesis/receipts/bbox_projector/world_to_camera.py` | v0.3b | bpy_extras + Y-flip |
| `src/document_simulator/synthesis/receipts/bbox_projector/projector.py` | v0.3b | `project_token` orchestrator |
| `src/document_simulator/synthesis/receipts/bbox_projector/visibility.py` | v0.3c | UV-pass + depth-pass occlusion |
| `src/document_simulator/synthesis/receipts/bbox_projector/clip.py` | v0.3c | Sutherland-Hodgman polygon clipping |
| `src/document_simulator/synthesis/receipts/bbox_projector/subdivide.py` | v0.3b | Polygon edge subdivision |
| `src/document_simulator/api/routers/receipt_synthesis.py` | v0.3a + v0.3d | Extend with `render_3d` flag, add `/hdri-thumbnails` |
| `src/document_simulator/api/models.py` | v0.3a | Extend `ReceiptRenderRequest` with `render_3d`, `hdri_id`, `curl_strength` |
| `webapp/src/components/receipt-synthesis/HDRIPicker.tsx` | v0.3d | Thumbnail grid |
| `webapp/src/components/receipt-synthesis/StageSelector.tsx` | v0.3d | Dropdown for which CoordSnapshot to overlay |
| `webapp/src/components/receipt-synthesis/PipelineStageCard.tsx` | v0.3d | Remove disabled state from 3D card |
| `webapp/src/components/receipt-synthesis/StageInspector.tsx` | v0.3d | Wire stage selector + 3D card-specific UI |
| `webapp/src/api/client.ts` | v0.3d | Add `listHdriThumbnails` |
| `webapp/src/types/index.ts` | v0.3d | Add HDRI types, extend ReceiptRenderRequest |
| `tests/synthesis/receipts/test_scene_*.py` | v0.3a | Scene + mesh + render tests |
| `tests/synthesis/receipts/test_bbox_projector_*.py` | v0.3b/c | Projector tests |
| `tests/api/routers/test_receipt_synthesis.py` | v0.3a/d | Extend with 3D-flag + hdri-thumbnails tests |

### TDD Cycle Summary (per sub-phase)

Each sub-phase ships its own Red→Green→Refactor cycle. The orchestrator's coding agents do this; the FDD's signoff section gets updated with results per sub-phase as PRs land.

### How to Run

```bash
# Install (after v0.3a lands)
uv sync --extra synthesis --extra synthesis-3d --native-tls

# macOS — system libs from v0.1
brew install pango cairo
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib

# Tests
uv run pytest tests/synthesis/receipts/ -q --no-cov

# Local dev
make dev   # starts uvicorn + npm run dev concurrently
open http://localhost:5173/receipt-synthesis
```

---

## Dependencies

### Requires

| Dependency | Kind | Why |
|------------|------|-----|
| `synthesis.receipts.*` (FDD #27, #28) | internal | Schema, render, content, augraphy_pretreat |
| `bpy==4.2.0` | external (new `synthesis-3d` extra) | Headless Blender for 3D scene + render |
| `numpy<2.0` | external (already core) | UV pass / depth pass arrays |
| `pillow>=10.2.0` | external (already core) | Image I/O |
| Linux system libs (`libxrender1` etc) | external (Dockerfile) | bpy headless rendering |
| 3 CC0 HDRIs from Poly Haven | external (bundled in `data/hdri/`) | Lighting variety |

### Required By

| Consumer | How it uses this feature |
|----------|------------------------|
| v0.4 (batch) | `ProcessPoolExecutor` workers each call `render_3d=True` end-to-end |
| v1.0 (camera FX) | Replaces the identity `camera_fx` stage with lens distortion / DoF / motion blur |

---

## Future Work

- [ ] **v1.0** camera FX: lens distortion (`cv2.projectPoints` with intrinsics), DoF (depth-pass blur), motion blur (kornia), JPEG quality jitter, contact-shadow plane
- [ ] **v0.4** batch generation with Sobol sampling over (template, hdri, curl_strength, etc.)
- [ ] HF Spaces GPU tier upgrade — config-only, no code change
- [ ] Cloud GPU burst via Modal/RunPod — `RENDERER_SERVICE_URL` env var indirection
- [ ] More HDRIs (full Poly Haven library, lazy-loaded from S3 or similar)
- [ ] Hand mesh prop (currently the receipt sits on a desk plane with no occluder)
- [ ] Doc3D mesh import (only if procedural meshes prove insufficient — they likely won't)

---

## References

- [Plan: Photorealistic Receipt Photo Synthesis §3.5 (deployment), §4 (GT)](../PHOTOREALISTIC_RECEIPT_PIPELINE.md)
- [Coordinate Tracking Design](../coordinate-tracking-design.md) — hand-traced worked example, Y-flip warnings, implementation skeleton
- [UI Exposure Design](../PHOTOREAL_RECEIPT_UI_DESIGN.md) — stage selector spec, HDRI picker spec
- [FDD #27 (v0.1)](feature_photoreal_receipt_synthesis.md), [FDD #28 (v0.2)](feature_receipt_synthesis_react_ui.md) — what this builds on
- [bpy on PyPI](https://pypi.org/project/bpy/) — Linux x86_64 + macOS arm64 wheels
- [Poly Haven HDRIs](https://polyhaven.com/hdris) — CC0 lighting library
