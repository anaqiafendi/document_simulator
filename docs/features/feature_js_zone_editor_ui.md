# Feature: React Zone Editor UI (DocuSign-Inspired)

> **GitHub Issue:** `#20`
> **Status:** `in-progress`
> **Module:** `document_simulator.api` + `webapp/` (React SPA)

---

## Summary

A DocuSign-inspired zone editor implemented as a React 18 single-page application served by a new FastAPI backend. Replaces the broken `streamlit-drawable-canvas`-based zone editor in `00_synthetic_generator.py` with a smooth, interactive canvas where users drag rectangles to define document zones, configure respondents and field types in side panels, and trigger synthetic document generation — all without Streamlit page reruns.

---

## Motivation

### Problem Statement

`streamlit-drawable-canvas` was archived on 2025-03-01 and is permanently incompatible with Streamlit >= 1.40 because Streamlit removed the `image_to_url` internal API. The `00_synthetic_generator.py` page crashes with `AttributeError` on every load. The community patch (`streamlit-drawable-canvas-fix`) is an unmaintained stopgap.

Beyond the immediate breakage, Streamlit's architecture is fundamentally unsuited for the DocuSign-like UX the feature demands:
- Every slider or dropdown change triggers a full Python rerun, making real-time canvas feedback laggy.
- `st_canvas` coordinates returned as JSON have no built-in support for resize handles, multi-select, or zone metadata.
- Preview image updates require re-running the entire page, not just the preview slot.

### Value Delivered

- Zone drawing on a live document canvas with no Python roundtrips (pure Konva JS).
- Respondent and field-type configuration in a persistent side panel — no accordion collapse on every interaction.
- Per-sample re-roll replaces exactly one preview image without regenerating the others.
- Full batch generation with real-time progress polling and one-click ZIP download.
- Five existing Streamlit pages (augmentation, OCR, batch, evaluation, RL) are completely untouched.
- The Python synthesis engine (`document_simulator.synthesis.*`) is untouched — the FastAPI layer is a thin HTTP wrapper.

---

## User Stories

| Role | Goal | So That |
|------|------|---------|
| Data engineer | I upload a blank invoice PDF and drag zones onto it | I configure 8 zones in under 2 minutes without writing code |
| Researcher | I adjust respondent ink colours and re-roll individual preview samples | I verify visual realism before committing to a 1,000-document batch run |
| Developer | I save the zone config to JSON and reload it | I reproduce the exact same synthetic dataset across machines |
| UI user | I click "Generate batch" and the ZIP downloads automatically when done | I get labelled document images without watching a progress spinner |

---

## Acceptance Criteria

- [ ] AC-1: `uv run python -m document_simulator.api` starts a uvicorn server; `GET http://localhost:8000/health` returns HTTP 200 within 5 seconds.
- [ ] AC-2: `POST /api/template` with a PNG returns HTTP 200 with `image_b64`, `width_px`, `height_px` fields.
- [ ] AC-3: `POST /api/template` with a PDF returns HTTP 200 with `is_pdf: true` and a base64 PNG rendered at 150 DPI.
- [ ] AC-4: `POST /api/preview` with a valid `SynthesisConfig` body returns HTTP 200 with a `samples` array of exactly 3 objects, each with `image_b64` and `seed`.
- [ ] AC-5: `POST /api/generate` with `n=5` returns HTTP 202 with `job_id`; polling `GET /api/jobs/{job_id}` eventually returns `status: "done"`; `GET /api/jobs/{job_id}/download` returns a ZIP with 5 PNGs and 5 JSONs, each JSON parseable by `GroundTruth.model_validate_json()`.
- [ ] AC-6: After `make build-frontend`, opening `http://localhost:8000` loads the React app without console errors.
- [ ] AC-7: Uploading a PNG in the React app renders it on the Konva stage background layer.
- [ ] AC-8: Drawing a rectangle on the Konva stage adds one entry to the zone list panel.
- [ ] AC-9: The respondent panel supports adding/removing respondents and field types via buttons.
- [ ] AC-10: The zone list panel shows a respondent selectbox and a field-type selectbox (filtered to the selected respondent) for each drawn zone.
- [ ] AC-11: Clicking "Preview" shows 3 preview images in a 3-column grid (fetched from `/api/preview`).
- [ ] AC-12: Each preview has a re-roll button that replaces only that slot's image with a new seed.
- [ ] AC-13: Clicking "Generate batch" polls progress and presents a "Download ZIP" link when complete.
- [ ] AC-14: The Streamlit page `00_synthetic_generator.py` shows a link to `http://localhost:8000` without error.
- [ ] AC-15: All existing Streamlit page tests (excluding the replaced `test_synthetic_generator.py` integration tests) pass unchanged.

---

## Design

### Public API

**Python API — FastAPI entry point:**

```python
# Start the API server
uv run python -m document_simulator.api
# → uvicorn listening on http://0.0.0.0:8000

# Or via installed script after uv sync:
document-simulator-api
```

**HTTP API surface:**

```
GET  /health                        → { status: "ok", version: "0.1.0" }
POST /api/template                  → TemplateResponse (base64 PNG + dimensions)
POST /api/preview                   → PreviewResponse (3× base64 PNG)
POST /api/generate                  → { job_id: str }          [202 Accepted]
GET  /api/jobs/{job_id}             → JobStatusResponse
GET  /api/jobs/{job_id}/download    → StreamingResponse (ZIP)
GET  /api/config/schema             → JSON Schema of SynthesisConfig
GET  /                              → React SPA (StaticFiles from webapp/dist/)
```

### Data Flow

```
USER                         REACT SPA (:8000)              FASTAPI (:8000)        PYTHON ENGINE
 │                                │                               │                      │
 │── uploads PDF/PNG ────────►    TemplateUploader                │                      │
 │                                │── POST /api/template ────────►│                      │
 │                                │                               │── fitz / Pillow      │
 │                                │◄── { image_b64, w, h } ──────│                      │
 │◄── image on Konva stage ───────│                               │                      │
 │                                │                               │                      │
 │── draws rect on canvas ───────►│ onZoneDrawn(zone)             │                      │
 │                                │ zones.push(zone)              │                      │
 │◄── zone in ZoneList ───────────│                               │                      │
 │                                │                               │                      │
 │── configures respondents ─────►│ respondents state updated     │                      │
 │                                │                               │                      │
 │── clicks "Preview" ───────────►│                               │                      │
 │                                │── POST /api/preview ─────────►│                      │
 │                                │   { synthesis_config,         │                      │
 │                                │     seeds: [42,43,44] }       │── generate_one(42)   │
 │                                │◄── { samples: [b64×3] } ──────│── generate_one(43)   │
 │◄── 3 preview images ───────────│                               │── generate_one(44)   │
 │                                │                               │                      │
 │── re-rolls sample #2 ─────────►│── POST /api/preview ─────────►│── generate_one(1043) │
 │◄── sample #2 replaced ─────────│◄── { samples: [b64×1] } ──────│                      │
 │                                │                               │                      │
 │── clicks "Generate" ──────────►│── POST /api/generate ────────►│ BackgroundTask       │
 │                                │◄── { job_id } ────────────────│── generate(n) ───────►
 │◄── progress polling ───────────│── GET /api/jobs/{id} ─────────►│◄─ progress cb ──────│
 │◄── "Download ZIP" ─────────────│── GET /api/jobs/{id}/download ►│── StreamingResponse  │
```

### Key Interfaces

| Symbol | Kind | Responsibility |
|--------|------|---------------|
| `document_simulator.api.app:app` | FastAPI app | ASGI application; mounts routes + StaticFiles |
| `document_simulator.api.routers.synthesis` | router | All `/api/*` route handlers |
| `document_simulator.api.models.TemplateResponse` | Pydantic | API response schema for template upload |
| `document_simulator.api.models.PreviewRequest` | Pydantic | API request schema for preview generation |
| `document_simulator.api.models.PreviewResponse` | Pydantic | API response schema for preview generation |
| `document_simulator.api.models.GenerateRequest` | Pydantic | API request schema for batch generation |
| `document_simulator.api.jobs.JobStore` | class | In-memory job state tracker (dict-based) |
| `webapp/src/components/ZoneCanvas.tsx` | React component | Konva stage; zone drawing + selection |
| `webapp/src/components/RespondentPanel.tsx` | React component | Respondent and field-type CRUD UI |
| `webapp/src/components/ZoneList.tsx` | React component | Per-zone configuration (label, respondent, faker provider) |
| `webapp/src/components/PreviewGallery.tsx` | React component | 3-column preview grid with re-roll buttons |
| `webapp/src/components/BatchGeneratePanel.tsx` | React component | Batch generation trigger, progress, ZIP download |
| `webapp/src/api/client.ts` | TS module | Typed async fetch wrappers for all API endpoints |
| `webapp/src/hooks/useZones.ts` | React hook | Zone list CRUD state management |
| `webapp/src/hooks/useRespondents.ts` | React hook | Respondent and field-type state management |
| `webapp/src/hooks/usePreviews.ts` | React hook | Preview fetch, loading state, re-roll logic |
| `webapp/src/hooks/useGenerate.ts` | React hook | Batch generate call, job polling, download trigger |

### Configuration

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `API_HOST` | `str` | `0.0.0.0` | Host for uvicorn bind |
| `API_PORT` | `int` | `8000` | Port for uvicorn bind |
| `MAX_UPLOAD_BYTES` | `int` | `20971520` | Max template upload size (20 MB) |

---

## Implementation

### Files

**Python — New:**

| Path | Role |
|------|------|
| `src/document_simulator/api/__init__.py` | Package init; exports `app`, `run()` for uvicorn |
| `src/document_simulator/api/__main__.py` | Enables `python -m document_simulator.api` |
| `src/document_simulator/api/app.py` | FastAPI application factory: CORS, router registration, StaticFiles mount |
| `src/document_simulator/api/routers/__init__.py` | Router package init |
| `src/document_simulator/api/routers/synthesis.py` | All `/api/*` route handlers |
| `src/document_simulator/api/models.py` | Pydantic request/response models for the API layer |
| `src/document_simulator/api/jobs.py` | In-memory job store: `create_job`, `get_job`, `set_result` |
| `tests/api/__init__.py` | Test package init |
| `tests/api/conftest.py` | Shared fixtures: `client`, `minimal_synthesis_config`, `tiny_png_bytes`, `minimal_pdf_bytes` |
| `tests/api/test_health.py` | Tests for `GET /health` |
| `tests/api/test_template_endpoint.py` | Tests for `POST /api/template` (PNG and PDF) |
| `tests/api/test_preview_endpoint.py` | Tests for `POST /api/preview` |
| `tests/api/test_generate_endpoint.py` | Tests for `POST /api/generate` + job polling + download |
| `tests/api/test_config_schema_endpoint.py` | Tests for `GET /api/config/schema` |

**Python — Modified:**

| Path | Role |
|------|------|
| `pyproject.toml` | Add `fastapi`, `uvicorn[standard]`, `python-multipart`; remove `streamlit-drawable-canvas`, `streamlit-image-coordinates`; add `document-simulator-api` script |
| `src/document_simulator/ui/pages/00_synthetic_generator.py` | Replace 989-line broken page with 6-line redirect stub |
| `tests/ui/integration/test_synthetic_generator.py` | Update to assert stub content (link present, no exception) |

**JavaScript/TypeScript — New (`webapp/`):**

| Path | Role |
|------|------|
| `webapp/package.json` | npm project; React 18, react-konva, Vite, TypeScript |
| `webapp/vite.config.ts` | Vite config: output to `webapp/dist/`, dev proxy `/api` → `localhost:8000` |
| `webapp/tsconfig.json` | TypeScript strict config |
| `webapp/index.html` | Vite HTML entrypoint |
| `webapp/src/main.tsx` | React 18 `createRoot` entrypoint |
| `webapp/src/App.tsx` | Root component; top-level state; 4-panel layout |
| `webapp/src/types/index.ts` | Shared TypeScript types mirroring Python Pydantic models |
| `webapp/src/api/client.ts` | Typed async fetch wrappers |
| `webapp/src/hooks/useTemplate.ts` | Template upload + server render hook |
| `webapp/src/hooks/useZones.ts` | Zone list CRUD hook |
| `webapp/src/hooks/useRespondents.ts` | Respondent + field-type CRUD hook |
| `webapp/src/hooks/usePreviews.ts` | Preview fetch + re-roll hook |
| `webapp/src/hooks/useGenerate.ts` | Batch generate + job polling + download hook |
| `webapp/src/components/TemplateUploader.tsx` | File input; calls `useTemplate`; renders loading spinner |
| `webapp/src/components/ZoneCanvas.tsx` | Konva Stage + Layers; draw mode + select mode |
| `webapp/src/components/ZoneList.tsx` | Per-zone config: label, respondent, field-type, faker provider, delete |
| `webapp/src/components/RespondentPanel.tsx` | Respondent and field-type CRUD with colour, font, fill-style controls |
| `webapp/src/components/InkColorPicker.tsx` | 5 preset swatches + free colour input |
| `webapp/src/components/PreviewGallery.tsx` | 3-column preview grid + re-roll buttons |
| `webapp/src/components/BatchGeneratePanel.tsx` | n input, generate button, progress, ZIP download |
| `webapp/src/components/ConfigPanel.tsx` | Save/load `SynthesisConfig` as JSON |
| `webapp/src/components/StatusBar.tsx` | Server health status indicator |
| `webapp/.gitignore` | Ignores `node_modules/`, `dist/` |
| `Makefile` | Targets: `build-frontend`, `dev-api`, `dev-ui` |

### Key Architectural Decisions

1. **FastAPI serves both the REST API and the React SPA from port 8000** — `StaticFiles` is mounted at `/` as a fallback after all API routes are registered. This means `make build-frontend` is a prerequisite for production; during development, Vite dev server proxies `/api` to FastAPI.

2. **Server-side PDF rendering via PyMuPDF** — `TemplateLoader` in `synthesis/template.py` already renders PDFs to PIL Images. The `/api/template` endpoint reuses this exact path, returns a base64 PNG, and the React app displays a plain `<img>` tag behind the Konva stage. This avoids the `pdfjs-dist` worker setup and large bundle size entirely.

3. **Background task with in-memory job store for batch generation** — FastAPI `BackgroundTasks` runs the generation in a thread pool, allowing the HTTP response to return immediately (202 Accepted). The job store is a module-level `dict` — single-process only, adequate for dev/local use. Documented limitation.

4. **`streamlit-drawable-canvas` removed entirely** — not patched with `streamlit-drawable-canvas-fix`. The community patch is unmaintained and will break again. The React SPA is the permanent replacement.

5. **React 18 + react-konva for the canvas** — Konva provides declarative `<Rect>` / `<Transformer>` components with built-in drag, resize, and hit detection. No custom canvas event handling required. Fabric.js was considered but lacks a first-class React binding.

6. **HiDPI scaling applied in `ZoneCanvas.tsx`** — `window.devicePixelRatio` scaling must be applied at initialisation to prevent blurry zones on Retina displays and to ensure pixel-accurate coordinate mapping.

7. **Zone coordinates stored in document pixels, not CSS pixels** — the Konva stage may be displayed at a different CSS size than the actual document. A scaling formula (`doc_x = canvas_x / display_scale`) is applied in `ZoneCanvas.tsx` before emitting `onZoneDrawn` and inverted when rendering loaded zones back onto the canvas.

### Known Edge Cases & Constraints

- Job store is in-process memory; running `uvicorn --workers 2` will lose job state across workers. Run single-process (`--workers 1`) for MVP.
- Template upload is capped at 20 MB; larger PDFs return HTTP 413.
- Preview generation runs 3 `generate_one` calls synchronously in the route handler. For templates with many zones or heavy Augraphy config, this may be slow (> 3 seconds). Document the limitation; move to background task if profiling warrants it.
- `webapp/dist/` is NOT committed to the repository; `make build-frontend` must be run before starting the API server in production mode.
- Konva coordinate accuracy depends on correct HiDPI scaling; if `devicePixelRatio` is ignored, zone bounding boxes in annotations will be offset by a factor of 1.5× or 2× on Retina displays.

---

## Tests

### Test Files

| File | Type | Count | What is covered |
|------|------|-------|-----------------|
| `tests/api/test_health.py` | unit | 2 | `GET /health` response code and body |
| `tests/api/test_template_endpoint.py` | unit | 8 | PNG upload, PDF upload, unsupported type, empty file |
| `tests/api/test_preview_endpoint.py` | unit | 6 | Returns 3 samples, custom seeds, invalid config, zero zones |
| `tests/api/test_generate_endpoint.py` | integration | 9 | 202 response, job polling, download ZIP contents, GroundTruth validity |
| `tests/api/test_config_schema_endpoint.py` | unit | 3 | Schema is valid JSON, contains expected fields |
| `tests/ui/integration/test_synthetic_generator.py` | integration | TBD | Updated to assert stub content (link present, no exception) |

### TDD Cycle Summary

**Red — first failing tests written:**

| Test name | File | Initial failure reason |
|-----------|------|----------------------|
| `test_health_returns_200` | `tests/api/test_health.py` | `ImportError: cannot import name 'app' from 'document_simulator.api.app'` |
| `test_post_template_png_returns_200` | `tests/api/test_template_endpoint.py` | `404 Not Found` — route not registered |
| `test_post_preview_returns_exactly_3_samples` | `tests/api/test_preview_endpoint.py` | `404 Not Found` — route not registered |
| `test_post_generate_returns_202` | `tests/api/test_generate_endpoint.py` | `404 Not Found` — route not registered |
| `test_get_config_schema_returns_200` | `tests/api/test_config_schema_endpoint.py` | `404 Not Found` — route not registered |

**Green — minimal implementation:**

Register the FastAPI app with `@app.get("/health")` returning `{"status": "ok"}`, then add each router module with the minimum code to satisfy the test (correct status code + response shape). For generate, use a synchronous stub that builds a ZIP from a single dummy image before wiring in `BackgroundTasks`.

**Refactor — improvements made after green:**

| What changed | Why |
|--------------|-----|
| Extract `_render_template_bytes(file, dpi, page)` helper | Reused by both `/api/template` and preview generation |
| Replace synchronous generate stub with `BackgroundTasks` | Allows 202 immediate response for large batches |
| Add `MAX_UPLOAD_BYTES` guard to `/api/template` | Prevents OOM on very large PDF uploads |

### How to Run

```bash
# All API tests
uv run pytest tests/api/ -v

# Single test
uv run pytest tests/api/test_template_endpoint.py::test_post_template_pdf_returns_200 -v

# With coverage
uv run pytest tests/api/ --cov=document_simulator.api

# Updated Streamlit stub test
uv run pytest tests/ui/integration/test_synthetic_generator.py -v
```

### Bugs Fixed Post-Implementation

None.

---

## Dependencies

### Requires

| Dependency | Kind | Why |
|------------|------|-----|
| `fastapi>=0.111.0` | external | HTTP framework; Pydantic-native request/response models |
| `uvicorn[standard]>=0.30.0` | external | ASGI server for FastAPI |
| `python-multipart>=0.0.9` | external | Required by FastAPI for `UploadFile` multipart form parsing |
| `document_simulator.synthesis.*` | internal | Generator, TemplateLoader, SynthesisConfig — the engine being exposed |
| `pymupdf` (fitz) | external (already dep) | Server-side PDF rendering in `/api/template` |
| `react` 18 | external JS | UI framework |
| `react-konva` | external JS | Canvas zone drawing |
| `konva` | external JS | Canvas engine underpinning react-konva |
| `vite` | external JS (dev) | Build tool and dev server |

### Required By

| Consumer | How it uses this feature |
|----------|------------------------|
| `webapp/src/api/client.ts` | Calls all REST endpoints |
| `src/document_simulator/ui/pages/00_synthetic_generator.py` (stub) | Links to `http://localhost:8000` |

---

## Usage Examples

### Minimal — start the API

```bash
# Install deps (adds fastapi, uvicorn, python-multipart)
uv sync

# Build the React frontend
make build-frontend

# Start the API + SPA on port 8000
uv run python -m document_simulator.api
# → open http://localhost:8000 in browser
```

### Typical — run API + Streamlit together

```bash
# Terminal 1: API + React SPA
uv run python -m document_simulator.api

# Terminal 2: Streamlit (5 existing pages unchanged)
uv run streamlit run src/document_simulator/ui/app.py
# → http://localhost:8501
# → "Synthetic Document Generator" page now shows a link to http://localhost:8000
```

### Advanced — React dev server with hot reload

```bash
# Terminal 1: FastAPI only (no static files needed in dev mode)
uv run python -m document_simulator.api

# Terminal 2: Vite dev server (proxies /api to localhost:8000)
cd webapp && npm run dev
# → http://localhost:5173 with hot module replacement
```

---

## Future Work

- [ ] Option B for preview: accept the template image in `/api/preview` so preview samples show the real document background, not a blank canvas.
- [ ] `webapp/dist/` included in wheel or Docker image so no Node.js build step is needed for deployment.
- [ ] JS component tests (Vitest + React Testing Library) for `ZoneCanvas`, `RespondentPanel`, and `ZoneList`.
- [ ] Konva zone coordinate unit tests (verify doc-pixel ↔ CSS-pixel conversion at common `devicePixelRatio` values).
- [ ] Redis-backed job store for multi-worker uvicorn deployments.
- [ ] Async preview endpoint using `BackgroundTasks` if 3-sample latency exceeds 3 seconds in practice.
- [ ] PDF AcroForm auto-detection to suggest zone placement from an existing form's field widgets.
- [ ] Dark mode for the React SPA.

---

## References

- [feature_synthetic_document_generator.md](feature_synthetic_document_generator.md)
- [docs/RESEARCH_FINDINGS.md](../RESEARCH_FINDINGS.md)
- [react-konva documentation](https://konvajs.org/docs/react/index.html)
- [FastAPI StaticFiles](https://fastapi.tiangolo.com/tutorial/static-files/)
- [streamlit-drawable-canvas issue #157](https://github.com/andfanilo/streamlit-drawable-canvas/issues/157)
