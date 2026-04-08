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

## 2026-04-06 — Augmentation UI Perceptual Language Reframing

### Context

During a live demo with Anand (2026-04-06), feedback was given that the term "jitter" in the augmentation UI is misleading. Verbatim from the transcript:

> "jitter is too literal here. So feedback for you. The point is not that these things get filled out in nicely typed fonts, right? The point is that there's it's difficult to process because... jitter in image processing, jitter could look like, you know, weird angles, less resolution, right? Noise, you know what I mean? Noise over the the text, right?"

The current augmentation lab uses:
- Technical parameter names in the sidebar sliders (e.g., "InkBleed probability", "Fading (LowLightNoise) probability")
- Phase groupings labelled "Ink Phase", "Paper Phase", "Post Phase"
- The word "jitter" in synthesis `FieldTypeConfig` for positional variation (unrelated to perceptual degradation)

The audience is business users ("it's not really just for devs, it's for business users"), so language should describe real-world scenarios, not library internals.

### 1. Existing Patterns in the Codebase

- `CATALOGUE` in `augmentation/catalogue.py` already has `display_name` and `description` fields per augmentation — these can be improved without changing the Python parameter names
- The 12-dim sidebar sliders in the Preset tab use `st.slider(label, ...)` — labels can be changed freely without breaking any backend
- Phase tab labels in the Catalogue tab (`"Ink Phase"`, `"Paper Phase"`, `"Post Phase"`) are plain strings
- `FieldTypeConfig` in `synthesis/zones.py` uses `jitter_x`, `jitter_y`, `char_spacing_jitter` as Python attribute names — these must NOT be renamed (would be a breaking API change). The UI can display them with different labels.

### 2. Recommended Implementation Approach

**A — Preset sidebar slider labels:** Replace raw technical names with plain English descriptions. Add `help=` tooltip strings explaining the real-world effect.

**B — Catalogue phase tab headers:** Rename to business-meaningful groupings:
- "Ink Phase" → "Ink Degradation" (what ink looks like after wear/time/printing)
- "Paper Phase" → "Paper Degradation" (what the paper surface looks like)
- "Post Phase" → "Capture Conditions" (what happens when the document is photographed/scanned)

**C — Catalogue description strings:** Improve `description` values in `catalogue.py` to be 1–2 sentence plain English that describes the real-world scenario (e.g., "This simulates ink bleed-through from the other side of the page, common in thin paper receipts").

**D — No Python API changes:** `jitter_x`, `jitter_y`, `char_spacing_jitter` stay as-is in the Python models. The synthesis page already redirects to the React app which owns those labels.

### 3. No New Dependencies

This is a pure UI label/copy change. No new Python packages, no backend changes, no API changes.

### 4. Testing Approach

- Existing AppTest integration tests for the augmentation lab check for label substrings. They must be updated to match the new labels.
- New tests verify that the plain-English section headers and slider labels are present.
- No new tests required for `catalogue.py` description strings (pure text content).

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
---

## 2026-03-07 — Multi-Template Batch Augmentation

### Context

This section documents research findings for extending the Batch Processing page
(`src/document_simulator/ui/pages/03_batch_processing.py`) and the underlying
`BatchAugmenter` (`src/document_simulator/augmentation/batch.py`) to support
**multi-template batch augmentation**: given N input document images, generate M
total augmented outputs where each output randomly picks one input as its source template.

---

### 1. Existing `BatchAugmenter` (`augmentation/batch.py`) — Full Analysis

Current interface:

```python
class BatchAugmenter:
    def __init__(self, augmenter="default", num_workers=4, show_progress=False)
    def augment_batch(self, images: List[Image | Path], parallel=True) -> List[Image]
    def augment_directory(self, input_dir, output_dir, ...) -> List[Path]
```

**Key observations:**

- `augment_batch` takes a flat list of images and returns one augmented copy per input (1:1 mapping).
- Multiprocessing is done via `multiprocessing.Pool.imap` with a top-level picklable helper `_augment_one(args)`.
- No random seed is set anywhere — augmentation results are non-deterministic by design (Augraphy applies transforms with random intensity).
- The existing API must remain fully backward-compatible: `augment_batch(images)` must continue to work with no new required arguments.

**Extension point identified:** Add a new method `augment_multi_template` (separate from `augment_batch`) that takes `sources`, `mode`, and per-mode count parameters. This avoids any signature change to `augment_batch`.

---

### 2. Existing Batch Processing Page (`03_batch_processing.py`) — Full Analysis

Current flow:
1. User uploads N files (images or PDFs); PDFs expand page-by-page.
2. Sidebar: preset selectbox, worker slider, parallel checkbox, "Run Batch Augmentation" button.
3. On run: `BatchAugmenter(augmenter=preset, num_workers=n).augment_batch(images, parallel=parallel)`.
4. Results stored in `state.set_batch_results(results)`.
5. ZIP download + thumbnail grid (up to 8 before/after pairs).

ZIP naming: `{original_stem}.png`. For PDFs: `{stem}_p{page}.png`.

**Key design constraints:**
- `st.download_button` is not accessible as `at.download_button` in AppTest — existing tests check `at.metric` labels only.
- No `at.file_uploader` — tests inject images via `at.session_state`.
- Session state key `batch_input_labels` is used for per-file display names.

---

### 3. Session State Keys (Existing)

```python
KEY_BATCH_INPUTS  = "batch_input_images"
KEY_BATCH_RESULTS = "batch_results"
KEY_BATCH_ELAPSED = "batch_elapsed"
```

No `batch_mode`, `batch_copies_per_template`, or `batch_total_outputs` keys exist yet.

---

### 4. Recommended Implementation Approach

#### 4a. New `BatchAugmenter.augment_multi_template` method

```python
def augment_multi_template(
    self,
    sources: List[Image.Image],
    mode: Literal["per_template", "random_sample"],
    copies_per_template: int = 1,   # N×M mode
    total_outputs: int = 10,        # M-total mode
    seed: Optional[int] = None,
    parallel: bool = True,
) -> List[tuple[Image.Image, str]]:
    """Return (augmented_image, source_stem) pairs."""
```

For **N×M mode** (`mode="per_template"`):
- For each source, generate `copies_per_template` augmented copies.
- Total output count = `len(sources) * copies_per_template`.
- ZIP naming: `{source_stem}_{copy_idx:03d}.png`.

For **M-total random mode** (`mode="random_sample"`):
- Use `random.Random(seed).choices(range(len(sources)), k=total_outputs)` to sample indices with replacement.
- Each selected source gets one augmented copy.
- ZIP naming: `{source_stem}_{global_idx:04d}.png` (avoid collisions when the same source is picked multiple times).

Seeding: use `random.Random(seed)` instance (not module-level `random.seed()`) to avoid contaminating the global state. Workers do not need seeding because Augraphy's non-determinism is a feature, not a bug, for data augmentation.

#### 4b. UI changes to `03_batch_processing.py`

Add a mode radio in the sidebar:
```python
batch_mode = st.radio(
    "Augmentation mode",
    ["Single template", "N×M (copies per template)", "M-total (random sample)"],
    key="batch_mode_radio",
)
```

Show conditional inputs:
- N×M mode: `st.number_input("Copies per template", min_value=1, max_value=100, value=3)`
- M-total mode: `st.number_input("Total outputs (M)", min_value=1, max_value=500, value=20)`
- Optional seed: `st.number_input("Random seed (0 = unseeded)", min_value=0, value=0)`

The existing "Single template" mode calls `augment_batch` unchanged. The two new modes call `augment_multi_template`.

ZIP naming in new modes: `{source_stem}_{idx:03d}.png` — driven by `(augmented_image, source_stem)` tuples.

#### 4c. Session state new keys

```python
KEY_BATCH_MODE           = "batch_mode"           # "single" | "per_template" | "random_sample"
KEY_BATCH_COPIES_PER_TPL = "batch_copies_per_tpl" # int
KEY_BATCH_TOTAL_OUTPUTS  = "batch_total_outputs"  # int
KEY_BATCH_SEED           = "batch_seed"           # int | None
```

---

### 5. Gotchas

1. **ZIP naming collisions in M-total mode** — if the same source is picked 5 times, use a global index: `doc_0001.png`, `doc_0002.png`, etc.
2. **Multiprocessing pickling of PIL Images** — `PIL.Image` objects are picklable. Confirmed by existing `augment_batch` implementation.
3. **`random.choices` with seed** — use `random.Random(seed).choices(...)` not `random.seed(); random.choices(...)` to avoid global seed mutation in test environments.
4. **Backward compatibility** — `augment_batch` signature unchanged. All 8 existing `test_batch_processing.py` tests must continue to pass.
5. **AppTest limitation** — tests inject images via `at.session_state` and assert `at.metric` / `at.radio` widgets.
6. **`copies_per_template` validation** — must be >= 1; raise `ValueError` for invalid input.
7. **Large output counts** — display a warning when `total_outputs > 50`.

---

### 6. Dependencies

No new dependencies required. Uses only stdlib `random`, existing `PIL`, `multiprocessing`, and the existing `BatchAugmenter`/`DocumentAugmenter` stack.

---

### Sources

- Existing `src/document_simulator/augmentation/batch.py`
- Existing `src/document_simulator/ui/pages/03_batch_processing.py`
- Existing `tests/test_batch_processing.py` and `tests/ui/integration/test_batch_processing.py`
- `src/document_simulator/ui/state/session_state.py` — session state patterns
- Python `random.Random` docs for seeded instance-level randomness

---

## 2026-03-07 — Augmentation Lab Catalogue Enhancement

### Context

This section documents research findings for upgrading the Augmentation Lab page
(`src/document_simulator/ui/pages/01_augmentation_lab.py`) from its current design (3 preset
radio buttons + one augmented preview) to a full augmentation catalogue where each Augraphy
transform appears as a thumbnail card, users can toggle transforms on/off, compose a custom
pipeline, and control per-augmentation parameters via sliders that actually drive the output.

---

### 1. Augraphy 8.2.6 — Full Augmentation Catalogue

The installed version (`augraphy==8.2.6`) exports **51 public augmentation classes** from
`augraphy.augmentations`. They are enumerated below, grouped by the natural pipeline phase they
belong to (ink, paper, post), with their key constructor parameters and any known gotchas.

#### 1a. Ink Phase — affects the ink/text layer

| Class | Key constructor params | Notes |
|---|---|---|
| `InkBleed` | `intensity_range`, `kernel_size`, `severity`, `p` | Used in all 3 presets. Reliable. |
| `LowLightNoise` | `num_photons_range`, `alpha_range`, `beta_range`, `gamma_range`, `bias_range`, `dark_current_value`, `exposure_time`, `p` | Replaces deprecated `Fading`. Used in all presets. |
| `BleedThrough` | `intensity_range`, `color_range`, `ksize`, `sigmaX`, `alpha`, `offsets`, `p` | Uses `load_image_from_cache` internally — works standalone but may produce blank bleed-through if no cached image exists; safe to use with `p=1`, the result is just the original when cache is empty. |
| `Letterpress` | `n_samples`, `n_clusters`, `std_range`, `value_range`, `value_threshold_range`, `blur`, `p` | Slow on large images (cluster computation). |
| `LowInkRandomLines` | `count_range`, `use_consistent_lines`, `noise_value`, `p` | Fast. |
| `LowInkPeriodicLines` | `count_range`, `period_range`, `noise_value`, `p` | Fast. |
| `InkColorSwap` | `ink_swap_sequence`, `ink_swap_type`, `ink_swap_iteration`, `ink_swap_color`, `ink_swap_min_width`, `p` | Swaps ink colours — useful for highlighting effects. |
| `InkMottling` | `ink_mottling_alpha_range`, `ink_mottling_noise_scale_range`, `p` | Subtle mottling texture on ink. |
| `InkShifter` | `max_shift_horizontal`, `max_shift_vertical`, `shift_type`, `p` | |
| `Dithering` | `dither`, `order`, `numba_jit`, `p` | Uses Numba JIT — first call is slow (compile); warm up or set `numba_jit=0` for UI previews. |
| `Hollow` | `hollow_median_kernel_value_range`, `hollow_min_width_range`, `p` | |

#### 1b. Paper Phase — affects the underlying paper texture

| Class | Key constructor params | Notes |
|---|---|---|
| `NoiseTexturize` | `sigma_range`, `turbulence_range`, `texture_width_range`, `texture_height_range`, `p` | Used in all presets. Reliable. |
| `ColorShift` | `color_shift_offset_x_range`, `color_shift_offset_y_range`, `color_shift_iterations`, `color_shift_brightness_range`, `color_shift_gaussian_kernel_range`, `p` | Note: NOT a single range — two separate x/y ranges. Used in all presets. |
| `ColorPaper` | `hue_range`, `saturation_range`, `p` | Tints the paper. |
| `Stains` | `stains_type`, `stains_blend_method`, `stains_blend_alpha`, `p` | |
| `WaterMark` | `watermark_word`, `watermark_font_size`, `watermark_font_thickness`, `watermark_font_type`, `watermark_rotation`, `watermark_location`, `watermark_color`, `watermark_method`, `p` | Requires OpenCV `cv2.FONT_*` constants for font type. |
| `BrightnessTexturize` | `range`, `deviation`, `p` | Adds brightness variation across the page. |
| `DelaunayTessellation` | `n_points_range`, `n_horizontal_points_range`, `n_vertical_points_range`, `noise_type`, `color_list`, `color_influence_range`, `p` | Decorative tessellation on paper. |
| `VoronoiTessellation` | `mult_range`, `seed`, `num_cells_range`, `noise_type`, `background_value`, `p` | |
| `PatternGenerator` | `imgx`, `imgy`, `n_rotation_range`, `p` | Alias `quasicrystal.PatternGenerator`. |

#### 1c. Post Phase — affects the printed/scanned document

| Class | Key constructor params | Notes |
|---|---|---|
| `Brightness` | `brightness_range`, `min_brightness`, `min_brightness_value`, `numba_jit`, `p` | Uses Numba JIT — same warm-up caveat as Dithering. |
| `Gamma` | `gamma_range`, `p` | Fast, reliable. |
| `Jpeg` | `quality_range`, `p` | Fast, reliable. |
| `Markup` | `num_lines_range`, `markup_length_range`, `markup_thickness_range`, `markup_type`, `markup_ink`, `markup_color`, `large_word_mode`, `single_word_mode`, `repetitions`, `p` | Used in medium/heavy presets. |
| `Faxify` | `scale_range`, `monochrome`, `monochrome_method`, `monochrome_arguments`, `halftone`, `invert`, `half_kernel_size`, `angle`, `sigma`, `numba_jit`, `p` | Numba JIT. |
| `BadPhotoCopy` | `noise_mask`, `noise_type`, `noise_side`, `noise_iteration`, `noise_size`, `noise_value`, `noise_sparsity`, `noise_concentration`, `blur_noise`, `blur_noise_kernel`, `wave_pattern`, `p` | Visually dramatic; medium speed. |
| `Folding` | `fold_x`, `fold_deviation`, `fold_count`, `fold_noise`, `fold_angle_range`, `gradient_width`, `gradient_height`, `backdrop_color`, `p` | Slow on large images (geometric warping). |
| `BookBinding` | `shadow_radius_range`, `curve_range_right`, `curve_range_left`, `curve_ratio_right`, `curve_ratio_left`, `mirror_range`, `binding_align`, `binding_pages`, `curling_direction`, `backdrop_color`, `enable_shadow`, `p` | Slow — heavy geometric warping. |
| `ShadowCast` | `shadow_side`, `shadow_vertices_range`, `shadow_width_range`, `shadow_height_range`, `shadow_color`, `shadow_opacity_range`, `shadow_iterations_range`, `shadow_blur_kernel_range`, `p` | |
| `LightingGradient` | `light_position`, `direction`, `max_brightness`, `min_brightness`, `mode`, `linear_decay_rate`, `transparency`, `numba_jit`, `p` | Numba JIT. |
| `DirtyDrum` | `line_width_range`, `line_concentration`, `direction`, `noise_intensity`, `noise_value`, `ksize`, `sigmaX`, `p` | |
| `DirtyRollers` | `line_width_range`, `scanline_type`, `p` | |
| `DirtyScreen` | `p` | |
| `GlitchEffect` | `glitch_direction`, `glitch_number_range`, `glitch_size_range`, `glitch_offset_range`, `p` | |
| `Moire` | `moire_density`, `moire_blend_method`, `moire_blend_alpha`, `p` | |
| `NoisyLines` | `noisy_lines_direction`, `noisy_lines_location`, `noisy_lines_number_range`, `noisy_lines_color`, `noisy_lines_noise_intensity_range`, `noisy_lines_stroke_width_range`, `p` | |
| `SubtleNoise` | `subtle_range`, `p` | Very fast and safe. |
| `LinesDegradation` | `line_roi`, `line_gradient_range`, `line_gradient_direction`, `line_split_probability`, `p` | |
| `Scribbles` | `scribbles_type`, `scribbles_ink`, `scribbles_location`, `scribbles_size_range`, `scribbles_count_range`, `scribbles_thickness_range`, `scribbles_brightness_change`, `scribbles_skeletonize`, `scribbles_color`, `scribbles_text`, `p` | |
| `BindingsAndFasteners` | `overlay_types`, `foreground`, `effect_type`, `ntimes`, `nscales`, `edge`, `border_width`, `p` | |
| `PageBorder` | `page_border_width_height`, `page_border_color`, `page_border_background_color`, `page_numbers`, `page_rotation_angle_range`, `curve_frequency`, `curve_height`, `curve_length_one_side`, `same_page_border`, `p` | |
| `Geometric` | `scale`, `translation`, `fliplr`, `flipud`, `crop`, `rotate_range`, `padding`, `padding_type`, `padding_value`, `randomize`, `p` | |
| `Rescale` | `target_dpi`, `source_dpi`, `p` | Changes image resolution. |
| `SectionShift` | `section_shift_x_range`, `section_shift_y_range`, `section_count_range`, `p` | |
| `Squish` | `squish_direction`, `squish_location`, `squish_number_range`, `squish_distance_range`, `p` | |
| `DoubleExposure` | `gaussian_kernel_range`, `offset_direction`, `offset_range`, `p` | Creates double-exposure ghosting. Self-contained — uses only the input image. |
| `ReflectedLight` | `reflected_light_smoothness`, `reflected_light_internal_radius_range`, `reflected_light_external_radius_range`, `p` | |
| `DepthSimulatedBlur` | `p` | |
| `LCDScreenPattern` | `p` | |
| `LensFlare` | `p` | |
| `DotMatrix` | `p` | |

#### 1d. Known Gotchas in 8.2.6

- **No `Fading` class** — use `LowLightNoise` instead (see MEMORY.md).
- **Numba JIT classes** (`Brightness`, `Dithering`, `Faxify`, `LightingGradient`) incur a one-time
  compilation penalty on first call (~2–5 s cold start). For catalogue thumbnails, either warm up
  before rendering or set `numba_jit=0` (slightly slower per-image but no cold start).
- **`BleedThrough`** uses `load_image_from_cache` — safe to instantiate standalone; when no cache
  exists the bleed layer is generated from a noise image rather than a real reverse-side scan.
- **`BookBinding` and `Folding`** are geometric-heavy and slow (~0.5–2 s per 1 MP image).
  Mark them as "slow" in the catalogue and skip them in the auto-generated thumbnail grid unless
  explicitly selected.
- **`Stains`** sometimes produces an all-black output on very small test images
  (< 200 × 200 px); safe on typical document images.
- **`WaterMark`** requires `cv2` constants (`cv2.FONT_HERSHEY_SIMPLEX`) as the default value
  for `watermark_font_type` — this imports OpenCV at construction time.
- **`ColorShift`** takes two separate keyword arguments `color_shift_offset_x_range` and
  `color_shift_offset_y_range`, not a single combined range.
- **`Rescale`** changes the output image resolution — the preview thumbnail will be a different
  size from the original; handle by resizing back to a fixed thumbnail size after applying.

---

### 2. Performance Considerations for a Thumbnail Catalogue

Generating 50+ augmented thumbnails from a single uploaded image simultaneously in Streamlit has
significant performance implications. The following analysis covers what is feasible and what
patterns to use.

#### 2a. Per-augmentation timing estimates (1 MP image, CPU, M-series Mac / comparable)

| Speed tier | Augmentations | Typical time |
|---|---|---|
| Fast (< 100 ms) | `SubtleNoise`, `Jpeg`, `Gamma`, `Brightness`*, `NoiseTexturize`, `ColorShift`, `GlitchEffect`, `DirtyScreen`, `Moire`, `LowInkRandomLines`, `LowInkPeriodicLines`, `DoubleExposure`, `Rescale` | 10–80 ms |
| Medium (100–500 ms) | `InkBleed`, `LowLightNoise`, `BleedThrough`, `Markup`, `Scribbles`, `DirtyDrum`, `DirtyRollers`, `ShadowCast`, `BadPhotoCopy`, `ColorPaper`, `WaterMark`, `Stains`, `Geometric`, `LightingGradient`* | 100–400 ms |
| Slow (> 500 ms) | `Folding`, `BookBinding`, `Letterpress`, `Dithering`*, `Faxify`*, `BrightnessTexturize`, `DelaunayTessellation`, `VoronoiTessellation`, `PatternGenerator` | 500 ms – 4 s |

*First call includes Numba JIT compilation; subsequent calls are fast-tier.

**Total naive sequential cost for all 51 augmentations: ~30–90 s** — clearly too slow for a
live Streamlit session with no caching.

#### 2b. Recommended approach: lazy on-select generation

Do NOT generate all thumbnails at page load time. Instead:

1. **Show the catalogue as a grid of cards** with the augmentation name and a description.
   Cards display the *original* image (or a placeholder) by default.
2. **When the user toggles a card on**, generate only that augmentation's thumbnail at that
   moment, cache the result in `st.session_state`, and immediately display it.
3. **On the first image upload**, optionally pre-generate thumbnails for the ~12 fastest
   augmentations (the "fast" tier above, < 100 ms each) in a background pass to make the
   catalogue feel responsive.
4. **On "Generate catalogue" button press**, run all (or user-selected) augmentations — wrap
   in `st.spinner` and show progress with `st.progress`.

#### 2c. `@st.cache_data` for thumbnail memoization

Wrap the per-augmentation function with `@st.cache_data`. Streamlit will hash the input image
(PIL Image hashing works via the `hash_funcs` mechanism or by converting to bytes for the key).

```python
@st.cache_data(show_spinner=False)
def _apply_single_aug(image_bytes: bytes, aug_name: str, **params) -> bytes:
    """Returns augmented image as PNG bytes, keyed by image + aug_name + params."""
    import numpy as np
    from PIL import Image
    import io
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    aug = _CATALOGUE[aug_name]["factory"](**params)
    result = aug(np.array(img))
    out = io.BytesIO()
    Image.fromarray(result).save(out, format="PNG")
    return out.getvalue()
```

Pass the image as `bytes` (not `PIL.Image`) so Streamlit can hash it correctly. Cache is
invalidated automatically when the uploaded image changes (different bytes = different hash).

#### 2d. Thumbnail sizing

Resize the source image to ~256 × 256 px before applying augmentations for the catalogue
preview. This reduces processing time by 8–16× compared to a 1 MP source. Re-run on the full
image only when the user clicks "Build custom pipeline" or "Augment" with their composed set.

```python
def _thumbnail(img: PIL.Image.Image, size: int = 256) -> PIL.Image.Image:
    img.thumbnail((size, size), PIL.Image.LANCZOS)
    return img
```

---

### 3. Enumerating Augraphy Augmentations Programmatically

The canonical source of truth for what is available in the installed version is:

```python
import inspect
import augraphy.augmentations as aa

CATALOGUE_CLASSES = {
    name: getattr(aa, name)
    for name in aa.__all__
    if inspect.isclass(getattr(aa, name))
}
```

`aa.__all__` (confirmed from `__init__.py`) lists 51 names in 8.2.6:

```
BadPhotoCopy, BindingsAndFasteners, BleedThrough, BookBinding, Brightness,
BrightnessTexturize, ColorPaper, ColorShift, DelaunayTessellation, DepthSimulatedBlur,
DirtyDrum, DirtyRollers, DirtyScreen, Dithering, DotMatrix, DoubleExposure, Faxify,
Folding, Gamma, Geometric, GlitchEffect, Hollow, InkBleed, InkColorSwap, InkMottling,
InkShifter, LCDScreenPattern, Jpeg, LensFlare, Letterpress, LightingGradient,
LinesDegradation, LowInkPeriodicLines, LowInkRandomLines, LowLightNoise, Markup, Moire,
NoiseTexturize, NoisyLines, PageBorder, PatternGenerator, ReflectedLight, Rescale,
Scribbles, SectionShift, ShadowCast, Squish, Stains, SubtleNoise, VoronoiTessellation,
WaterMark
```

For the catalogue, build a static metadata dict (not dynamic inspection at runtime in Streamlit)
because importing all 51 classes at page load adds ~0.5–1 s:

```python
# src/document_simulator/augmentation/catalogue.py
CATALOGUE = {
    "InkBleed": {
        "phase": "ink",
        "description": "Ink bleeds outward from text strokes, simulating wet ink.",
        "speed": "medium",
        "params": {
            "intensity_range": ((0.1, 0.9), "tuple[float,float]", "Bleed intensity"),
            "p": (1.0, "float", "Apply probability"),
        },
        "factory": lambda **kw: InkBleed(**kw),
    },
    # ... one entry per augmentation
}
```

This dict is the single source of truth for the catalogue page — no runtime `inspect` calls.

---

### 4. Best Streamlit Layout for an Augmentation Catalogue

#### 4a. Primary recommendation: tabs by phase + 4-column card grid

```
st.tabs(["Ink Phase", "Paper Phase", "Post Phase", "Custom Pipeline"])

Within each tab:
    st.columns(4) grid — each column holds one augmentation card

Each card:
    st.container(border=True)
        st.image(thumbnail, use_container_width=True)
        st.caption(aug_name)
        st.checkbox("Enable", key=f"aug_enabled_{aug_name}")
        with st.expander("Parameters"):
            # per-aug sliders
```

**Why tabs by phase:** Augraphy's three-phase model maps directly to the pipeline execution
order. Keeping them in tabs reduces visual noise (51 cards in one flat grid is overwhelming)
and teaches users the pipeline structure.

**Why 4 columns:** At 256 px thumbnails, 4 columns fits a standard 1280 px wide layout.
`st.columns(4)` distributes cards evenly. For narrow viewports, drop to `st.columns(2)`.

#### 4b. Alternative: single scrollable grid with phase filter

```
# Phase filter chips (st.radio as horizontal buttons)
phase = st.radio("Phase", ["All", "Ink", "Paper", "Post"], horizontal=True)

# Filtered cards in 4-column grid
visible = [a for a in CATALOGUE if phase == "All" or CATALOGUE[a]["phase"] == phase.lower()]
cols = st.columns(4)
for i, aug_name in enumerate(visible):
    with cols[i % 4]:
        _render_card(aug_name)
```

This is simpler to implement and works well for under 20 visible items at a time.

#### 4c. "Custom Pipeline" tab

After the catalogue tabs, a final tab shows:
- The enabled augmentations in order (drag-to-reorder is not natively supported in Streamlit;
  use `st.multiselect` to let users specify order)
- A single "Augment with custom pipeline" button
- The before/after side-by-side result (reuse existing `show_side_by_side`)

#### 4d. What NOT to use

- **`streamlit-image-gallery`**: External component, adds a dependency, limited control over
  card content (no sliders inside cards).
- **`streamlit-drawable-canvas`**: Irrelevant to this feature.
- **One-tab flat grid of 51 cards**: Too visually dense; users cannot orient themselves.

---

### 5. Connecting Per-Augmentation Sliders to the Actual Augmenter

#### 5a. Current problem

The existing 12 sliders in the sidebar expander are *display-only* — they don't feed into
`DocumentAugmenter`. `DocumentAugmenter._create_pipeline(preset)` always calls
`PresetFactory.create(preset)` which ignores slider values entirely.

#### 5b. What needs to change in `DocumentAugmenter`

Add a second constructor path that accepts an explicit list of configured augmentation objects
(bypassing `PresetFactory`):

```python
class DocumentAugmenter:
    def __init__(
        self,
        pipeline: str = "default",
        custom_augmentations: list | None = None,  # NEW
    ):
        if custom_augmentations is not None:
            # Custom mode: user supplies pre-configured aug objects
            self._augraphy_pipeline = AugraphyPipeline(
                ink_phase=[a for a in custom_augmentations if a._phase == "ink"],
                paper_phase=[a for a in custom_augmentations if a._phase == "paper"],
                post_phase=[a for a in custom_augmentations if a._phase == "post"],
            )
        else:
            self._augraphy_pipeline = self._create_pipeline(pipeline)
```

Note: Augraphy augmentation objects do not carry a `_phase` attribute by default. The
catalogue metadata dict (section 3) tracks phase externally — use that at the UI layer to
separate enabled augmentations into the three lists before passing to `AugraphyPipeline`.

#### 5c. What needs to change in `PresetFactory`

No changes needed to `PresetFactory` itself — it remains the quick-start path. The new custom
path bypasses it entirely.

#### 5d. What needs to change in the page

Replace the preset-only flow with a two-mode UI:

```
Mode A (current): Preset radio → DocumentAugmenter(pipeline=preset)
Mode B (new):     Catalogue toggles + sliders → build aug list →
                  AugraphyPipeline(ink_phase=[...], paper_phase=[...], post_phase=[...])
```

Use `st.radio("Mode", ["Preset", "Custom catalogue"])` to switch.

In custom mode, the page collects:
```python
enabled_augs = []
for aug_name, meta in CATALOGUE.items():
    if st.session_state.get(f"aug_enabled_{aug_name}"):
        params = {k: st.session_state[f"aug_{aug_name}_{k}"] for k in meta["params"]}
        enabled_augs.append(meta["factory"](**params))
```

Then runs:
```python
ink   = [a for (a, name) in zip(enabled_augs, enabled_names) if CATALOGUE[name]["phase"] == "ink"]
paper = [a for (a, name) in zip(enabled_augs, enabled_names) if CATALOGUE[name]["phase"] == "paper"]
post  = [a for (a, name) in zip(enabled_augs, enabled_names) if CATALOGUE[name]["phase"] == "post"]
result = AugraphyPipeline(ink_phase=ink, paper_phase=paper, post_phase=post)(np.array(src))
```

#### 5e. Session state keys for the catalogue

Follow the existing codebase convention of prefixing all keys with the page short name:

```python
f"aug_enabled_{aug_name}"          # bool — checkbox
f"aug_param_{aug_name}_{param_key}"  # float/int — slider value
"aug_catalogue_thumbnails"         # dict[str, bytes] — cached PNG bytes per aug
"aug_mode"                         # "preset" | "catalogue"
```

Add typed accessors to `SessionStateManager` for the new keys (following the pattern in
`src/document_simulator/ui/state/session_state.py`).

---

### 6. Known Constraints: AppTest + Session State

#### 6a. AppTest limitations (Streamlit 1.54.0) — unchanged from existing codebase

From `MEMORY.md` and `CLAUDE.md`:
- No `at.plotly_chart`, `at.download_button`, `at.file_uploader`, `at.image` accessors.
- `at.session_state` is `SafeSessionState` — use `"key" in at.session_state` not `.get()`.
- `streamlit-drawable-canvas` is incompatible; do not introduce it.

#### 6b. Testing the catalogue page

For the new catalogue mode, integration tests should:

1. Inject a pre-baked thumbnail image via `at.session_state["last_uploaded_image"] = pil_img`
   (same pattern as existing `test_augmentation_lab.py`).
2. Set the mode: `at.session_state["aug_mode"] = "catalogue"`.
3. Enable a specific augmentation: `at.session_state["aug_enabled_InkBleed"] = True`.
4. Click the "Generate thumbnail" button.
5. Assert `"aug_catalogue_thumbnails" in at.session_state`.

Avoid testing all 51 augmentations in CI — pick 2–3 representative ones from different speed
tiers. Mark slow-tier augmentation tests with `@pytest.mark.slow`.

#### 6c. Numba JIT in tests

`Brightness` and `Dithering` will hit JIT compilation on first call in a fresh test process,
adding ~3–5 s. Either:
- Use `SubtleNoise` and `Jpeg` as the test augmentations (no Numba).
- Or set `numba_jit=0` in `Brightness(numba_jit=0)` in test fixtures.

#### 6d. `@st.cache_data` in AppTest

`@st.cache_data` decorated functions are **not** mocked or bypassed by AppTest. They execute
normally. This is fine for correctness but means thumbnail tests will actually run the
augmentation (slow). Scope test augmentations to fast-tier only.

---

### 7. Recommended Implementation Approach

#### Phase A — New module: `augmentation/catalogue.py`

Create `src/document_simulator/augmentation/catalogue.py` with:
- A static `CATALOGUE` dict (51 entries) mapping augmentation name to phase, description,
  speed tier, default params, and a factory lambda.
- A helper `apply_single(aug_name: str, image: np.ndarray, **params) -> np.ndarray` function
  that instantiates the augmentation with `p=1` (forced apply) and runs it.
- An `AUGMENTATION_PHASES` dict grouping names by phase for the tab layout.

No changes to `DocumentAugmenter` or `PresetFactory` in this phase.

#### Phase B — Update `DocumentAugmenter`

Add `custom_augmentations: list[Augmentation] | None = None` constructor parameter.
When provided, skip `PresetFactory` and build `AugraphyPipeline` directly from the list,
splitting by phase using the `CATALOGUE` metadata.

Keep backward compatibility: `DocumentAugmenter(pipeline="medium")` must continue to work
exactly as before for the 3-preset radio path and all existing tests.

#### Phase C — Revamp `01_augmentation_lab.py`

Structure:

```
Sidebar:
  Mode radio: "Preset" | "Custom catalogue"

  If preset mode:
    [existing preset radio + sliders — unchanged]

  If catalogue mode:
    [nothing — catalogue controls are in main area]

  "Augment" button (both modes)

Main area:
  File uploader (unchanged)
  Sample data (unchanged)

  If preset mode:
    [existing side-by-side display — unchanged]

  If catalogue mode:
    st.tabs(["Ink Phase", "Paper Phase", "Post Phase", "Custom Pipeline"])
      Each phase tab: 4-column card grid
        Each card: thumbnail image + name + checkbox + params expander
      Custom Pipeline tab:
        st.multiselect to order enabled augmentations
        "Augment" button result (before/after)
```

#### Phase D — Tests

New test file: `tests/ui/integration/test_augmentation_lab_catalogue.py`

Test plan:
- Page loads in catalogue mode without error.
- Catalogue tabs are present.
- Enabling an augmentation via session state and clicking "Generate thumbnail" stores result
  in session state.
- Custom pipeline with 2 enabled augmentations runs and stores augmented image.
- "Augment" button in catalogue mode with no image shows warning.

#### Phase E — SessionStateManager updates

Add new typed keys to `SessionStateManager` for:
- `aug_mode: str` (default `"preset"`)
- `aug_catalogue_thumbnails: dict[str, bytes]`
- `aug_enabled_augs: set[str]`

#### Recommended file changes summary

| File | Change |
|---|---|
| `src/document_simulator/augmentation/catalogue.py` | New file — static catalogue metadata |
| `src/document_simulator/augmentation/augmenter.py` | Add `custom_augmentations` param |
| `src/document_simulator/ui/pages/01_augmentation_lab.py` | Add catalogue mode UI |
| `src/document_simulator/ui/state/session_state.py` | Add catalogue state keys |
| `tests/ui/integration/test_augmentation_lab_catalogue.py` | New test file |
| `docs/features/feature_ui_augmentation_lab.md` | Update with new acceptance criteria |

#### Key design principles to maintain

- No business logic in the page — the page calls `catalogue.apply_single()` and
  `AugraphyPipeline`; it does not import raw augmentation classes directly.
- Sliders in an expander per card — keeps the catalogue scannable by default.
- Preset path is untouched — existing tests continue to pass without modification.
- Thumbnail generation is lazy + cached — never block the full page render.
- The `@st.cache_data` thumbnail function takes `bytes` not `PIL.Image` as input to ensure
  correct Streamlit hashing.

---

### Sources

- [List of Augmentations — augraphy 8.2.0 documentation](https://augraphy.readthedocs.io/en/latest/doc/source/list_of_augmentations.html)
- [How Augraphy Works — augraphy 8.2.0 documentation](https://augraphy.readthedocs.io/en/latest/doc/source/how_augraphy_works.html)
- [Augraphy GitHub — sparkfish/augraphy](https://github.com/sparkfish/augraphy)
- [st.cache_data — Streamlit Docs](https://docs.streamlit.io/library/api-reference/performance/st.cache)
- [Caching overview — Streamlit Docs](https://docs.streamlit.io/develop/concepts/architecture/caching)
- [st.columns — Streamlit Docs](https://docs.streamlit.io/develop/api-reference/layout/st.columns)
- [Layouts and Containers — Streamlit Docs](https://docs.streamlit.io/develop/api-reference/layout)
- [streamlit-image-gallery (GitHub)](https://github.com/virtUOS/streamlit-image-gallery)
- [Defining Custom Pipelines in Augraphy — Sparkfish](https://www.sparkfish.com/augraphy-series-custom-pipelines/)

---

## 2026-03-08 — Augraphy Full Catalogue (28 Missing Classes)

Introspected constructor signatures for all 28 missing augraphy 8.2.6 classes.

### Ink Phase

| Class | Key Params |
|-------|-----------|
| `InkMottling` | `ink_mottling_alpha_range=(0.2,0.3)`, `ink_mottling_noise_scale_range=(2,2)`, `ink_mottling_gaussian_kernel_range=(3,5)` |
| `LowInkPeriodicLines` | `count_range=(2,5)`, `period_range=(10,30)`, `use_consistent_lines=True`, `noise_probability=0.1` |
| `LowInkRandomLines` | `count_range=(5,10)`, `use_consistent_lines=True`, `noise_probability=0.1` |
| `Hollow` | `hollow_median_kernel_value_range=(71,101)`, `hollow_min_width_range=(1,2)`, `hollow_max_width_range=(150,200)`, etc. |
| `Scribbles` | `scribbles_type='random'`, `scribbles_ink='random'`, `scribbles_size_range=(400,600)`, `scribbles_count_range=(1,6)`, `scribbles_thickness_range=(1,3)` |
| `LinesDegradation` | `line_roi=(0.0,0.0,1.0,1.0)`, `line_gradient_range=(32,255)`, `line_gradient_direction=(0,2)`, `line_split_probability=(0.2,0.4)` |
| `BindingsAndFasteners` | `overlay_types='random'`, `effect_type='random'`, `width_range='random'`, `height_range='random'`, `angle_range=(-30,30)`, `ntimes=(2,6)`, `nscales=(1.0,1.5)`, `edge='random'`, `edge_offset=(5,20)`, `use_figshare_library=0` |

### Paper Phase

| Class | Key Params |
|-------|-----------|
| `BrightnessTexturize` | `texturize_range=(0.8,0.99)`, `deviation=0.08` |
| `ColorPaper` | `hue_range=(28,45)`, `saturation_range=(10,40)` |
| `DirtyScreen` | `n_clusters=(50,100)`, `n_samples=(2,20)`, `std_range=(1,5)`, `value_range=(150,250)` |
| `Stains` | `stains_type='random'`, `stains_blend_method='darken'`, `stains_blend_alpha=0.5` |
| `NoisyLines` | `noisy_lines_direction='random'`, `noisy_lines_number_range=(5,20)`, `noisy_lines_thickness_range=(1,2)`, `noisy_lines_color=(0,0,0)` |
| `PatternGenerator` | `imgx=512`, `imgy=512`, `n_rotation_range=(10,15)`, `color='random'`, `alpha_range=(0.25,0.5)`, `numba_jit=1` |
| `DelaunayTessellation` | `n_points_range=(500,800)`, `n_horizontal_points_range=(500,800)`, `n_vertical_points_range=(500,800)`, `noise_type='random'` |
| `VoronoiTessellation` | `mult_range=(50,80)`, `seed=19829813472`, `num_cells_range=(500,1000)`, `noise_type='random'`, `background_value=(200,255)`, `numba_jit=1` |
| `PageBorder` | `page_border_width_height='random'`, `page_border_color=(0,0,0)`, `page_numbers='random'`, `page_rotation_angle_range=(-3,3)`, `numba_jit=1` |

### Post Phase

| Class | Key Params |
|-------|-----------|
| `DepthSimulatedBlur` | `blur_center='random'`, `blur_major_axes_length_range=(120,200)`, `blur_minor_axes_length_range=(120,200)`, `blur_iteration_range=(8,10)` |
| `DoubleExposure` | `gaussian_kernel_range=(9,12)`, `offset_direction='random'`, `offset_range=(18,25)` |
| `Faxify` | `scale_range=(1.0,1.25)`, `monochrome=-1`, `halftone=-1`, `numba_jit=1` |
| `LCDScreenPattern` | `pattern_type='random'`, `pattern_value_range=(0,16)`, `pattern_skip_distance_range=(3,5)`, `pattern_overlay_method='darken'` |
| `LensFlare` | `lens_flare_location='random'`, `lens_flare_color='random'`, `lens_flare_size=(0.5,5)`, `numba_jit=1` |
| `LightingGradient` | `max_brightness=255`, `min_brightness=0`, `mode='gaussian'`, `numba_jit=1` |
| `Moire` | `moire_density=(15,20)`, `moire_blend_method='normal'`, `moire_blend_alpha=0.1`, `numba_jit=1` |
| `ReflectedLight` | `reflected_light_smoothness=0.8`, `reflected_light_internal_radius_range=(0.0,0.2)`, `reflected_light_external_radius_range=(0.1,0.8)` |
| `DotMatrix` | `dot_matrix_shape='random'`, `dot_matrix_dot_width_range=(3,19)`, `dot_matrix_dot_height_range=(3,19)`, `numba_jit=1` |
| `Rescale` | `target_dpi=300` |
| `SectionShift` | `section_shift_number_range=(3,5)`, `section_shift_x_range=(-10,10)`, `section_shift_y_range=(-10,10)` |
| `Squish` | `squish_direction='random'`, `squish_number_range=(5,10)`, `squish_distance_range=(5,7)` |

### Notes

- `BindingsAndFasteners`: set `use_figshare_library=0` (int, not bool) to avoid network calls
- `numba_jit=0` required for: `PatternGenerator`, `VoronoiTessellation`, `PageBorder`, `Faxify`, `LensFlare`, `LightingGradient`, `Moire`, `DotMatrix`
- Slow augmentations (skip auto-thumbnails): `BindingsAndFasteners`, `PageBorder`, `VoronoiTessellation`, `DelaunayTessellation`

---

## 2026-03-12 — Streamlit to React Migration

### Goal

Migrate all 5 Streamlit pages (Augmentation Lab, OCR Engine, Batch Processing, Evaluation Dashboard, RL Training) into the existing React 18 + TypeScript + Vite SPA (`webapp/`) backed by the existing FastAPI server (`src/document_simulator/api/`).

### Existing Frontend Stack

- **React 18 + TypeScript + Vite** in `webapp/`
- **Konva / react-konva** for canvas drawing (zone editor)
- **No routing library** — currently a single-page app rendering `App.tsx` (the zone editor)
- **No charting library** — charts needed for CER/WER/confidence (Evaluation) and reward curve (RL Training)
- **API client** in `webapp/src/api/client.ts` using raw `fetch` against same-origin `/api/*`
- **Types** in `webapp/src/types/index.ts`

### Existing Backend Stack

- **FastAPI** app in `src/document_simulator/api/app.py`
- **Jobs module** in `src/document_simulator/api/jobs.py` — `create_job / get_job / update_job` with in-memory `JobState` dataclass
- **Synthesis router** (`src/document_simulator/api/routers/synthesis.py`) — handles template upload, preview, generate, download, samples
- **`python-multipart>=0.0.9`** already in `pyproject.toml` (required for file uploads)
- **`fastapi>=0.111.0`** already present

### Streamlit Pages — What Each Needs

#### 01 Augmentation Lab
- Preset selector: `light | medium | heavy` (from `PresetFactory`)
- Image/PDF upload
- Catalogue mode: pick individual augmentations and tune parameters (advanced)
- Before/after display (side-by-side)
- Download result as PNG or PDF

**FastAPI endpoints needed:**
- `GET /api/augmentation/presets` → `["light","medium","heavy","default"]`
- `POST /api/augmentation/augment` → multipart: `file` (image), `preset` (str) → `{"image_b64": str, "metadata": {...}}`

#### 02 OCR Engine
- Image/PDF upload
- Language selector, GPU checkbox
- Run OCR → annotated image with bboxes, text area, region table
- Optional ground truth .txt upload → CER/WER

**FastAPI endpoints needed:**
- `POST /api/ocr/recognize` → multipart: `file` (image), `lang` (str), `use_gpu` (bool) → `{"text": str, "boxes": [...], "scores": [...], "mean_confidence": float}`

#### 03 Batch Processing
- Multi-file upload
- Preset selector, worker count, mode (single/NxM/M-total)
- Start job, poll progress, download ZIP

**FastAPI endpoints needed:**
- `POST /api/batch/process` → multipart: `files` (list), `preset` (str), `mode` (str), `copies` (int), `total_outputs` (int), `seed` (int) → `{"job_id": str}`
- `GET /api/batch/jobs/{job_id}` → job status (reuse jobs module)
- `GET /api/batch/jobs/{job_id}/download` → ZIP StreamingResponse

#### 04 Evaluation Dashboard
- ZIP upload or local directory path
- Augmentation preset, GPU toggle
- Run evaluation → CER/WER/confidence metrics, bar charts, summary table

**FastAPI endpoints needed:**
- `POST /api/evaluation/run` → multipart: `zip_file` (optional), `dataset_dir` (optional str), `preset` (str) → `{"job_id": str}`
- `GET /api/evaluation/jobs/{job_id}` → job status + result metrics when done

#### 05 RL Training
- Dataset directory / ZIP upload
- Hyperparameter form (lr, batch_size, n_steps, num_envs, total_steps, ckpt_freq)
- Start/Stop training (background thread)
- Live reward chart updates

**FastAPI endpoints needed:**
- `POST /api/rl/train` → JSON body with config → `{"job_id": str}`
- `GET /api/rl/jobs/{job_id}/status` → `{status, progress, step, reward, error}`
- `GET /api/rl/jobs/{job_id}/metrics` → `{reward_curve: [{step, reward}], loss_curve: []}`

### Navigation Strategy

Add **React Router v6** (`react-router-dom`) to support multi-page navigation:
- `"/"` → Synthetic Generator (existing `App.tsx`)
- `"/augmentation"` → Augmentation Lab
- `"/ocr"` → OCR Engine
- `"/batch"` → Batch Processing
- `"/evaluation"` → Evaluation Dashboard
- `"/rl"` → RL Training

Add a persistent `<NavBar>` component rendered outside routes.

### Charting Library

**Recharts** (MIT, ~500KB gzipped 130KB) — chosen because:
- React-native (uses SVG, no D3 dependency)
- Simple `<BarChart>`, `<LineChart>` with declarative JSX matching existing React pattern
- Active maintenance, 22k GitHub stars
- Small bundle impact vs Plotly (5MB)

Alternative considered: **Chart.js + react-chartjs-2** — Canvas-based, slightly smaller, but less idiomatic for React.

### File Upload Handling

- React: `<input type="file" multiple>` with `FormData` sent to FastAPI
- FastAPI: `UploadFile` for single files; `List[UploadFile]` for batch
- Images decoded with PIL in Python, converted to base64 PNG for React display
- `python-multipart` already installed

### Background Tasks (Batch, Evaluation, RL)

- Pattern already established by synthesis router: `BackgroundTasks` + jobs module
- React polls `GET /api/*/jobs/{job_id}/status` every 2s while status is `running|pending`
- On `done`, enable download button
- RL training uses `threading.Thread` (same as Streamlit page) because SB3 PPO is not async-compatible

### Key Constraints

- OCR engine (`OCREngine`) is expensive to initialise — lazy-load as module-level singleton in the router, cached after first call
- SB3/PPO training: must run in a daemon thread; FastAPI `BackgroundTasks` spawns a thread anyway
- Batch augmentation: `BatchAugmenter` uses Python `multiprocessing` internally — safe to call from a background thread in FastAPI
- No streaming SSE needed — polling every 2s is sufficient given typical job durations (augmentation ~1-30s, OCR ~0.5-5s, evaluation ~30-300s, RL training ~minutes)

### Package.json Changes

Add to `webapp/package.json`:
```json
"react-router-dom": "^6.23.0",
"recharts": "^2.12.0"
```
Dev deps: `"@types/recharts"` is not needed — recharts ships its own TypeScript types since v2.


---

## 2026-03-12 — Free Hosting for JS App

### Context

The Document Simulator React SPA + FastAPI backend currently runs locally only. This section documents research into free hosting options to make the app publicly accessible.

### Options Evaluated

#### Frontend-only (React SPA)
- **Vercel / Netlify / Cloudflare Pages** — all free, excellent CDN, auto-deploy from GitHub. But require a separate backend host. CORS configuration needed.
- **GitHub Pages** — free, static only, needs a separate backend.

#### Backend (FastAPI + Python)
- **Render free tier** — supports Python/Docker but **spins down after 15 min of inactivity** (cold-start ~30s). Unacceptable for demo use.
- **Railway** — free trial ($5 credit) then paid. Not truly free.
- **Google Cloud Run** — free tier (2M requests/month) but cold-starts and complex setup.
- **Fly.io** — 3 free shared VMs, Docker, good Python support. Cold-start possible.

#### Full-Stack (Frontend + Backend in one container)
- **Hugging Face Spaces (Docker SDK)** ✅ **Recommended**
  - Free forever, no credit card required
  - 2 vCPUs, **16GB RAM** — enough for synthesis + augraphy
  - **No cold-start** — containers stay alive
  - Git-based deployment: `git push` → auto rebuild
  - ML/demo ecosystem — good for discovery
  - Port 7860 expected by default

### Decision: Hugging Face Spaces with Docker

Single Docker container serving both React SPA (as static files via FastAPI) and the Python API. Multi-stage Dockerfile: Node.js builds `webapp/dist/`, Python stage copies it and runs `uvicorn`.

**Excluded from Docker image:** `paddleocr`, `paddlepaddle`, `stable-baselines3`, `gymnasium` — these add ~2.5GB and are not needed for the synthesis demo.

### References
- [HF Spaces Docker docs](https://huggingface.co/docs/hub/spaces-sdks-docker)
- [Render free tier limitations](https://render.com/docs/free#free-web-services)
- [Fly.io free allowances](https://fly.io/docs/about/pricing/#free-allowances)
