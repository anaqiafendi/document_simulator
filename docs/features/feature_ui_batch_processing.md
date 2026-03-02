# Feature: UI — Batch Processing

> **GitHub Issue:** `#16`
> **Status:** `complete`
> **Module:** `document_simulator.ui.pages.03_batch_processing`

---

## Summary

A Streamlit page for uploading multiple images, selecting a preset and worker count, running parallel augmentation via `BatchAugmenter`, and downloading all results as a single ZIP archive. Throughput metrics (processed count, time, images/sec) are shown after the run.

---

## Motivation

### Problem Statement

`BatchAugmenter` can process hundreds of images in parallel, but requires scripting. A UI page makes this capability available to non-technical users who want to generate training data from a folder of scans.

### Value Delivered

- Multi-file upload with parallel augmentation in one click.
- Real-time throughput metrics after the run.
- ZIP download containing all augmented images with their original filenames.
- Parallel/sequential toggle and worker count slider for control.

---

## Acceptance Criteria

- [ ] AC-1: Page loads without error.
- [ ] AC-2: A "Run Batch" button is present.
- [ ] AC-3: A preset selectbox is present.
- [ ] AC-4: A worker count slider is present.
- [ ] AC-5: A "parallel" checkbox is present.
- [ ] AC-6: Clicking Run with no files shows a `st.warning`.
- [ ] AC-7: When `batch_results` and `batch_elapsed` are in session state, a "Processed" metric appears.

---

## Design

### Public API

No Python API — Streamlit page.

### Data Flow

```
User uploads multiple files → state.set_batch_inputs(pil_images)
User selects preset, workers, parallel toggle
User clicks "Run Batch"
    │
    ▼
BatchAugmenter(augmenter=preset, num_workers=n).augment_batch(images, parallel=parallel)
    │
    ▼
state.set_batch_results(augmented_images)
state.set_batch_elapsed(elapsed_seconds)
Compute metrics: processed, throughput
Build ZIP in-memory → st.download_button(data=zip_bytes)
```

### Key Interfaces

| Symbol | Kind | Responsibility |
|--------|------|---------------|
| Multi-file uploader | widget | `st.file_uploader(..., accept_multiple_files=True)` |
| Preset selectbox | widget | Maps to `BatchAugmenter(augmenter=preset)` |
| Worker slider | widget | `num_workers` parameter |
| Parallel checkbox | widget | `parallel=True/False` |
| Processed / Time / Throughput | metrics | Post-run summary |
| ZIP download button | widget | In-memory `zipfile.ZipFile` → bytes |

---

## Implementation

### Files

| Path | Role |
|------|------|
| `src/document_simulator/ui/pages/03_batch_processing.py` | Complete page |
| `src/document_simulator/augmentation/batch.py` | `BatchAugmenter` |
| `src/document_simulator/ui/state/session_state.py` | `SessionStateManager` |

### Key Architectural Decisions

1. **In-memory ZIP** — Results are packed into a `zipfile.ZipFile(BytesIO())` without writing to disk. This keeps the server stateless and avoids temp file cleanup.

2. **`batch_input_images` stored in state** — The list of input PIL Images is stored alongside results so the page can show thumbnail grids (up to 8 before/after pairs) without re-loading uploaded files.

3. **`parallel=False` in sequential mode** — The checkbox is exposed so users can debug augmentation issues by running sequentially (deterministic order, no subprocess forking, cleaner tracebacks).

### Known Edge Cases & Constraints

- `st.download_button` is not accessible as `at.download_button` in AppTest — tests check `at.metric` labels.
- Uploading many large images can exceed Streamlit's `server.maxUploadSize` (default 200 MB).
- Multiprocessing on macOS uses `spawn` — first batch job starts slowly due to process fork overhead.

---

## Tests

### Test Files

| File | Type | Count | What is covered |
|------|------|-------|-----------------|
| `tests/ui/integration/test_batch_processing.py` | integration | 8 | Load, Run button, preset selectbox, worker slider, parallel checkbox, warning on no files, metrics on results (2 cases) |

### TDD Cycle Summary

**Red — first failing tests written:**

| Test name | File | Initial failure reason |
|-----------|------|----------------------|
| `test_batch_page_loads` | `test_batch_processing.py` | `FileNotFoundError: 03_batch_processing.py does not exist` |
| `test_batch_page_has_parallel_checkbox` | `test_batch_processing.py` | Page existed but had no checkbox |
| `test_batch_page_shows_metrics_after_results_in_state` | `test_batch_processing.py` | `at.metric` was empty — results branch not rendering |

**Green — minimal implementation:**

Created page with file uploader, preset selectbox, worker slider, parallel checkbox, and Run button. Injected results via `at.session_state["batch_results"]` and `at.session_state["batch_elapsed"]`. Metrics appeared once the results branch was wired to check both keys.

**Refactor — improvements made after green:**

| What changed | Why |
|--------------|-----|
| Added `batch_input_images` to session state | The thumbnail grid required access to original images after the run; re-reading from `st.file_uploader` fails on rerun (Streamlit clears upload state) |
| Added ZIP creation from `batch_results` | `test_batch_page_shows_processed_metric_after_results` passed but users needed the actual download; added `zipfile.ZipFile` in the results branch |

### How to Run

```bash
uv run pytest tests/ui/integration/test_batch_processing.py -v
```

---

## Dependencies

### Requires

| Dependency | Kind | Why |
|------------|------|-----|
| `augmentation/batch.py` | internal | `BatchAugmenter` |
| `ui/components/file_uploader.py` | internal | `uploaded_files_to_pil` |
| `ui/state/session_state.py` | internal | `SessionStateManager` |
| `zipfile` | stdlib | In-memory ZIP creation |
| `io` | stdlib | `BytesIO` for ZIP |

---

## Future Work

- [ ] Add progress bar during augmentation (Streamlit's `st.progress`).
- [ ] Add thumbnail grid for first 8 before/after pairs.
- [ ] Add per-file error reporting when individual images fail.

---

## References

- [feature_batch_processing.md](feature_batch_processing.md)
- [UI_PLAN.md](../UI_PLAN.md)
