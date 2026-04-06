# Feature: Migrate Streamlit Pages to React SPA + FastAPI

> **GitHub Issue:** `#24`
> **Status:** `complete`
> **Module:** `document_simulator.api.routers.*` + `webapp/src/pages/*`

---

## Summary

Migrates all 5 Streamlit UI pages (Augmentation Lab, OCR Engine, Batch Processing, Evaluation Dashboard, RL Training) into the existing React 18 + TypeScript + Vite SPA, backed by new FastAPI routers. The Streamlit UI is kept as a legacy fallback; the React SPA becomes the primary interface for all document-simulator workflows.

---

## Motivation

### Problem Statement

The Streamlit pages are functional but architecturally mismatched with the React SPA that was introduced for the zone editor (feature #20). Users must run two separate servers (Streamlit on :8501, FastAPI on :8000) and switch between two different UIs. This creates:

- Split user experience: zone editor in React, everything else in Streamlit
- Duplicate launch complexity: two processes, two ports
- Inconsistent styling: Streamlit's widget look vs the React SPA
- Streamlit reruns on every interaction causing slow feedback for image-heavy workflows

### Value Delivered

- Single unified React SPA for all document-simulator workflows
- All 5 pages accessible from a persistent navigation sidebar/header
- FastAPI endpoints reusable by other clients (CLI, tests, external tools)
- Recharts for lightweight, React-native CER/WER and reward visualisation
- Background-task pattern (already used by synthesis) extended to batch, evaluation, and RL training

---

## User Stories

| Role | Goal | So That |
|------|------|---------|
| Data engineer | I upload a document image and apply a preset augmentation in the React UI | I get a before/after view without switching to a separate Streamlit server |
| Researcher | I run OCR on a document and see bounding box overlays with confidence scores | I can inspect OCR quality without running the Streamlit page |
| Data engineer | I batch-augment 50 documents in the React UI and download the ZIP | I process a full dataset without the Streamlit page |
| Researcher | I evaluate CER/WER across a labelled dataset and see bar charts | I measure augmentation impact without Streamlit |
| ML engineer | I launch PPO training from the React UI and watch the reward curve update | I monitor RL training without the Streamlit page |

---

## Acceptance Criteria

- [x] AC-1: `GET /api/augmentation/presets` returns HTTP 200 with `["light","medium","heavy","default"]`
- [x] AC-2: `POST /api/augmentation/augment` with a PNG + preset returns HTTP 200 with `image_b64` and `metadata` fields
- [x] AC-3: `POST /api/ocr/recognize` with a PNG returns HTTP 200 with `text`, `boxes`, `scores`, `mean_confidence`
- [x] AC-4: `POST /api/batch/process` starts a background job; `GET /api/batch/jobs/{id}` eventually returns `status: "done"`; `GET /api/batch/jobs/{id}/download` returns a ZIP
- [x] AC-5: `POST /api/evaluation/run` starts a background job; when done, `GET /api/evaluation/jobs/{id}/status` returns CER/WER metrics in the result
- [x] AC-6: `POST /api/rl/train` starts training in a daemon thread; `GET /api/rl/jobs/{id}/status` returns progress; `GET /api/rl/jobs/{id}/metrics` returns `reward_curve`
- [x] AC-7: React Router routes `/`, `/augmentation`, `/ocr`, `/batch`, `/evaluation`, `/rl` all render without 404
- [x] AC-8: A persistent nav bar links all 6 pages; active page is highlighted
- [x] AC-9: Augmentation Lab page: preset dropdown, image upload, before/after display, download button
- [x] AC-10: OCR Engine page: image upload, Run OCR button, annotated image display, text output, region table
- [x] AC-11: Batch Processing page: multi-file upload, preset/mode selector, progress bar, download ZIP button
- [x] AC-12: Evaluation page: ZIP upload, Run Evaluation button, Recharts bar chart for CER/WER, summary table
- [x] AC-13: RL Training page: config form, Start/Stop buttons, polling progress bar, Recharts reward line chart
- [x] AC-14: All existing API tests pass unchanged after new routers are registered
- [x] AC-15: New API test files (`tests/api/test_augmentation_router.py`, `tests/api/test_ocr_router.py`, `tests/api/test_batch_router.py`) all pass

---

## Design

### Public API

```
# Augmentation
GET  /api/augmentation/presets
POST /api/augmentation/augment       multipart: file, preset

# OCR
POST /api/ocr/recognize              multipart: file, lang, use_gpu

# Batch
POST /api/batch/process              multipart: files[], preset, mode, copies, total_outputs, seed
GET  /api/batch/jobs/{job_id}
GET  /api/batch/jobs/{job_id}/download

# Evaluation
POST /api/evaluation/run             multipart: zip_file (opt), dataset_dir (opt), preset
GET  /api/evaluation/jobs/{job_id}/status

# RL Training
POST /api/rl/train                   JSON: {lr, batch_size, n_steps, num_envs, total_steps, ckpt_freq, dataset_dir}
GET  /api/rl/jobs/{job_id}/status
GET  /api/rl/jobs/{job_id}/metrics
```

### Data Flow

```
React Page (TypeScript)
    │  fetch/FormData
    ▼
FastAPI Router (Python)
    │  import from document_simulator.*
    ▼
Background Thread / BackgroundTask
    │  update_job(job_id, ...)
    ▼
Jobs Store (in-memory)
    │  polled by React every 2s
    ▼
React Page: progress bar → download or chart
```

### Component Tree

```
main.tsx
└── BrowserRouter
    ├── NavBar (persistent)
    └── Routes
        ├── /                  → <App>           (existing zone editor)
        ├── /augmentation      → <AugmentationLab>
        │   ├── PresetDropdown
        │   ├── FileUploadInput
        │   └── BeforeAfterDisplay
        ├── /ocr               → <OcrEngine>
        │   ├── FileUploadInput
        │   ├── OcrCanvas (bbox overlay)
        │   └── RegionTable
        ├── /batch             → <BatchProcessing>
        │   ├── MultiFileInput
        │   ├── ModeSelector
        │   └── JobPoller
        ├── /evaluation        → <Evaluation>
        │   ├── DatasetInput
        │   ├── JobPoller
        │   └── MetricsBarChart (Recharts)
        └── /rl                → <RlTraining>
            ├── ConfigForm
            ├── JobPoller
            └── RewardLineChart (Recharts)
```

### Key Interfaces

| Symbol | Kind | Responsibility |
|--------|------|---------------|
| `AugmentResult` | TypeScript interface | `{image_b64, metadata}` from `/api/augmentation/augment` |
| `OcrResult` | TypeScript interface | `{text, boxes, scores, mean_confidence}` from `/api/ocr/recognize` |
| `BatchJobRequest` | TypeScript interface | multipart form fields for `/api/batch/process` |
| `EvalMetrics` | TypeScript interface | CER/WER/confidence stats returned when eval job done |
| `RlMetrics` | TypeScript interface | `{reward_curve: [{step,reward}]}` |
| `augmentationRouter` | FastAPI APIRouter | `/api/augmentation/*` |
| `ocrRouter` | FastAPI APIRouter | `/api/ocr/*` |
| `batchRouter` | FastAPI APIRouter | `/api/batch/*` |
| `evaluationRouter` | FastAPI APIRouter | `/api/evaluation/*` |
| `rlTrainingRouter` | FastAPI APIRouter | `/api/rl/*` |

### Configuration

No new `.env` settings. Existing settings (`PADDLEOCR_USE_GPU`, etc.) are respected.

---

## Implementation

### Files

| Path | Role |
|------|------|
| `src/document_simulator/api/routers/augmentation.py` | Augmentation preset list + augment endpoint |
| `src/document_simulator/api/routers/ocr.py` | OCR recognize endpoint |
| `src/document_simulator/api/routers/batch.py` | Batch augmentation job endpoints |
| `src/document_simulator/api/routers/evaluation.py` | Evaluation job endpoints |
| `src/document_simulator/api/routers/rl_training.py` | RL training job endpoints |
| `src/document_simulator/api/app.py` | Register 5 new routers |
| `src/document_simulator/api/models.py` | New request/response Pydantic models |
| `webapp/src/pages/AugmentationLab.tsx` | Augmentation Lab React page |
| `webapp/src/pages/OcrEngine.tsx` | OCR Engine React page |
| `webapp/src/pages/BatchProcessing.tsx` | Batch Processing React page |
| `webapp/src/pages/Evaluation.tsx` | Evaluation Dashboard React page |
| `webapp/src/pages/RlTraining.tsx` | RL Training React page |
| `webapp/src/components/NavBar.tsx` | Persistent navigation bar |
| `webapp/src/App.tsx` | Add BrowserRouter + NavBar + Routes |
| `webapp/src/main.tsx` | Unchanged |
| `webapp/src/api/client.ts` | New API client functions |
| `webapp/src/types/index.ts` | New TypeScript types |
| `webapp/package.json` | Add react-router-dom, recharts |
| `tests/api/test_augmentation_router.py` | Augmentation endpoint tests |
| `tests/api/test_ocr_router.py` | OCR endpoint tests |
| `tests/api/test_batch_router.py` | Batch endpoint tests |

### Key Architectural Decisions

1. **OCR lazy singleton** — `OCREngine` is expensive to initialise (loads PaddleOCR model ~2-5s). A module-level `_ocr_engine: OCREngine | None = None` singleton is created on first request. Subsequent requests reuse it. Lang and GPU settings are fixed at first-call time; changing them requires a server restart (acceptable for a dev tool).

2. **Jobs module reuse** — All background jobs (batch, evaluation, RL) reuse the existing `document_simulator.api.jobs` module (`create_job / get_job / update_job`). Job IDs are UUIDs. Result bytes (ZIPs) stored in memory; large results could exhaust memory in edge cases but are acceptable for a dev tool.

3. **Polling not SSE** — React pages poll every 2 seconds while a job is running. SSE/WebSocket would give tighter latency but adds complexity. 2s polling is sufficient given typical job durations.

4. **Recharts not Plotly** — Recharts is ~130KB gzipped vs Plotly's ~5MB. The React frontend already avoids heavy dependencies; Recharts aligns with that philosophy. Python-side Plotly (used in Streamlit) is not replicated in React.

5. **React Router in `App.tsx`** — `BrowserRouter` wraps the existing `App` component. The existing zone editor code is moved to a route component. `NavBar` is rendered outside `<Routes>` to persist across page changes.

### Known Edge Cases & Constraints

- OCR is slow on CPU; React page shows a spinner but there is no streaming progress for single-image OCR
- Batch augmentation uses Python `multiprocessing` — may conflict with some thread/fork configurations on macOS; `num_workers=1` is a safe fallback
- RL training job stores reward log in memory (`update_job` with extra fields) — `JobState` is extended with `training_log: list[dict]`
- Evaluation requires a dataset directory or ZIP; ZIP is extracted to a `tempfile.TemporaryDirectory` that is deleted when the Python process cleans up

---

## Tests

### Test Files

| File | Type | Count | What is covered |
|------|------|-------|-----------------|
| `tests/api/test_augmentation_router.py` | unit | 4 | presets endpoint, augment endpoint happy path, missing file 422, invalid preset 422 |
| `tests/api/test_ocr_router.py` | unit | 3 | recognize endpoint happy path, missing file 422, response shape |
| `tests/api/test_batch_router.py` | unit | 4 | process endpoint returns job_id, status polling, download before done returns 404, job store |

### TDD Cycle Summary

**Red — first failing tests written:**

| Test name | File | Initial failure reason |
|-----------|------|----------------------|
| `test_presets_returns_list` | `tests/api/test_augmentation_router.py` | `ImportError: cannot import augmentation router` |
| `test_augment_returns_image_b64` | `tests/api/test_augmentation_router.py` | `404 Not Found` |
| `test_ocr_recognize_returns_text` | `tests/api/test_ocr_router.py` | `ImportError: cannot import ocr router` |
| `test_batch_process_returns_job_id` | `tests/api/test_batch_router.py` | `ImportError: cannot import batch router` |

**Green — minimal implementation:**

Each router file is created with the minimum endpoint implementation. `OCREngine` is lazy-loaded to avoid import-time PaddleOCR initialisation.

**Refactor — improvements made after green:**

| What changed | Why |
|--------------|-----|
| Extracted `_lazy_ocr_engine()` helper | Avoid re-loading engine on every request |
| Used `threading.Thread` for RL training | `BackgroundTasks` runs in the request thread for sync functions; RL training must not block |

### How to Run

```bash
# All API tests
uv run pytest tests/api/ -q --no-cov

# New router tests only
uv run pytest tests/api/test_augmentation_router.py tests/api/test_ocr_router.py tests/api/test_batch_router.py -v --no-cov

# Full test suite
uv run pytest tests/ -q --no-cov
```

---

## Dependencies

### Requires

| Dependency | Kind | Why |
|------------|------|-----|
| `react-router-dom ^6` | external (npm) | Multi-page routing in React SPA |
| `recharts ^2` | external (npm) | Bar/Line charts for metrics visualisation |
| `document_simulator.augmentation` | internal | Augmentation Lab endpoint |
| `document_simulator.ocr` | internal | OCR endpoint |
| `document_simulator.augmentation.batch` | internal | Batch processing endpoint |
| `document_simulator.evaluation` | internal | Evaluation endpoint |
| `document_simulator.rl` | internal | RL training endpoint |
| `document_simulator.api.jobs` | internal | Background job tracking |

### Required By

| Consumer | How it uses this feature |
|----------|------------------------|
| React SPA pages | HTTP fetch to FastAPI endpoints |
| Future CLI clients | FastAPI endpoints are reusable |

---

## Usage Examples

### Minimal (curl)

```bash
# List presets
curl http://localhost:8000/api/augmentation/presets

# Augment an image
curl -X POST http://localhost:8000/api/augmentation/augment \
  -F "file=@document.png" -F "preset=light"
```

### React (TypeScript)

```typescript
import { augmentImage, listPresets } from './api/client'

const presets = await listPresets()           // ["light","medium","heavy","default"]
const result = await augmentImage(file, 'medium')
// result.image_b64 → display in <img src={`data:image/png;base64,${result.image_b64}`} />
```

---

## Future Work

- [ ] Add SSE/WebSocket streaming for live OCR progress on large PDFs
- [ ] Add per-augmentation parameter sliders in the React UI (Catalogue mode equivalent)
- [ ] Add GPU toggle in OCR page (currently fixed at first-call time)
- [ ] Add evaluation results download (CSV export)
- [ ] Persist job results beyond in-memory store (Redis or SQLite)

---

## References

- [Research Findings — Streamlit to React Migration](../RESEARCH_FINDINGS.md#2026-03-12--streamlit-to-react-migration)
- [React Zone Editor UI FDD](feature_js_zone_editor_ui.md)
- [React Router v6 docs](https://reactrouter.com/en/main)
- [Recharts docs](https://recharts.org/en-US)
