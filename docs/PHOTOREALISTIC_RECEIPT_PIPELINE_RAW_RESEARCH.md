# Synthetic Receipt Photo Pipeline — Consolidated Research Findings (Pre-Critique Draft)

> Compiled from 4 parallel research agents covering: receipt content/2D rendering, lightweight 3D rendering, existing synthetic-document pipelines, UI + batch architecture. To be critiqued by judge agents before final synthesis.

## The Idea

Six-stage pipeline:
1. **Generate fake receipt content** (Faker-style data, line items, totals)
2. **Render to 2D image/PDF** with realistic print textures
3. **Place on paper mesh in randomized 3D scene** (hand, desk, background)
4. **Lighting + shadows** simulation
5. **Virtual camera screenshot** with camera artifacts
6. **Feed into existing PaddleOCR + Augraphy + SB3 RL pipeline**

Existing project: Python 3.11, uv, Streamlit UI, Augraphy, PaddleOCR, Stable-Baselines3 (`document_simulator/`).

---

## Recommended Stack (Convergent)

| Stage | Recommendation | Confidence | Notes |
|---|---|---|---|
| **Content gen** | `Faker` + `polyfactory` (Pydantic-driven) | High | `mimesis` only if >10k/sec needed |
| **2D layout** | `Jinja2` + HTML/CSS templates | High | One template per receipt class (thermal, restaurant, retail, A4 invoice) |
| **2D rasterize** | `WeasyPrint` (default), `Pillow` fast-path | High | Genalog (MIT) is reference impl — borrow templating |
| **Barcodes** | `python-barcode` + `qrcode` | High | `treepoem` only for exotic symbologies |
| **Fonts** | VT323, Courier Prime, OCR-B (SIL-OFL) | High | Bundle in `data/fonts/` |
| **2D degradation** | Keep existing **Augraphy** | High | Apply *before* 3D step, on the texture |
| **3D renderer (dev)** | **Blender `bpy` 4.x (Eevee)** | High | Apple Silicon Metal works; pip-installable on Py 3.11 |
| **3D renderer (prod)** | PyTorch3D on NVIDIA box (later) | Medium | Batched tensor render, 10× throughput |
| **3D renderer (gold eval)** | Mitsuba 3, ~500 frames | Medium | Validate cheap-renderer domain gap doesn't break OCR |
| **Paper meshes** | Borrow **Doc3D** OBJ library | High | 100k pre-captured warps; research license |
| **Hand asset** | Sprite composite OR Mixamo rigged | Medium | MANO is overkill for OCR augmentation |
| **HDRI lighting** | Poly Haven (CC0, ~700 maps) | High | inv3d's hdrdb.com source is dead — use Poly Haven |
| **Camera FX** | 2D post-process via `kornia` + Augraphy | High | Exception: depth-aware DoF stays in renderer |
| **UI** | Streamlit page-per-stage, tabs inside | High | Already in stack, tested |
| **UI param forms** | `streamlit-pydantic` from per-stage Pydantic configs | High | Single source of truth for UI + CLI sweeps |
| **3D preview** | Server-rendered PNG thumbnail (canonical) + optional Three.js iframe (debug aid) | High | **Renderer parity is the highest-leverage decision** |
| **Param sampling** | `scipy.stats.qmc.Sobol(scramble=True)` | High | Beats uniform sampling for variety |
| **Param spec** | **Hydra** structured configs + `--multirun` | Medium | Single declaration of param space for UI + CLI |
| **Parallel exec (local)** | `concurrent.futures.ProcessPoolExecutor` w/ `spawn` + `initializer=load_renderer` | High | macOS quirk: `fork` deadlocks with native libs |
| **Parallel exec (scale)** | **Ray Data** when fanning out across machines | Medium | Or sustained 10k+ batches |
| **Caching** | `cache_resource` (renderer/OCR), `cache_data` (stage outputs), `joblib.Memory` (render_scene), `diskcache` (KV) | High | Four-layer but each has a clear job |
| **Observability** | `rich.progress` + Parquet timing log + 3-state manifest (pending/done/failed) | High | "Where's the bottleneck" becomes a one-liner |
| **Cloud burst** | RunPod RTX 4090 (~$0.34/hr) or Modal serverless | Medium | Local for tuning; cloud for production passes |

---

## Throughput Targets (M3 Max class)

| Pipeline config | Per-image | Images/hr |
|---|---|---|
| 2D only (PIL composite, no 3D) | 50–200ms | 18k–72k |
| Rasterized 3D (PyTorch3D Metal, 512²) | 200–600ms | 6k–18k |
| Blender Eevee, 1024² | 1–3s | 1.2k–3.6k |
| Blender Eevee, 8 worker pool | ~80ms | ~43k |
| Cycles low-sample, 1024² | 5–20s | 180–720 |
| Cycles production, 1024² | 30–120s | 30–120 |

**10k images:** 1–3hr local rasterized; 80–300hr local path-traced → rent cloud.

---

## Open Tension: BlenderProc vs Raw `bpy`

- **Agent 1 (existing pipelines)** recommends wrapping **BlenderProc** (DLR, GPL-3.0, pip-installable, mature, ML-focused). Argues GPL-3 is fine for synthetic-data use, gives camera/lighting/output infra free, ~1000–1500 LoC of glue.
- **Agent 3 (3D rendering)** recommends **raw `bpy`** as a Python module. Argues `bpy` 4.x has good Apple Silicon support, gives full control, lower dependency footprint.

**Question for judges:** Which is right for this project? BlenderProc adds a layer but provides RGB+depth+normals+segmentation and randomization helpers. Raw `bpy` is tighter but you re-implement scene setup boilerplate.

---

## What's Genuinely New (Publishable Angle)

- No open-source synthetic *receipt* generator does 3D scene simulation. Inv3D (KIT, IJDAR 2023) is the closest precedent — 25k synthetic invoices in 3D, but invoices ≠ receipts (different aspect ratio, layouts, thermal artifacts).
- The "synthetic receipt → 3D phone photo → PaddleOCR finetune" loop doesn't exist as an open package.
- ~1000–1500 LoC of new Python + a parameterized `.blend` scene template covers the gap.

---

## Architecture Sketch

```
src/document_simulator/
  synthesis/
    content.py              # Pydantic Receipt + polyfactory ReceiptFactory
    catalog.py              # SKU corpora by merchant category
    render.py               # Jinja → WeasyPrint → PIL.Image
    barcodes.py             # python-barcode + qrcode wrappers
    augraphy_pretreat.py    # apply existing 2D degradation to texture
    scene_render.py         # bpy/BlenderProc scene loader + render
    bbox_projector.py       # UV → world → camera bbox math (HARD PART)
    camera_post.py          # kornia + Augraphy post-render FX
    sampler.py              # Sobol sampler over Pydantic ParamRange
  templates/receipts/       # Jinja2: thermal_single.html, restaurant_tip.html, ...
  data/fonts/               # VT323, Courier Prime, OCR-B
  data/sku_corpora/         # grocery.json, restaurant.json, fuel.json
  data/meshes/              # Doc3D paper warps
  data/hdri/                # Poly Haven environments
  scenes/                   # parametrized .blend files
ui/pages/
  06_receipt_synthesis.py   # content + 2D render preview
  07_3d_scene.py            # scene config + thumbnail
  08_camera_fx.py           # post-process preview
  09_batch_runner.py        # Hydra sweep + Ray/PPE execution
```

---

## Key Risks to Probe

1. **Renderer parity:** Three.js preview ≠ Blender batch. Users tune live, batch produces something different. Mitigation: server-rendered PNG is canonical preview.
2. **Bounding-box ground truth through 3D transform:** Non-trivial — UV → world → camera projection needs to track text bboxes from flat receipt to final photo. Doc3D's UV approach is the reference.
3. **Apple Silicon GPU rendering:** Blender Cycles on Metal exists but is ~5–10× slower than CUDA. Path-traced production passes will need cloud GPU.
4. **GPL-3 if going with BlenderProc:** Fine for in-house data generation; problematic only if you ship a tool that *embeds* it.
5. **Augraphy 8.2.6 quirks** (already documented in CLAUDE.md): no `Fading` class, custom edge-fade strategy needed.
6. **Determinism:** seeds for Faker, polyfactory, Sobol, renderer RNG — all need to be wired through one config root for reproducible RL eval.
7. **macOS multiprocessing:** `spawn` (default Py 3.11) costs ~0.5s/worker init — amortize with long batches and `initializer=load_renderer`.

---

## Source Reports

Full agent reports are in the conversation transcript. Key citations:
- Inv3D paper (closest precedent): https://link.springer.com/article/10.1007/s10032-023-00434-x
- Doc3D / DewarpNet (paper meshes): https://github.com/cvlab-stonybrook/doc3D-dataset
- BlenderProc: https://github.com/DLR-RM/BlenderProc
- Genalog (HTML→degraded image, MIT): https://github.com/microsoft/genalog
- PyTorch3D paper: https://arxiv.org/pdf/2007.08501
- Mitsuba 3: https://github.com/mitsuba-renderer/mitsuba3
- Poly Haven HDRIs: https://polyhaven.com/hdris
- Hydra multi-run: https://hydra.cc/docs/tutorials/basic/running_your_app/multi-run/
