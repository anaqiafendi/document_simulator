# Research Findings: Document Simulator

## Project Overview

This project aims to build a **document simulator** that can:
1. Generate variations of scanned document images based on input samples
2. Modify specific values/fields within documents programmatically
3. Serve as a red teaming tool for testing document extraction and OCR systems
4. Generate synthetic training data for RL tuning of extraction and OCR models

The goal is to create realistic document variations to improve the robustness and accuracy of document processing models.

---

## 1. Document Image Augmentation

### Augraphy (Recommended Primary Tool)
- Python library specifically designed for document image augmentation
- 100+ augmentation effects designed for documents
- Simulates ink, paper, post-processing, and markup effects
- Pipeline-based architecture for combining effects
- Installation: `pip install augraphy`
- GitHub: https://github.com/sparkfish/augraphy

### Albumentations
- General-purpose image augmentation with document-relevant transforms
- Fast performance (uses OpenCV)
- Geometric transforms, color/brightness adjustments, noise and blur
- Installation: `pip install albumentations`
- Documentation: https://albumentations.ai/

### Document-Specific Augmentation Techniques
1. **Geometric**: Perspective distortion, rotation, skew, warping
2. **Degradation**: Paper texture/aging, ink bleeding/fading, watermarks, stains, crumpling
3. **Scanning Artifacts**: Scanner noise, shadows, lighting variations, motion blur, defocus
4. **Post-processing**: JPEG compression, resolution changes, contrast adjustments, binarization

---

## 2. OCR and Document Extraction

### OCR Engines

| Engine | Type | Languages | Best For |
|--------|------|-----------|----------|
| **PaddleOCR** | Deep learning | Multi-language | Best accuracy/speed balance |
| **EasyOCR** | Deep learning | 80+ | Complex layouts |
| **Tesseract** | Traditional + LSTM | 100+ | Baseline comparison |

### Document Understanding Models

- **LayoutLM / LayoutLMv3** (Microsoft) — Combines text, layout, and image; pre-trained on millions of documents; available via Hugging Face
- **Donut** — OCR-free document understanding; end-to-end transformer model
- **TrOCR** — Transformer-based OCR; state-of-the-art text recognition

### Cloud Services (for benchmarking)
- Google Cloud Vision API
- AWS Textract
- Azure Computer Vision / Form Recognizer

---

## 3. Reinforcement Learning for Document Processing

### RL Frameworks

| Framework | Backend | Best For |
|-----------|---------|----------|
| **Stable-Baselines3** | PyTorch | Primary RL framework (well-documented) |
| **Ray RLlib** | Multiple | Large-scale distributed training |
| **TF-Agents** | TensorFlow | TF ecosystem projects |

### RL Problem Formulation
- **State**: Document image + current extraction results
- **Action**: Select regions, adjust parameters, choose extraction methods
- **Reward**: Accuracy of extracted information vs. ground truth
- **Goal**: Learn optimal extraction strategy for various document types

### Training Considerations
- Reward shaping is critical (sparse rewards are challenging)
- May need curriculum learning (start with easy documents)
- Combination with supervised learning likely optimal
- Consider imitation learning from expert extraction rules

---

## 4. Synthetic Document Generation

### Template-Based Generation
- **ReportLab** — Programmatic PDF creation (`pip install reportlab`)
- **Pillow (PIL)** — Image creation, text rendering, format conversion
- **Faker** — Realistic fake data (names, addresses, dates, amounts) (`pip install faker`)
- **python-docx** — Word document generation (`pip install python-docx`)

### Generative AI Approaches
- **Diffusion Models / ControlNet** — Generate realistic document backgrounds/textures
- **GANs** — Learn to generate document-like images (research-level)

---

## 5. Value Modification and Field Replacement

### Approaches

#### OCR + Template Matching
1. Use OCR to locate existing values
2. Identify field types (dates, amounts, names)
3. Replace with synthetic values using similar formatting
4. Re-render with matching fonts and styling

#### Inpainting + Text Rendering
1. Use image inpainting to remove existing text (`cv2.inpaint()`)
2. Render new text with matching font/style (Pillow ImageDraw)
3. For advanced cases: LaMa, Stable Diffusion inpainting

#### PDF Layer Manipulation (for digital documents)
1. Parse PDF text layers (PyPDF2, pdfplumber)
2. Modify text content programmatically
3. Re-render to image (pdf2image)

### Font Matching
- **fontTools** (`pip install fonttools`) — Parse and extract font metrics
- **Pillow + system fonts** — Render text with specific fonts

---

## 6. Data Annotation and Ground Truth

- **Label Studio** — Open-source data labeling with OCR integration (`pip install label-studio`)
- **CVAT** — Annotation tool from Intel, good for bounding boxes
- **VGG Image Annotator (VIA)** — Lightweight browser-based annotation

---

## 7. Recommended Tech Stack

### Core
| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ |
| Augmentation | Augraphy, Albumentations |
| Image Processing | Pillow, OpenCV, NumPy |
| OCR | PaddleOCR (primary), Tesseract (baseline) |
| Document Understanding | LayoutLM via Hugging Face Transformers |

### Synthetic Data
| Component | Technology |
|-----------|-----------|
| Fake Data | Faker |
| PDF Generation | ReportLab |
| DOCX Generation | python-docx |

### RL Training
| Component | Technology |
|-----------|-----------|
| RL Framework | Stable-Baselines3 |
| Deep Learning | PyTorch |
| Experiment Tracking | Weights & Biases or MLflow |

### Data Management
| Component | Technology |
|-----------|-----------|
| Annotation | Label Studio |
| Version Control | DVC |
| Metadata Storage | SQLite or PostgreSQL |

---

## 8. Proposed Pipeline

```
1. Template Creation
   - Create base document templates (ReportLab/python-docx)
   - Define field locations and types

2. Value Variation
   - Generate synthetic values (Faker)
   - Modify document fields programmatically

3. Image Augmentation
   - Apply Augraphy augmentation pipeline
   - Generate multiple variations per document
   - Simulate real-world scanning conditions

4. Ground Truth Management
   - Track original values and locations
   - Store metadata (field types, positions, values)

5. RL Training Pipeline
   - Feed augmented documents to extraction model
   - Calculate reward based on extraction accuracy
   - Update RL policy, iterate

6. Evaluation
   - Test on held-out documents
   - Measure extraction accuracy
   - Analyze failure modes
```

---

## 9. Feasibility Assessment

### Technical Feasibility: HIGH

**Strengths:**
- Mature libraries exist for all core components
- Document augmentation is a solved problem (Augraphy)
- OCR technology is production-ready
- RL frameworks are well-established

### Implementation Complexity: MEDIUM

| Component | Estimated Time |
|-----------|---------------|
| Basic augmentation pipeline | 1-2 weeks |
| OCR integration | 1 week |
| Template-based generation | 2 weeks |
| Value modification with font matching | 2-3 weeks |
| RL integration and reward design | 3-4 weeks |
| End-to-end pipeline | 2 weeks |
| **Total MVP** | **8-12 weeks** |

---

## 10. Potential Challenges & Mitigations

| Challenge | Mitigation |
|-----------|-----------|
| Font matching for realistic text replacement | Start with digital PDFs; use deep learning inpainting for complex cases |
| RL reward function design | Start with supervised baseline; use dense per-field rewards |
| Unrealistic augmentations harming training | Use Augraphy (research-validated); validate with domain experts |
| Tracking field locations through augmentations | Use coordinate-aware augmentation; store transformation matrices |
| Scalability (millions of variations) | Parallelize pipeline; use efficient OpenCV processing; cache results |

---

## 11. Alternative Approaches

| Approach | When to Use | Trade-offs |
|----------|-------------|-----------|
| Generative models (GANs/diffusion) | Need entirely novel documents | Higher compute, less controllable |
| Supervised learning (no RL) | Simpler baseline needed | Less adaptive, needs more labeled data |
| Commercial Document AI | Benchmarking only | Cost per doc, vendor lock-in, privacy concerns |
| Active learning + synthetic | Have some real documents | Better generalization, needs human annotation |

---

## 12. MVP Specification (4 Weeks)

**Input:** 10 sample document images + CSV with field values to modify
**Processing:** Generate 100 variations per document (1,000 total)
**Output:** Augmented images + ground truth JSON with field locations and values
**Evaluation:** Run OCR, measure extraction accuracy, compare with baseline

**MVP Stack:** Python 3.10+, Augraphy, Pillow, PaddleOCR, Faker, pandas, matplotlib

---

## 13. References & Resources

### Libraries
- Augraphy: https://github.com/sparkfish/augraphy
- Albumentations: https://albumentations.ai/
- PaddleOCR: https://github.com/PaddlePaddle/PaddleOCR
- EasyOCR: https://github.com/JaidedAI/EasyOCR
- Stable-Baselines3: https://stable-baselines3.readthedocs.io/
- Label Studio: https://labelstud.io/

### Models (Hugging Face)
- LayoutLM: https://huggingface.co/models?search=layoutlm
- Donut: https://huggingface.co/naver-clova-ix/donut-base
- TrOCR: https://huggingface.co/models?search=trocr

### Papers
- "Augraphy: A Data Augmentation Library for Document Images" (2022)
- "LayoutLMv3: Pre-training for Document AI with Unified Text and Image Masking" (2022)
- "Donut: Document Understanding Transformer without OCR" (2022)

---

## Conclusion

This project is highly feasible using existing open-source technologies. The recommended approach is:

1. **Phase 1-3**: Build solid augmentation and extraction pipeline
2. **Phase 4**: Add RL capabilities once foundation is stable
3. **Iterate** based on evaluation metrics

**Key Success Factors:**
- Leverage proven libraries (especially Augraphy)
- Start simple before adding RL complexity
- Build robust ground truth management from the beginning
- Focus on practical, incremental improvements

---

## 2026-03-07 — JS Synthetic Document Generator UI

### Context

The Streamlit zone editor (`src/document_simulator/ui/pages/00_synthetic_generator.py`) is broken because `streamlit-drawable-canvas` (maintained by andfanilo) was archived on 2025-03-01 and is now read-only. The root cause is that Streamlit removed the `image_to_url` internal helper from `streamlit.elements.image` (moved to `image_utils`) in Streamlit ≥ 1.40. The original package raises `AttributeError: module 'streamlit.elements.image' has no attribute 'image_to_url'` on every canvas render. The project is already on Streamlit 1.54.0 (pinned via `streamlit>=1.32.0`).

A community fork `streamlit-drawable-canvas-fix` exists on PyPI and patches the import path, but it is an unofficial stopgap with no long-term guarantee of tracking Streamlit API changes. Replacing the zone editor with a proper JavaScript SPA is the durable solution.

The remaining five Streamlit pages (augmentation lab, OCR engine, batch processing, evaluation dashboard, RL training) are fully functional and must not be disrupted.

---

### 1. JS Libraries for Document Annotation / Zone Editors

#### PDF Rendering

| Library | Version (2026-03) | Licence | Weekly DLs | Verdict |
|---|---|---|---|---|
| `pdfjs-dist` | 5.5.207 | Apache 2.0 | ~8 M | **Best choice.** Mozilla's official PDF.js generic build. Low-level canvas rendering API. Worker script keeps rendering off the main thread. Must pin worker version to match `pdfjs-dist` version exactly — mismatches are the most common setup error. |
| `react-pdf` | 9.x | MIT | ~950 K | Thin React wrapper around `pdfjs-dist`. Provides `<Document>` and `<Page>` components. Does not include annotations, form filling, or signatures. Good for rendering-only use cases; adds little value when the application needs a custom annotation layer anyway. |
| `@react-pdf-viewer/core` | 3.12.0 | MIT | Low | Last published 3 years ago — **unmaintained**. Do not use. |

**Decision: use `pdfjs-dist` directly.** `react-pdf` is a thin convenience wrapper; using `pdfjs-dist` directly avoids a middleman and gives full control of canvas layers needed for the zone overlay.

**Server-side vs browser-side PDF rendering.** Two approaches exist:

- **Server-side (PyMuPDF/FastAPI):** The Python backend opens the PDF with `fitz.open()`, calls `page.get_pixmap(dpi=150)`, converts to PNG bytes, base64-encodes, and returns from a FastAPI endpoint. The browser receives a flat PNG — no PDF parsing in JS. Simple and avoids cross-origin worker headaches.
- **Browser-side (pdfjs-dist):** The browser fetches the raw PDF bytes and renders via `pdfjs-dist`. More interactive (zoom, text selection layer), but requires a Web Worker setup and careful CORS headers.

**Recommended approach: server-side rendering for MVP.** The synthesis engine already uses PyMuPDF (`fitz.open(path)[page_num].get_pixmap(dpi=150)`) — re-using this path is zero additional code. The FastAPI endpoint returns `{ "image": "<base64 PNG>", "width": W, "height": H, "dpi": 150 }`. The browser composites the annotation canvas on top of an `<img>` element. Browser-side PDF rendering can be added later if zoom/text-layer is needed.

#### Canvas / Annotation Layer

| Library | Licence | React binding | Maintenance | Fit |
|---|---|---|---|---|
| **Konva.js + react-konva** | MIT | `react-konva` (official) | Active (2014–present) | **Best fit.** Declarative React API. Drag-and-drop, resizable rectangles, hit detection all built in. Lightweight (~130 KB gzipped). Used for design editors, annotation tools, interactive maps. |
| Fabric.js | MIT | No official binding; imperative API | Active | More features (filters, SVG export) but heavier (~300 KB) and requires manual React lifecycle bridging. Overkill for rectangle annotation. |
| Plain HTML5 Canvas | — | — | N/A | Maximum control; high implementation cost. Not worth it when Konva provides exactly what is needed. |
| `@excalidraw/excalidraw` | MIT | React | Active | Whiteboard tool — wrong abstraction for form zone definition. |

**Decision: `react-konva`.** The zone editor needs exactly what Konva provides: draggable resizable `<Rect>` components rendered on top of an `<Image>` background, with click-to-select and coordinate read-back. The `react-konva` pattern maps cleanly: one Konva `Stage` → one Konva `Layer` for the background image → one Konva `Layer` for zone rectangles. Zone coordinates are read directly from Konva node attributes (`x`, `y`, `width`, `height`) in screen pixels and scaled to document pixels: `doc_px = screen_px * (render_dpi / display_dpi)`.

---

### 2. JS Framework Choice

| Framework | Bundle (runtime) | Ecosystem | Hiring pool | Streamlit component support | Verdict |
|---|---|---|---|---|---|
| **React 18** | ~42 KB | Largest | Very large | First-class (`streamlit/component-template` ships React + Vite) | **Recommended** |
| Vue 3 | ~16 KB | Large | Large | Community template available | Good alternative |
| Svelte 5 | ~1.6 KB | Growing | Smaller | Less documented for Streamlit components | Best perf, weakest ecosystem |

**Decision: React 18 + TypeScript + Vite.**

Rationale:
- The Streamlit official component template (`streamlit/component-template` v2) ships a React 18 + Vite 6 + TypeScript 5 starter out of the box, meaning bidirectional communication boilerplate is already solved.
- `react-konva` is a first-class React library.
- `pdfjs-dist` has the most React examples and integration guides.
- React dominates the document-tooling SaaS ecosystem (DocuSign, HelloSign, PDF.js Express all publish React SDKs or examples). Future library additions are more likely to have React bindings.
- The development team already works in Python; React has the largest hiring pool if a dedicated frontend developer is ever brought in.

---

### 3. Python Backend API

#### Options Evaluated

| Option | Verdict |
|---|---|
| **FastAPI** | Recommended. Async, type-annotated, Pydantic-native, ships `StaticFiles` for serving the React build. `uvicorn` startup is a single line. |
| Flask | Synchronous by default. Pydantic integration requires extra glue. No strong reason to prefer it. |
| Starlette | FastAPI is built on Starlette. Use FastAPI unless zero-overhead is critical. |
| Django REST | Massive overkill for an internal tool API. |

**Decision: FastAPI + uvicorn.**

The synthesis engine (`SyntheticDocumentGenerator`, `SynthesisConfig`, `ZoneDataSampler`, etc.) is pure Python with Pydantic models. FastAPI endpoints map 1:1 to the existing Python API:

```
POST /api/synthesis/render-template   → TemplateLoader.load() → base64 PNG
POST /api/synthesis/preview           → generator.generate_one(seed) → base64 PNG
POST /api/synthesis/generate          → generator.generate(n, write=True) → { output_dir, count }
GET  /api/synthesis/config/schema     → SynthesisConfig.model_json_schema()
POST /api/synthesis/config/validate   → SynthesisConfig.model_validate(payload)
GET  /api/synthesis/download/{job_id} → StreamingResponse(zip_bytes)
```

`SynthesisConfig` is already a Pydantic `BaseModel` with `model_dump_json()` / `model_validate()`, so JSON serialisation is zero-cost.

#### How to Run Alongside Streamlit

The standard deployment pattern is two separate processes:

```
# Terminal 1 — Streamlit (existing pages, port 8501)
uv run streamlit run src/document_simulator/ui/app.py

# Terminal 2 — FastAPI + React zone editor (port 8000)
uv run uvicorn document_simulator.api.app:app --port 8000 --reload
```

FastAPI serves the React build as static files via `app.mount("/", StaticFiles(directory="frontend/dist", html=True))`. All API routes are prefixed `/api/...` so the SPA catch-all does not shadow them.

The Streamlit page `00_synthetic_generator.py` is replaced with a simple redirect page:

```python
# 00_synthetic_generator.py (replacement stub)
import streamlit as st
st.info("The Synthetic Document Generator has moved to the standalone zone editor.")
st.markdown("[Open Zone Editor](http://localhost:8000)", unsafe_allow_html=True)
```

This preserves the sidebar navigation entry without breaking anything.

**Alternative: Streamlit Custom Component (iframe).** The React app can also be embedded as a Streamlit custom component via `st.components.v1.iframe("http://localhost:8000", height=900)`. This keeps the navigation experience inside Streamlit but introduces a same-origin restriction for `Streamlit.setComponentValue()` callbacks. The standalone app on a separate port is simpler and more flexible for a tool this complex.

---

### 4. Packaging the React App Alongside the Python Package

The React source lives at `frontend/` at the repo root (sibling to `src/`). It is a standard Vite project:

```
frontend/
├── package.json
├── vite.config.ts
├── tsconfig.json
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── components/
    │   ├── ZoneCanvas.tsx      # react-konva stage + zone Rects
    │   ├── TemplateDisplay.tsx # img tag from server-rendered PNG
    │   ├── ZoneList.tsx        # sidebar list of zones
    │   ├── RespondentPanel.tsx # respondent + field type config
    │   └── PreviewGallery.tsx  # 3-sample preview grid
    └── api/
        └── client.ts           # typed fetch wrappers for /api/synthesis/*
```

Build output (`frontend/dist/`) is committed to the repo or generated in CI. The FastAPI app mounts it:

```python
# src/document_simulator/api/app.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()
# API routes registered first
app.include_router(synthesis_router, prefix="/api/synthesis")
# SPA catch-all last
app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")
```

The `pyproject.toml` can add a `[project.scripts]` entry:

```toml
document-simulator-api = "document_simulator.api.app:run"
```

Where `run()` calls `uvicorn.run("document_simulator.api.app:app", host="0.0.0.0", port=8000)`.

**No Node.js at runtime.** The React app is pre-built (`npm run build`) and the output is static HTML/JS/CSS. End users need only Python + uv.

---

### 5. PDF Page Rendering in the Browser

#### Option A: Server-side rendering via PyMuPDF (Recommended for MVP)

The FastAPI endpoint `POST /api/synthesis/render-template` accepts the uploaded PDF bytes (as multipart/form-data), opens it with `fitz.open(stream=pdf_bytes, filetype="pdf")`, renders page 0 at 150 DPI, encodes to base64 PNG, and returns:

```json
{
  "image_b64": "...",
  "width_px": 1240,
  "height_px": 1754,
  "dpi": 150
}
```

The React component renders `<img src={`data:image/png;base64,${image_b64}`} />` behind the Konva stage. Zone coordinates drawn on the Konva stage are in screen pixels; scaling to document pixels requires the display scale factor: `doc_x = canvas_x * (doc_width_px / canvas_display_width_px)`.

**Advantages:** Zero JS PDF-parsing complexity. No CORS worker headache. PyMuPDF already a dependency. Works for image templates too (same endpoint, different handler branch).

**Disadvantages:** PDF must round-trip to server. No browser-side zoom/text-layer without re-fetching.

#### Option B: Browser-side rendering via pdfjs-dist

The frontend loads `pdfjs-dist` (Apache 2.0, latest 5.5.207), sets `GlobalWorkerOptions.workerSrc` to the matching worker script from the same package version (critical: mismatched versions cause silent failures), fetches the raw PDF bytes from the server, and renders into a hidden `<canvas>`. The rendered canvas is then used as the Konva background image.

**Advantages:** Zoom without re-fetching. Text selection layer possible. Thumbnail navigation for multi-page documents.

**Disadvantages:** Worker setup is finicky. CORS headers required on PDF serving endpoint. pdfjs-dist version and worker must be pinned together.

**Recommendation:** Start with server-side (Option A) for MVP. Add Option B incrementally when multi-page navigation or zoom is needed.

---

### 6. Relevant Patterns in This Codebase

- **Pydantic everywhere:** `SynthesisConfig`, `ZoneConfig`, `RespondentConfig`, `FieldTypeConfig`, `GeneratorConfig` are all `BaseModel`. FastAPI natively accepts and validates Pydantic models as request/response bodies — no serialisation glue required.
- **PyMuPDF already a dependency:** `pymupdf>=1.23.0` is in `pyproject.toml` core dependencies. The template rendering path in `TemplateLoader` (`fitz.open().get_pixmap(dpi=150)`) is already implemented in `src/document_simulator/synthesis/template.py`.
- **Generator API is clean and synchronous:** `SyntheticDocumentGenerator.generate_one(seed)` and `generate(n, write=True)` are pure Python with no async dependencies. FastAPI can call them directly in a route handler (use `run_in_executor` or `BackgroundTasks` for batch generation to avoid blocking the event loop).
- **GroundTruth JSON format is documented:** `AnnotationBuilder.build()` produces `GroundTruth` which `GroundTruthLoader` can re-read. FastAPI can return the same JSON structure — the React preview panel can render it as a zone overlay.
- **Existing `overlay_bboxes()` component:** Lives in `src/document_simulator/ui/components/image_display.py`. The React equivalent is Konva `<Rect>` components with `stroke` colour matching respondent ink colour and a Konva `<Text>` label. Same concept, different runtime.

---

### 7. Known Gotchas, Performance Considerations, and Compatibility Constraints

| Issue | Detail | Mitigation |
|---|---|---|
| `streamlit-drawable-canvas` archived | Original repo read-only from 2025-03-01. `streamlit-drawable-canvas-fix` on PyPI is an unofficial patch fork. | Remove `streamlit-drawable-canvas` and `streamlit-image-coordinates` from `pyproject.toml` dependencies once the JS replacement is live. |
| PyMuPDF AGPL licence | AGPL triggers on external distribution. Already documented in feature spec and accepted for internal use. | No change needed. |
| FastAPI + uvicorn not in dependencies | Neither is in `pyproject.toml` yet. | Add `fastapi>=0.111.0` and `uvicorn[standard]>=0.30.0` to core dependencies (or a new `[project.optional-dependencies] api` group). |
| CORS between Streamlit (8501) and FastAPI (8000) | If the Streamlit pages ever call the FastAPI API directly via `requests`, there is no CORS issue (server-to-server). If the React app (served on 8000) calls FastAPI on the same origin (8000), no CORS issue. Cross-origin only arises if the React app is served on a different origin than the FastAPI API. | Serve React from FastAPI (same origin). |
| Large PDF upload size | `fitz.open(stream=bytes)` loads the whole PDF into memory. | Limit upload size via FastAPI `UploadFile` max-size; render only the requested page on demand. |
| Konva coordinate system | Konva `Stage` uses CSS pixels, not device pixels. On HiDPI displays the stage appears blurry unless `scaleX/scaleY` is set to `window.devicePixelRatio` and CSS width/height are set accordingly. | Apply the standard Konva HiDPI pattern: `stage.width(containerWidth * ratio); stage.scale({ x: ratio, y: ratio })`. |
| react-konva peer dependency | `react-konva` requires `react` and `react-dom` as peer dependencies. Must be the same React version. | Standard Vite + React setup satisfies this automatically. |
| Batch generation blocking the event loop | `generate(n=1000, write=True)` is CPU-bound (PIL rendering). Calling it directly in a FastAPI route blocks the uvicorn worker. | Use `fastapi.BackgroundTasks` or `asyncio.get_event_loop().run_in_executor(None, generate_fn)` to offload to a thread pool. Return a job ID immediately; the client polls `GET /api/synthesis/job/{job_id}` for status. |
| NumPy < 2.0 constraint | Already pinned in `pyproject.toml` (`numpy>=1.26.0,<2.0.0`) for PaddlePaddle compatibility. No impact on the JS frontend or FastAPI. | No action needed. |
| Node.js build step | Developers need Node.js (≥ 18) installed to rebuild the frontend. The pre-built `frontend/dist/` can be committed to avoid this for most contributors. | Add a `Makefile` or `justfile` target: `make build-frontend` that runs `cd frontend && npm install && npm run build`. |

---

### 8. Recommended Implementation Approach

**Architecture: FastAPI + React 18 + Vite + react-konva + pdfjs-dist (server-side rendering MVP)**

#### Phase 1: FastAPI backend (2–3 days)

1. Create `src/document_simulator/api/` package:
   - `app.py` — FastAPI app, CORS middleware, router registration, static file mount
   - `routers/synthesis.py` — `/render-template`, `/preview`, `/generate`, `/config/validate`, `/job/{id}`
   - `models.py` — FastAPI-specific request/response models (thin wrappers or re-exports of existing Pydantic models)
2. Add `fastapi>=0.111.0` and `uvicorn[standard]>=0.30.0` to `pyproject.toml` (core dependencies or new `api` optional group).
3. Write pytest tests for each endpoint using `httpx.AsyncClient` and `FastAPI.TestClient`.

#### Phase 2: React frontend scaffold (1–2 days)

1. `cd frontend && npm create vite@latest . -- --template react-ts`
2. Install: `npm install react-konva konva pdfjs-dist`
3. Configure `vite.config.ts` to proxy `/api` to `http://localhost:8000` during development.
4. Build `api/client.ts` with typed fetch wrappers for all synthesis endpoints.

#### Phase 3: Zone editor components (3–5 days)

1. `TemplateDisplay.tsx` — renders server-provided base64 PNG as a Konva `Image` node.
2. `ZoneCanvas.tsx` — Konva `Stage` + `Layer`. Draw mode: mouse-down starts a new `Rect`, mouse-up finalises it. Select mode: click to select, drag handles to resize. Each zone is a Konva `Rect` + `Text` label. Zone state lives in React `useState` / `useReducer`.
3. `RespondentPanel.tsx` — sidebar with respondent cards and field type sub-cards. Mirrors the Streamlit expander layout from the feature spec. Colour pickers, font selectors, fill style radios, jitter sliders.
4. `ZoneList.tsx` — list of placed zones with respondent/field-type dropdowns and faker provider selector.
5. `PreviewGallery.tsx` — fetches 3 preview PNGs from `/api/synthesis/preview` in parallel. Re-roll button calls the same endpoint with a different seed.

#### Phase 4: Batch generation + download (1 day)

1. "Generate batch" button calls `POST /api/synthesis/generate` with `write=true`. Returns `{ job_id }`.
2. Client polls `GET /api/synthesis/job/{job_id}` every 2 s until `status === "done"`.
3. Download link calls `GET /api/synthesis/download/{job_id}` which streams a ZIP of all PNGs + JSONs.

#### Phase 5: Streamlit stub page (30 min)

Replace `src/document_simulator/ui/pages/00_synthetic_generator.py` with a stub that shows a link/iframe to the zone editor. The five remaining Streamlit pages are untouched.

#### Phase 6: Cleanup (1 day)

- Remove `streamlit-drawable-canvas>=0.9.0` and `streamlit-image-coordinates>=0.1.4` from `pyproject.toml` dependencies.
- Remove `streamlit_drawable_canvas.*` and `streamlit_image_coordinates.*` from `[tool.mypy.overrides]`.
- Run full test suite: `uv run pytest -m "not slow" -q`.

**Total estimated effort: 8–12 developer-days.**

---

### 9. Alternatives Considered and Why They Are Inferior

| Alternative | Why Inferior |
|---|---|
| `streamlit-drawable-canvas-fix` (unofficial fork) | Unofficial, unarchived stopgap. No guarantee of tracking future Streamlit API changes. Does not address the fundamental problem that `streamlit-drawable-canvas` is abandoned. Acceptable as a 1-day hotfix but not a durable solution. |
| Rebuild zone editor as a pure Streamlit page with numeric inputs (no canvas drawing) | Loses the core DocuSign-style drag-to-place UX described in the feature spec (AC-11). Zone placement via `x1, y1, x2, y2` number inputs is functional but frustrating for non-developers placing 10+ zones on a form. |
| Label Studio embedded via `st.components.v1.iframe` | Label Studio is a heavy annotation tool (Docker or pip install, ~200 MB). Launching it as a subprocess adds operational complexity. Its UI is not DocuSign-like and does not integrate with `SynthesisConfig`. Overkill. |
| CVAT | Same issues as Label Studio. Web-based but requires a full server deployment (PostgreSQL, Redis, nginx). |
| Streamlit custom component (React + `streamlit-component-lib`) | Valid approach, but the bidirectional communication API (`Streamlit.setComponentValue`) is limited: it sends one value per interaction and requires a Python rerun for every canvas event. The zone editor needs continuous interaction (drag, resize, select, configure). Embedding as a full SPA on a separate port is cleaner. |
| Next.js instead of Vite + React | Next.js is a full-stack framework with SSR. The zone editor is a pure SPA with no SSR requirements. Vite produces a smaller, simpler build. Next.js adds deployment complexity (Node.js server required at runtime). |
| Vue 3 instead of React | Vue 3 is a good choice, but `react-konva` has no Vue equivalent with the same maturity. Konva's own Vue binding (`vue-konva`) exists but is less actively maintained. The Streamlit component template also favours React. |

---

### 10. Preserving the Existing Streamlit Pages

The five functional Streamlit pages must not be touched:

| Page | File | Status |
|---|---|---|
| Augmentation Lab | `01_augmentation_lab.py` | Intact |
| OCR Engine | `02_ocr_engine.py` | Intact |
| Batch Processing | `03_batch_processing.py` | Intact |
| Evaluation Dashboard | `04_evaluation.py` | Intact |
| RL Training | `05_rl_training.py` | Intact |

The only change to the Streamlit app is:
- `00_synthetic_generator.py` is replaced with a stub redirect page (no business logic removed — all business logic lives in `src/document_simulator/synthesis/` which is unchanged).
- `streamlit-drawable-canvas` and `streamlit-image-coordinates` are removed from `pyproject.toml`. The stub page does not import them.
- The Streamlit app (`app.py`) home page and navigation are unchanged.

The FastAPI server is an additive new entry point. It imports from `document_simulator.synthesis.*` (existing, unchanged). It does not modify or replace any existing module.

---

### Summary Table

| Decision | Choice | Rationale |
|---|---|---|
| JS framework | React 18 + TypeScript + Vite | Largest ecosystem, first-class Streamlit component template, react-konva requires React |
| Canvas / annotation layer | react-konva (MIT) | Declarative React API, drag-resize rectangles, active maintenance since 2014 |
| PDF rendering | PyMuPDF server-side → base64 PNG (MVP) | Zero new dependencies, already in codebase, avoids pdfjs-dist worker complexity |
| Python API | FastAPI + uvicorn | Pydantic-native, async, StaticFiles for SPA serving, zero friction with existing models |
| Deployment | FastAPI on :8000 serves React + API; Streamlit on :8501 serves other pages | Clean separation, no interference, standard two-process pattern |
| Existing pages | Untouched | Only `00_synthetic_generator.py` is replaced with a redirect stub |
| Removed dependencies | `streamlit-drawable-canvas`, `streamlit-image-coordinates` | Both broken/archived; zone editor no longer uses them |
| Added dependencies | `fastapi>=0.111.0`, `uvicorn[standard]>=0.30.0` | Required for the API server |

---

### Sources Consulted

- [react-pdf npm](https://www.npmjs.com/package/react-pdf)
- [react-pdf GitHub (wojtekmaj)](https://github.com/wojtekmaj/react-pdf)
- [pdfjs-dist npm](https://www.npmjs.com/package/pdfjs-dist)
- [PDF.js Getting Started](https://mozilla.github.io/pdf.js/getting_started/)
- [react-pdf-highlighter (agentcooper)](https://github.com/agentcooper/react-pdf-highlighter)
- [Konva.js documentation — React](https://konvajs.org/docs/react/index.html)
- [react-konva npm](https://www.npmjs.com/package/react-konva)
- [react-konva GitHub (MIT licence)](https://github.com/konvajs/react-konva/blob/master/LICENSE)
- [Konva vs Fabric comparison (DEV Community)](https://dev.to/lico/react-comparison-of-js-canvas-libraries-konvajs-vs-fabricjs-1dan)
- [Konva vs Fabric npm-compare](https://npm-compare.com/fabric,konva)
- [streamlit-drawable-canvas issue #157 — image_to_url](https://github.com/andfanilo/streamlit-drawable-canvas/issues/157)
- [streamlit-drawable-canvas-fix on PyPI](https://pypi.org/project/streamlit-drawable-canvas-fix/)
- [Streamlit Custom Components — intro](https://docs.streamlit.io/develop/concepts/custom-components/intro)
- [Streamlit component-template (GitHub)](https://github.com/streamlit/component-template)
- [streamlit-component-template-react-hooks (whitphx)](https://github.com/whitphx/streamlit-component-template-react-hooks)
- [FastAPI Static Files](https://fastapi.tiangolo.com/tutorial/static-files/)
- [Serving React with FastAPI](https://www.deeplearningnerds.com/how-to-serve-a-react-app-with-fastapi-using-static-files/)
- [FastAPI + Streamlit ML serving (TestDriven.io)](https://testdriven.io/blog/fastapi-streamlit/)
- [Build React PDF viewer with pdfjs-dist (Nutrient)](https://www.nutrient.io/blog/how-to-build-a-reactjs-viewer-with-pdfjs/)
- [Top 6 React PDF Viewer Libraries 2025](https://blog.react-pdf.dev/top-6-pdf-viewers-for-reactjs-developers-in-2025)
- [React vs Vue vs Svelte 2026 (Medium)](https://medium.com/h7w/react-vs-vue-vs-svelte-we-rebuilt-our-saas-in-all-three-heres-what-broke-1f166d22e26d)
- [PyMuPDF documentation](https://pymupdf.readthedocs.io/en/latest/tutorial.html)
