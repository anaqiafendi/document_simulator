# Feature: UI — OCR Engine

> **GitHub Issue:** `#15`
> **Status:** `complete`
> **Module:** `document_simulator.ui.pages.02_ocr_engine`

---

## Summary

A Streamlit page that lets a user upload a document image, select a language and GPU option, click Run OCR, and see extracted text overlaid with confidence-coloured bounding boxes, per-region metrics, optional CER/WER vs a ground-truth file, and a text download button.

---

## Motivation

### Problem Statement

`OCREngine.recognize()` returns a dict that is useful programmatically but not visually. A UI page that draws bounding boxes, displays confidence per region, and computes CER/WER against a reference lets users evaluate OCR quality interactively without writing code.

### Value Delivered

- Visual bounding box overlay colour-coded by confidence.
- Mean confidence, region count, CER, and WER as metric widgets.
- Per-region table (text, confidence, bounding box top-left).
- Optional ground-truth `.txt` upload for CER/WER computation.
- "Clear engine cache" button to evict the Streamlit-cached `OCREngine` after code changes.

---

## Acceptance Criteria

- [ ] AC-1: Page loads without error.
- [ ] AC-2: "Run OCR" button is present.
- [ ] AC-3: Language selectbox includes `"en"` as an option.
- [ ] AC-4: Clicking Run OCR with no image shows a `st.warning`.
- [ ] AC-5: When `last_ocr_result` is in session state, a "Mean Confidence" metric appears.
- [ ] AC-6: When `last_ocr_result` is in session state, a region details dataframe appears.
- [ ] AC-7: When `last_ocr_result` is in session state, a "Regions Detected" metric appears.

---

## Design

### Public API

No Python API — Streamlit page.

### Data Flow

```
User uploads image → state.set_uploaded_image(pil)
User selects language / GPU option
User clicks "Run OCR"
    │
    ▼
_get_ocr_engine(lang, use_gpu)   ← @st.cache_resource
    └─► OCREngine(lang=lang, device="cpu"/"gpu")
    │
    ▼
engine.recognize(src)
    │
    ▼
state.set_ocr_result(result)
overlay_bboxes(src, boxes, scores) → annotated image
aggregate_confidence(scores) → mean confidence metric
_build_region_df(result)    → dataframe
```

### Key Interfaces

| Symbol | Kind | Responsibility |
|--------|------|---------------|
| `_get_ocr_engine(lang, use_gpu)` | cached function | `@st.cache_resource` — constructs `OCREngine` once per `(lang, gpu)` pair |
| `_build_region_df(ocr_result)` | helper | Converts `{text, boxes, scores}` to `pd.DataFrame` |
| `"Clear engine cache"` button | widget | Calls `st.cache_resource.clear(); st.rerun()` |

---

## Implementation

### Files

| Path | Role |
|------|------|
| `src/document_simulator/ui/pages/02_ocr_engine.py` | Complete page |
| `src/document_simulator/ocr/engine.py` | `OCREngine` — constructed via `_get_ocr_engine` |
| `src/document_simulator/ocr/metrics.py` | `aggregate_confidence`, `calculate_cer`, `calculate_wer` |
| `src/document_simulator/ui/components/image_display.py` | `overlay_bboxes` |

### Key Architectural Decisions

1. **`@st.cache_resource` on `_get_ocr_engine`** — PaddleOCR model loading takes 2–10 seconds. Caching on `(lang, gpu)` means switching language creates a new engine but reusing the same settings reuses the cached instance.

2. **"Clear engine cache" button** — After fixing `engine.py` (PaddleOCR 3.x migration), the cached broken engine persisted across reruns. A sidebar button lets users evict the cache without restarting the Streamlit server.

3. **`_build_region_df` as a pure helper** — Converts the raw OCR result dict into a `pd.DataFrame` for display. Testable in isolation, and keeps the page's display section clean.

4. **Lazy CER/WER computation** — CER and WER metrics only appear when the user uploads a ground-truth `.txt` file. The metric columns are always rendered (avoiding layout shift) but show values only when GT is available.

### Known Edge Cases & Constraints

- The "Clear engine cache" button clears **all** `@st.cache_resource` caches app-wide, not just the OCR engine cache.
- `AppTest` does not expose `at.download_button` — tests check session state instead.
- PaddleOCR may print verbose logs to stdout even with `device="cpu"` — these cannot be suppressed in 3.x without patching logging.

---

## Tests

### Test Files

| File | Type | Count | What is covered |
|------|------|-------|-----------------|
| `tests/ui/integration/test_ocr_engine_page.py` | integration | 8 | Load, Run button, language selectbox, "en" option, warning on no image, confidence metric, region table, region count metric |

### TDD Cycle Summary

**Red — first failing tests written:**

| Test name | File | Initial failure reason |
|-----------|------|----------------------|
| `test_ocr_page_loads` | `test_ocr_engine_page.py` | `ValueError: Unknown argument: show_log` — PaddleOCR 2.x constructor in cached function |
| `test_ocr_page_shows_metrics_when_result_in_state` | `test_ocr_engine_page.py` | `AttributeError: 'list' object has no attribute 'get'` — 2.x result parsing |
| `test_ocr_page_shows_region_table_when_result_in_state` | `test_ocr_engine_page.py` | `AttributeError: SafeSessionState has no .get()` |

**Green — minimal implementation:**

Fixed `engine.py` for PaddleOCR 3.x (see `feature_ocr_engine.md` TDD section). Injected mock results via `at.session_state["last_ocr_result"] = mock_result` in tests. Replaced `st.session_state.get()` with `"key" in st.session_state` guard. All 8 tests passed.

**Refactor — improvements made after green:**

| What changed | Why |
|--------------|-----|
| Added "Clear engine cache" sidebar button | Streamlit cached the old broken `OCREngine`; users need a way to evict it without a server restart |
| Added ground-truth file uploader with CER/WER metric columns | The evaluation use-case requires comparing OCR output against known text |

### How to Run

```bash
uv run pytest tests/ui/integration/test_ocr_engine_page.py -v
```

---

## Dependencies

### Requires

| Dependency | Kind | Why |
|------------|------|-----|
| `ocr/engine.py` | internal | `OCREngine` |
| `ocr/metrics.py` | internal | `aggregate_confidence`, `calculate_cer`, `calculate_wer` |
| `ui/components/image_display.py` | internal | `overlay_bboxes` |
| `ui/state/session_state.py` | internal | `SessionStateManager` |
| `pandas` | external | `_build_region_df` → `pd.DataFrame` |

---

## Future Work

- [ ] Add page-level "Copy text" button (requires JS integration).
- [ ] Add language auto-detection suggestion based on script detection.
- [ ] Cache engine per-language and allow warm switching without a full clear.

---

## References

- [feature_ocr_engine.md](feature_ocr_engine.md)
- [feature_ui_components.md](feature_ui_components.md)
- [UI_PLAN.md](../UI_PLAN.md)
