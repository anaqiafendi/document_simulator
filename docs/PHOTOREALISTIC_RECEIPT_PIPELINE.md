# Photorealistic Receipt Photo Synthesis — Research & Build Plan

**Goal**: generate **photorealistic images of receipts that look like phone photos a real person would take**, each paired with a complete ground-truth label file (text content + bounding boxes that survive every transform in the pipeline). Photorealism is the product; **the GT-bundled dataset is the deliverable**.

**Scope split**: this plan covers dataset generation only. **Choosing or evaluating an OCR model — PaddleOCR vs Tesseract vs DocTR vs Donut vs LLM-based extractors — is a separate workstream once the dataset exists.** The ground-truth schema (§4) is format-agnostic and feeds any of them via thin adapter layers written later.

This document synthesizes findings from four parallel research agents (receipt content, lightweight 3D rendering, existing synthetic-document pipelines, UI + batch architecture) and two judge agents (skeptic + pragmatist builder). The raw pre-critique consolidation is at `PHOTOREALISTIC_RECEIPT_PIPELINE_RAW_RESEARCH.md` in this directory.

---

## 1. The Goal Reframe — Why It Matters

The original framing assumed "synthetic OCR training data." The skeptic agent argued — correctly, under that framing — that 2D perspective + shadow + warp tricks (kornia + Augraphy) get you ~90% of OCR augmentation value at ~5% of the engineering cost, and that 3D rendering is overkill for a CRNN that just learns glyph features.

**That argument no longer applies.** The clarified goal is photorealism — images a human inspector would believe are real phone photos. Photorealism requires:

- **True perspective from a held camera** — not a 4-corner warp; a real lens with focal length, sensor crop, and the slight barrel distortion of phone optics.
- **True contact shadows where the receipt meets the surface** — soft, blurred, multi-bounce. 2D `RandomShadow` produces a blob that doesn't track the paper geometry.
- **True specular highlights on semi-glossy thermal paper** — you can fake this in 2D, but only badly.
- **True depth-of-field falloff** — the part of the receipt closest to the camera is sharper than the part further away. A 2D blur can't do this without a depth map, and once you have a depth map you're already half-rendering in 3D.
- **Real environmental color cast** — light bouncing off a wood desk tints the bottom of the page warmer than the top. HDRI image-based lighting gives this for free.

So **3D rendering stays in the plan**. But every other criticism the judges raised survives the reframe and reshapes the architecture below — most importantly, **bbox tracking through every transform stage is now non-negotiable**, because without surviving GT the dataset is just pretty pictures.

---

## 2. Final Recommended Stack

Decisions, with confidence levels, after both critiques:

| Stage | Choice | Confidence | Why |
|---|---|---|---|
| **Receipt content** | `Faker` + lightweight Pydantic models. **Skip `polyfactory`** for v0.x — it's a third abstraction over Pydantic that earns its keep at scale, not at 10–100 receipts | High | Pragmatist said "no polyfactory yet" and they're right — Pydantic + Faker is enough for the first PR |
| **2D layout** | Jinja2 + HTML, **with `data-token-id` attributes on every text token** | High | Token IDs are how you survive the bbox-tracking chain (§4) |
| **2D rasterize** | **WeasyPrint** (default), pinned `>=60,<63` | High | Don't use Pillow's `ImageDraw` for v1 — receipts have variable wrap, multi-column items, line-height arithmetic that Pillow can't do |
| **Bbox extraction from rasterizer** | `weasyprint.Document.pages[i].text_lines` — true rendered glyph rects, **not** the input HTML coordinates | High | Critical detail from pragmatist; both 2D-only and 3D paths depend on this |
| **Fonts** | VT323 / Courier Prime / OCR-B (SIL-OFL) for thermal, plus **a sans-serif fallback** (Inter, OFL) for retail receipts. Visual-inspect each in sample renders | Medium | OCR-readability validation deferred to OCR-selection workstream; for dataset generation, visual fidelity is the criterion |
| **2D ink/paper degradation** | Existing **Augraphy** stack. Apply *post-3D* in 2D pixel space, **not pre-3D on the texture** | High | Reverses the original plan. Reasoning in §4 — Augraphy's non-affine warps don't return forward maps, so they break bbox tracking if applied before the 3D step |
| **Barcodes** | `python-barcode` + `qrcode` only | High | Skip `treepoem` — Ghostscript dep not worth it for receipts |
| **3D renderer (dev + v1.0)** | **Blender `bpy==4.2.0` (Eevee, Metal backend on Mac)** | High | Pragmatist verified arm64 wheel works; install: `uv add 'bpy==4.2.0' --extra rendering`. Skip BlenderProc — adds a layer that breaks debuggability and fights the NumPy<2 pin |
| **3D renderer (later, when NVIDIA available)** | PyTorch3D or Cycles+OptiX on a rented RTX 4090 | Medium | For 10k+ runs only, after v1.0 ships |
| **Paper meshes** | **Generate procedurally**, not Doc3D. ~20–30 parametric warps via `bmesh` (subdivision + Bezier curl + sparse fold lines, ~50 LoC) | High | Pragmatist showed Doc3D is 88GB total, ships `.mat` files (not OBJ), needs a converter, hosting is unreliable, and license is "research only." Treat Doc3D as a stretch goal, not a dependency |
| **Hand asset** | Sprite composite of a real hand cutout (CC0 from Pexels/Unsplash) | High | Lower friction than MANO/Mixamo. Skeptic's point: anatomical hand fidelity adds nothing photorealism users will notice as long as the hand casts a believable shadow on the receipt |
| **HDRI lighting** | **Poly Haven** (CC0, ~700 maps), bundle 30–50 indoor under `data/hdri/` | High | inv3d's hdrdb.com is dead. Poly Haven's API and license are both sane |
| **Camera FX** | 2D post-process via `kornia` + `Augraphy` post-phase. **Exception**: depth-of-field stays in the renderer using its depth pass | High | Both 2D-friendly perf and renderer-faithful DoF |
| **UI** | Streamlit page-per-stage, **`st.form` + "Render Preview" button** (not slider-on-change) | High | bpy at 512² is 300–800ms; rendering on every slider drag is unusable |
| **UI param forms** | `streamlit-pydantic` — generated from per-stage Pydantic configs | High | Single source of truth for UI + CLI |
| **3D preview** | Server-rendered PNG thumbnail from the actual `bpy` instance is canonical. Optional Three.js iframe is **debug aid only**, labeled "lighting preview — final may differ" | High | The single highest-leverage UX decision; renderer parity is non-negotiable |
| **Param sampling** | `scipy.stats.qmc.Sobol(scramble=True)` for continuous dims, plain categorical sampling for `background ∈ {office, café, kitchen}` | High | Conditional spaces handled hierarchically: sample background first, then per-branch Sobol |
| **Param spec / sweeps** | **Pydantic `ParamRange` models with a `.sample(rng)` method**. **Skip Hydra.** Use `itertools.product` over Pydantic configs for grid sweeps | High | Skeptic's point and it's airtight: Hydra + OmegaConf actively fights Pydantic v2 (two schema systems), and a single dev doesn't need Hydra's structured-config power |
| **Parallel exec (local)** | `concurrent.futures.ProcessPoolExecutor` with `mp_context="spawn"`, `initializer=load_renderer`, **`max_tasks_per_child=10`** | High | The `max_tasks_per_child` is critical — bpy can segfault under load and you must recycle workers |
| **Parallel exec (later)** | Ray Data only when going beyond one machine; otherwise overkill | Medium | |
| **Caching** | Two layers, not four: (1) `@st.cache_resource` for renderer/OCR singletons, (2) `diskcache.Cache` keyed on `hash(json.dumps(config.model_dump(), sort_keys=True))` for stage outputs. **Drop `joblib.Memory` and `cache_data`** | High | Skeptic's simplification — three of the four invalidation surfaces silently serve stale renders when Pydantic models gain fields |
| **Observability** | `rich.progress` + a SQLite (or Parquet) manifest with `pending` / `done` / `failed(reason)` states | High | Sufficient for 10k–100k runs |
| **Cloud burst** | RunPod RTX 4090 (~$0.34/hr) for path-traced production passes | Medium | Only after v1.0 ships locally |

---

## 3. Honest Throughput Numbers

The original synthesis claimed **~43k images/hr** on an M3 Max with an 8-worker `bpy` Eevee pool. **That number is wrong by an order of magnitude.** Skeptic's correction, which holds up to scrutiny:

- bpy worker cold-start: 3–8s per process loading bpy + scene `.blend` + meshes + HDRI
- Eevee on Metal does **not** cleanly parallelize across processes — they contend for one GPU context. Realistic concurrency is 2–4 effective workers, not 8
- Each worker eats 1.5–3 GB RSS with paper meshes loaded — at 6+ workers you OOM on a 36GB Mac running Streamlit + PaddleOCR
- Per-render scene reset (texture swap, camera reseed, light shuffle) is 200–600ms before the actual render call
- Add bbox projection (~50–150ms) and PNG encode (~80ms at 1024²)

**Realistic steady-state: 800ms–1.5s per image, ~3k–4k images/hour on an M3 Max.**

| Configuration | Realistic per-image | Realistic /hour |
|---|---|---|
| 2D-only, PIL composite | 50–200ms | 18k–72k |
| Cheap 3D (Eevee 512², 4 workers) | 400–800ms | 4.5k–9k |
| **Photoreal target (Eevee 1024², HDRI, depth-pass DoF, 4 workers)** | **800ms–1.5s** | **2.4k–4.5k** |
| Cycles low-sample, 1024², Apple Metal | 5–20s | 180–720 |
| Cycles production, 1024², RunPod 4090 | 1–4s | 900–3.6k |

10k photorealistic local images = **2–4 hours**. That's fine for v1.0. 100k = a weekend or a $5 cloud rental.

---

## 4. Ground Truth — The Core Deliverable

**This is the heart of the project, not a side artifact.** Every generated image must be paired with a ground-truth file recording (a) the receipt's text content, (b) per-token bounding boxes in the *final image's pixel space*, and (c) the **full coordinate trail** through every transform stage so debugging is tractable. If photorealism is the product, the GT-bundled dataset is the deliverable.

This is also the single most underestimated piece of the project. The original plan said the bbox projector was "~150 LoC." Both judges independently corrected this to **600–900 LoC plus 2–3 weeks of debugging**.

### 4.1 Schema (Pydantic)

```python
class CoordSnapshot(BaseModel):
    """One snapshot of a token's polygon at a specific pipeline stage."""
    stage: Literal[
        "html",         # DOM-declared coords from Jinja template
        "raster",       # WeasyPrint glyph rects (true rendered, NOT input)
        "uv",           # normalized [0,1]² UV space on the receipt plane
        "world",        # 3D world coords on the deformed paper mesh
        "camera_2d",    # projected to image pixels by virtual camera
        "camera_fx",    # after affine 2D camera FX (lens distortion etc)
        "final_crop",   # after final crop/resize to output resolution
    ]
    polygon: list[tuple[float, float]]                          # 4+ points
    polygon_3d: list[tuple[float, float, float]] | None = None  # only for stage="world"


class TokenGroundTruth(BaseModel):
    token_id: str                       # stable ID from data-token-id attribute
    text: str                           # transcription
    semantic_role: str | None = None    # "merchant_name", "line_item_qty", "total", ...
    coords: list[CoordSnapshot]         # the trail through all stages
    visible: bool = True                # false if occluded by hand or off-frame
    occlusion_ratio: float = 0.0        # 0.0 fully visible, 1.0 fully occluded

    @property
    def final_polygon(self) -> list[tuple[float, float]]:
        return self.coords[-1].polygon


class ImageGroundTruth(BaseModel):
    """Paired with each rendered image. Persisted as {image}.gt.json."""
    image_id: str
    image_path: Path                    # relative to dataset root
    image_size: tuple[int, int]         # (W, H) of final photo

    tokens: list[TokenGroundTruth]
    receipt: Receipt                    # the source synthetic content (full)

    seed: int                           # reproducibility
    pipeline_version: str               # bumped on any stage-output-affecting change
    scene_state: SceneState | None      # camera matrix, light positions, mesh deform params (3D only)
```

### 4.2 The transform chain — what gets recorded at each stage

| Stage | Coord space | How GT is computed | What can break |
|---|---|---|---|
| **HTML emit** | DOM px | Tag every text token with `data-token-id` (and optional `data-semantic`). Nothing else needed. | None if every token is tagged |
| **WeasyPrint raster** | image px | Walk `Document.pages[i].text_lines[j].text_boxes[k]` to get true rendered glyph rects. **Do not trust HTML coordinates.** | DPI mismatch, font fallback shifts glyph 1–4 px, line-height rounding |
| **UV mapping** | UV [0,1]² | Direct: `u = x_px / W`, `v = y_px / H` (flat unwrap of receipt plane assumed) | None if the unwrap is flat — verify the .blend file's UV is identity |
| **3D world (deformed mesh)** | (x,y,z) world | For each polygon corner, query the mesh's UV→world map via barycentric interpolation across the triangle containing that UV point | Sub-triangle interpolation must subdivide bbox edges before mapping (straight lines in UV become curved in world) |
| **Camera projection** | image px | `bpy_extras.object_utils.world_to_camera_view()` per polygon vertex. Convert NDC → pixels with render resolution. **Watch the Y-flip.** | Y-flip bugs, off-by-one at image edges |
| **Visibility / occlusion** | bool + ratio | Render UV pass + depth pass. For each token polygon, sample N points; count those whose visible-depth matches expected (no occluder closer to camera). | Per-pixel UV needed; tiny glyphs may span 5–20 px; subpixel UV interpolation essential |
| **Camera FX (lens distortion etc)** | image px | Affine ops via `kornia.geometry.transform_points`. Lens distortion is non-affine — needs `cv2.undistortPoints` per polygon vertex with the correct distortion coeffs. Pure 2D blur / noise / JPEG do not shift coords. | Forgetting to invert the distortion direction |
| **Final crop / resize** | image px (output) | Subtract crop origin; clip polygons to image bounds with **Sutherland-Hodgman** (not just min/max); mark `visible=False` on fully-clipped tokens | Polygons partially off-frame must be clipped properly or downstream consumers see invalid quads |

Each stage **appends** a `CoordSnapshot` to the token's `coords` list; the previous stage's snapshot is never overwritten. This is what makes debugging tractable — you can render any intermediate stage's polygons over the corresponding intermediate image and see *exactly* where a transform went wrong.

### 4.3 Why Augraphy applies *after* 3D, not before

Augraphy's geometric transforms (`Geometric`, `BadPhotoCopy`, ink-bleed) use `cv2.remap` internally with displacement maps that it does not return. Wrapping every transform with a coord-tracking shim is intractable. **Two options**:

1. Apply Augraphy *before* 3D, on the flat texture: ink-bleed "follows" paper curl naturally, but bbox tracking through the non-affine warp is impossible.
2. Apply Augraphy *after* 3D, in 2D pixel space (post-camera): bbox tracking stays affine via UV; the tradeoff is that ink-bleed sits on the *photographed* image rather than on the printed paper itself.

**We pick option 2.** For phone-photo realism this is actually more correct — phone photos *do* photograph already-degraded receipts; the camera doesn't degrade them in the act of photography. The "ink follows curl" loss is a small visual nit; the "bbox tracking impossible" loss is a project-killer.

### 4.4 On-disk format

```
data/synthetic/receipts_v1/
├── images/
│   ├── 00000001.png
│   ├── 00000002.png
│   └── ...
├── ground_truth/
│   ├── 00000001.gt.json    # full ImageGroundTruth dump
│   ├── 00000002.gt.json
│   └── ...
├── overlays/               # optional debug renders, .gitignored
│   └── 00000001.overlay.png
├── manifest.jsonl          # one line per image: {image_id, image_path, gt_path, n_tokens, generated_at, pipeline_version}
└── dataset.toml            # generation params, asset hashes, total counts
```

The per-image `.gt.json` is the source of truth. The manifest is a fast index for batch loaders. **Format adapters** (PaddleOCR `train.txt`, COCO JSON, custom) are written when an OCR consumer is selected — they read from the per-image files via `from_image_groundtruth(gt: ImageGroundTruth) -> str`. None of these adapters are part of the v0.x scope.

### 4.5 Validation gates (no OCR involved)

Without an OCR model in the loop, what proves the bboxes are correct?

1. **WeasyPrint API consistency test** *(automated)* — render a fixed-content receipt; assert every token's `raster`-stage polygon overlaps its DOM-declared rect within ±2 px (accounts for font hinting). Catches stage-1 regressions.
2. **Visual overlay tool** *(script + manual review)* — given any image + GT JSON, draw colored polygons back onto the image and save as `{image}.overlay.png`. Run on samples and eyeball. Non-automated but powerful.
3. **Pixel-content statistical test** *(automated, coarse)* — for each visible token polygon, sample 20 random pixels inside vs outside; assert `mean(inside) < mean(outside) - threshold` (dark text on lighter paper). Catches gross mis-projections (>10 px off) but won't catch sub-pixel drift.
4. **Round-trip fixture test** *(automated, tight)* — hand-craft one canonical (HTML, expected-GT-JSON) pair; assert pipeline output matches the fixture within tolerance. Highest fidelity but requires curating the fixture.
5. **Hash-stability regression** *(automated)* — same input + seed → byte-identical GT JSON. Catches accidental non-determinism.

For **v0.1** we ship #1 + #2 + #5. **#3** lands with v0.3 (3D rendering, where it matters most). **#4** lands when the fixture is worth the curation cost.

### 4.6 Design doc first

The bbox-projection chain through the deformed-mesh UV (§4.2 stages 3–5) is dense enough that **it deserves a one-page design doc with a hand-traced example end-to-end before any code is written**. Suggested location: `docs/coordinate-tracking-design.md`. Trace one specific token (e.g., the cents column of line 3) through every coord space with concrete numbers and a diagram. This is the cheapest possible insurance against discovering at 800 LoC into the projector that step 4 had a Y-flip you didn't notice.

---

## 5. Phased Build Plan

Anchored to the photorealism goal. Each phase ships a usable artifact.

### v0.1 — Tracer Bullet (1 weekend, no 3D, no Augraphy, no OCR)

**Goal**: prove the ground-truth chain works end-to-end for the simplest 2D-only case, and lock the on-disk schema everything else builds on.

Files:
- `src/document_simulator/synthesis/__init__.py`
- `src/document_simulator/synthesis/schema.py` — `Receipt`, `CoordSnapshot`, `TokenGroundTruth`, `ImageGroundTruth` Pydantic models per §4.1
- `src/document_simulator/synthesis/content.py` — one hardcoded `Receipt` factory (no Faker yet)
- `src/document_simulator/synthesis/render.py` — Jinja → WeasyPrint → `(PIL.Image, ImageGroundTruth)`. Walks `Document.pages[0].text_lines` to populate the `raster`-stage `CoordSnapshot` for every token
- `src/document_simulator/synthesis/persist.py` — writes `{image}.png`, `{image}.gt.json`, appends to `manifest.jsonl`, owns the on-disk layout from §4.4
- `src/document_simulator/synthesis/overlay.py` — `draw_overlay(image, gt) -> PIL.Image` for visual inspection (any stage selectable)
- `src/document_simulator/templates/receipts/thermal_minimal.html.j2` — single template, 5 fixed line items, every text token wrapped with `<span data-token-id="...">`
- `tests/unit/test_synthesis_schema.py` — round-trip serialization: `ImageGroundTruth.model_validate_json(gt.model_dump_json()) == gt`
- `tests/unit/test_synthesis_raster_bbox.py` — gate **#1** from §4.5: every token's `raster`-stage polygon overlaps its DOM-declared rect within ±2 px
- `tests/unit/test_synthesis_determinism.py` — gate **#5** from §4.5: same input + seed → byte-identical `gt.json`

Deps: `uv add 'weasyprint>=60,<63' 'jinja2>=3.1' --extra synthesis`

**The validation gate**: all three tests above pass, AND `python -m document_simulator.synthesis.overlay tests/fixtures/sample_receipt.png` produces a visually-correct annotated image (manual eyeball — gate **#2** from §4.5).

**If the WeasyPrint bbox test fails**, fix it before doing anything else. The entire 3D pipeline stacks on this stage producing trustworthy raster-space rects. **No OCR is involved at this stage** — correctness is verified structurally, not by round-tripping through a recognizer.

### v0.2 — Faker + Variety + Augraphy (1 weekend)

- Add `Faker` content generation, locale-aware tax rates, per-merchant SKU corpora under `data/sku_corpora/`
- Add 4 more templates (restaurant tip, retail multi-column, A4 invoice, taxi stub) — every token tagged with `data-token-id` and `data-semantic`
- `synthesis/manifest.py` — JSONL manifest writer with append + resume support
- Wire in **post-render** Augraphy 2D degradation (per §4.3 — Augraphy applies *after* the would-be-3D step, so for v0.2 it just applies after the raster step). Augraphy ops do not modify GT polygons (they're pixel-only at this stage).
- Add a Streamlit page (`ui/pages/06_receipt_synthesis.py`) showing 12 random samples in a grid with toggleable bbox overlay
- Validation gate: gates #1 + #5 from §4.5 across 100 random Faker-generated receipts; manual review of a 24-sample contact sheet (gate #2)

### v0.3 — Cheap 3D + the bbox projector (2–3 weekends, the hard one)

**Prerequisite**: write `docs/coordinate-tracking-design.md` per §4.6 *before* starting code.

- `uv add 'bpy==4.2.0' --extra rendering`
- One parameterized `.blend` template under `scenes/photo_v1.blend` with: subdivided plane (receipt), HDRI env (random per render), desk plane with PBR wood texture, sprite-composited hand prop
- `synthesis/scene_render.py` — loads `.blend`, swaps texture, randomizes HDRI/camera/curl, renders Eevee 1024² + UV pass + depth pass
- `synthesis/bbox_projector.py` — implements the §4.2 stages 3–7 chain (UV → world → camera_2d → visibility → camera_fx → final_crop). **Budget: 600–900 LoC, 1–2 weeks.** Each stage appends a `CoordSnapshot` to every token; nothing is overwritten.
- `synthesis/visibility.py` — UV-pass + depth-pass occlusion test populating `visible` and `occlusion_ratio`
- Streamlit page (`ui/pages/07_3d_scene.py`) with `st.form` + "Render Preview" button at 256² (~150ms), GT-overlay toggle, **and a stage selector that lets the dev visualize any intermediate `CoordSnapshot` overlaid on the corresponding intermediate render** (this is the debugging tool that justifies the coord-trail design)
- Sidecar bpy in `multiprocessing.Process` started at session start, communicates via `multiprocessing.Queue` — keeps Streamlit alive when bpy segfaults (~80 LoC)
- Validation gate: gates #1 + #2 + #3 + #5 from §4.5 across 50 3D-rendered samples. Gate **#3 (pixel-content statistical test)** is the moment of truth — if the projected polygons don't actually contain the rendered text pixels, the projector is wrong.

### v0.4 — Batch + Sampling (1 weekend)

- `synthesis/sampler.py` — Sobol over Pydantic `ParamRange` fields, hierarchical for conditional spaces
- `ProcessPoolExecutor` runner with `spawn`, `initializer=load_renderer`, `max_tasks_per_child=10`
- SQLite manifest with pending/done/failed states, resumable
- `rich.progress` for CLI; `st.progress` for Streamlit batch page
- Two-layer cache: `@st.cache_resource` for renderer, `diskcache.Cache` for stage outputs

### v1.0 — Photoreal Polish (1–2 weekends)

- Depth-pass DoF in Eevee
- Random motion blur via `kornia.augmentation.RandomMotionBlur`
- Per-render lens distortion with realistic phone-camera intrinsics (24mm equivalent, ~1–2% barrel)
- Auto-exposure / white balance jitter to match real phone HDR
- Contact-shadow plane under the receipt for grounded look
- Documentation page in Streamlit showing 32-sample contact sheet for qualitative review

### v1.1+ — Stretch (post-ship, evaluate need)

- Cloud burst recipe for RunPod RTX 4090 path-traced "gold" eval set (~500 images via Cycles)
- PyTorch3D port if you ever get a CUDA box and want differentiable end-to-end
- Doc3D mesh import (only if procedural meshes prove insufficient)
- RL environment coupling — extend `Synthetic3DEnv` action space to include 3D scene params (likely Phase 2 paper, not v1)

---

## 6. What to Skip Entirely (in this scope)

Both judges agreed on these. Cutting them now saves a week each:

- **OCR model selection / evaluation / fine-tuning** — explicitly a *separate workstream* that begins after the dataset exists. The GT schema in §4 is format-agnostic; thin adapter layers convert to PaddleOCR / Tesseract / DocTR / Donut / LLM-based extractors when an OCR target is chosen. Do not build an OCR baseline as part of this work.
- **OCR-format adapters** (PaddleOCR `train.txt`, COCO JSON) — written when an OCR consumer is selected. The dataset's source-of-truth is the per-image `gt.json`.
- **BlenderProc** — fights NumPy<2 pin, breaks debuggability, you don't need its randomization helpers (one stable scene template, many texture swaps)
- **Hydra** — Pydantic + `itertools.product` is enough; Hydra + OmegaConf actively fights Pydantic v2
- **`polyfactory`** — Pydantic + Faker is enough until you're past 10k samples
- **`joblib.Memory`** — silent staleness when Pydantic models gain fields
- **Streamlit `cache_data` for renders** — same problem; use `diskcache` instead
- **MANO hand model** — overkill; sprite composite is fine
- **Doc3D mesh dependency** — unreliable hosting, license risk, format conversion needed; generate procedural warps instead
- **PyTorch3D / Mitsuba 3 / Kaolin** for v1 — all assume CUDA; no benefit on Mac dev
- **Three.js / headless-gl as production renderer** — fragile, memory leaks, breaks renderer parity
- **Cycles for batch** — 30–120s/frame on Apple Silicon is a non-starter
- **The "publishable angle" framing** — scope inflation; if it happens it's a discovery, not a goal

---

## 7. Open Questions You Need to Decide

These are forks the research can't resolve — they require your judgment:

1. **Bbox alignment tolerance for the v0.1 raster-stage gate.** The proposed ±2 px tolerance is a guess that accounts for font hinting. Tighter (±1 px) catches subtle drift but may flag harmless rounding; looser (±5 px) may mask a real bug. **Action**: render one fixture, measure observed drift, then pick.

2. **Receipt language coverage.** Real phone-photo receipts in MY/SG/ID are bilingual (Bahasa + English, Mandarin in some). VT323/Courier Prime/OCR-B cover Latin only; CJK/jawi receipts need a font like Noto Sans Mono CJK (OFL). The renderer doesn't care, but the templates and SKU corpora need locale variants. **Action**: declare which locale(s) v1.0 must cover.

3. **`semantic_role` taxonomy.** The schema's `TokenGroundTruth.semantic_role` is `str | None`. Should it be a `Literal[...]` enum (CORD-style 42 classes), a free-form string, or a hierarchical taxonomy? Locking the enum early helps downstream consumers; leaving it free gives template authors flexibility. **Recommendation**: free-form string in v0.1, promote to enum in v1.0 once the actual vocabulary stabilizes.

4. **Pipeline versioning policy.** `ImageGroundTruth.pipeline_version` should bump on any stage change that affects output. What's "any" — git SHA? semver bumped manually? content-hash of the synthesis package? **Recommendation**: `synthesis-{semver}` bumped manually on stage logic changes; recorded in `dataset.toml` for the dataset run.

5. **Decoupled vs coupled with the existing RL loop.** The synthesis pipeline can either (a) write a static dataset that the existing `rl/environment.py` consumes unchanged (decoupled), or (b) extend the action space with 3D scene params (coupled, ~2× RL surface area). **Recommendation: decoupled for v1.0**, coupled is a later question.

6. **Commercial vs research use.** Doc3D and (parts of) MANO are research-only licenses. Procedural meshes + sprite-composited public-domain hand photos sidestep this entirely. If commercial use is on the roadmap, lock in CC0/MIT-only assets from day 1.

7. **Manifest format**: SQLite vs JSONL vs Parquet. JSONL is the simplest (append-only, human-readable, streamable); SQLite gives you transactional state for the pending/done/failed manifest in §4.4 but adds a file format. **Recommendation**: JSONL for the dataset manifest; SQLite for the in-flight batch-job state in v0.4.

---

## 8. Sources

Full research agent reports are in the conversation transcript. Key citations:

**Closest published precedent**
- Inv3D (KIT, IJDAR 2023) — synthetic invoices in 3D with smartphone-photo test set: https://link.springer.com/article/10.1007/s10032-023-00434-x | https://github.com/FelixHertlein/inv3d-generator
- Doc3D / DewarpNet (ICCV 2019) — paper-mesh rendering pipeline: https://github.com/cvlab-stonybrook/doc3D-dataset

**Receipt content + 2D rendering**
- Faker: https://github.com/joke2k/faker
- WeasyPrint: https://weasyprint.org/
- Genalog (MIT, HTML→PNG reference impl): https://github.com/microsoft/genalog
- VT323 (OFL): https://www.fontsquirrel.com/license/vt323

**3D rendering**
- bpy on PyPI: https://pypi.org/project/bpy/
- Blender Metal GPU on Apple Silicon: https://docs.blender.org/manual/en/latest/render/cycles/gpu_rendering.html
- Poly Haven HDRIs (CC0): https://polyhaven.com/hdris
- Kornia augmentation: https://kornia.readthedocs.io/en/latest/augmentation.html

**UI + batch**
- Streamlit caching: https://docs.streamlit.io/develop/concepts/architecture/caching
- streamlit-pydantic: https://github.com/lukasmasuch/streamlit-pydantic
- scipy.stats.qmc: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.qmc.Sobol.html
- diskcache: https://grantjenks.com/docs/diskcache/

**Cloud burst**
- RunPod (RTX 4090 ~$0.34/hr Mar 2026): https://www.runpod.io/

---

## 9. Next Action

If you agree with this plan, the **first PR** is the v0.1 tracer bullet in §5:

- 7 new files in `src/document_simulator/synthesis/` (`__init__`, `schema`, `content`, `render`, `persist`, `overlay`, plus templates dir)
- 1 new template under `templates/receipts/thermal_minimal.html.j2`
- 3 unit tests: schema round-trip, raster-stage bbox alignment (±2 px), determinism
- 2 new optional deps (`weasyprint`, `jinja2`) under a new `synthesis` extra
- **No OCR. No 3D. No Augraphy.** Just: synthetic receipt → rendered PNG → bundled `gt.json` → manifest entry → visual overlay tool.

Roughly 350–400 LoC, ships in one evening to one weekend. If the raster-stage bbox test passes, the foundation for everything else is locked. If it fails, fix the WeasyPrint `Document.pages[i].text_lines` walk before doing anything else.

**Before starting v0.3 (3D + bbox projector)**: write `docs/coordinate-tracking-design.md` per §4.6. Trace one specific token through every CoordSnapshot stage with concrete numbers and a diagram. This is the single highest-leverage hour you can spend on the whole project.
