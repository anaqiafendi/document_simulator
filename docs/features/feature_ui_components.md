# Feature: UI Shared Components

> **GitHub Issue:** `#13`
> **Status:** `complete`
> **Module:** `document_simulator.ui.components` + `document_simulator.ui.state`

---

## Summary

Four shared UI utility modules — `image_display`, `metrics_charts`, `file_uploader`, and `session_state` — that provide reusable building blocks for all five Streamlit pages. They wrap PIL/numpy image operations, Plotly chart construction, file validation, and typed `st.session_state` access behind clean function/class interfaces.

---

## Motivation

### Problem Statement

Without shared components, each page would duplicate bounding-box drawing, chart creation, file validation, and `st.session_state` key management. Duplicate session state keys across pages lead to subtle cross-page interference bugs; duplicate chart code means chart style inconsistencies.

### Value Delivered

- **`image_display`**: Confidence-coloured bounding box overlay for OCR results; side-by-side layout; `image_to_bytes` for download buttons.
- **`metrics_charts`**: Three Plotly chart types (grouped bar, box, line) consistent in style across evaluation and RL pages.
- **`file_uploader`**: Centralised extension validation and PIL conversion for all upload widgets.
- **`session_state`**: Typed accessor methods around `st.session_state` — no raw string keys in pages.

---

## User Stories

| Role | Goal | So That |
|------|------|---------|
| UI page developer | I call `overlay_bboxes(image, boxes, scores)` | I get an annotated PIL Image without writing drawing code |
| UI page developer | I call `state.set_ocr_result(result)` | State is stored under the correct key without a typo risk |
| UI page developer | I call `cer_wer_bar(metrics)` | I get a Plotly figure with no Plotly API knowledge |
| UI page developer | I call `uploaded_file_to_pil(file)` | I get a PIL Image without handling bytes/BytesIO myself |

---

## Acceptance Criteria

- [ ] AC-1: `overlay_bboxes(image, boxes, scores)` returns a PIL Image of the same size.
- [ ] AC-2: `_confidence_colour(1.0)` returns green-ish RGB; `_confidence_colour(0.0)` returns red-ish.
- [ ] AC-3: `image_to_bytes(image)` returns non-empty bytes.
- [ ] AC-4: `cer_wer_bar(metrics)` returns a Plotly `Figure` with `"CER"` and `"WER"` in the data.
- [ ] AC-5: `confidence_box(original_scores, augmented_scores)` returns a Plotly `Figure`.
- [ ] AC-6: `reward_line([])` returns a Plotly `Figure` without raising.
- [ ] AC-7: `is_valid_image_extension("file.jpg")` returns `True`; `"file.pdf"` returns `False`.
- [ ] AC-8: `uploaded_file_to_pil(fake_file)` returns a PIL Image.
- [ ] AC-9: `SessionStateManager().get_uploaded_image()` returns `None` when unset.
- [ ] AC-10: `SessionStateManager().set_ocr_result(result).get_ocr_result()` returns the same dict.
- [ ] AC-11: `SessionStateManager().clear()` resets all keys to their default values.

---

## Design

### Public API

```python
# image_display
from document_simulator.ui.components.image_display import overlay_bboxes, image_to_bytes, show_side_by_side
annotated: Image.Image = overlay_bboxes(src, boxes, scores)
raw: bytes = image_to_bytes(annotated, fmt="PNG")

# metrics_charts
from document_simulator.ui.components.metrics_charts import cer_wer_bar, confidence_box, reward_line
fig = cer_wer_bar({"mean_original_cer": 0.05, "mean_augmented_cer": 0.18, ...})
fig = reward_line([{"step": 1000, "reward": 0.42}, ...])

# file_uploader
from document_simulator.ui.components.file_uploader import uploaded_file_to_pil, is_valid_image_extension
image: Image.Image = uploaded_file_to_pil(uploaded_file)

# session_state
from document_simulator.ui.state.session_state import SessionStateManager
state = SessionStateManager()
state.set_uploaded_image(pil_image)
state.get_uploaded_image()  # → PIL Image or None
```

### Data Flow

```
overlay_bboxes(image, boxes, scores)
    │
    ├─► PIL ImageDraw.Draw(image_copy)
    ├─► for each (box, score): _confidence_colour(score) → (R,G,B)
    │       draw.polygon(box, outline=colour, width=line_width)
    └─► return annotated PIL Image
```

### Key Interfaces

**image_display**

| Symbol | Kind | Responsibility |
|--------|------|---------------|
| `_confidence_colour(score)` | function | Maps `[0,1]` → `(R, G, B)` green↔red gradient |
| `overlay_bboxes(image, boxes, scores, ...)` | function | Draw coloured polygon bboxes on a copy of the image |
| `image_to_bytes(image, fmt)` | function | PIL Image → bytes for `st.download_button` |
| `show_side_by_side(original, augmented, labels)` | function | Two `st.columns` with images |

**metrics_charts**

| Symbol | Kind | Responsibility |
|--------|------|---------------|
| `cer_wer_bar(metrics)` | function | Grouped Plotly bar: Original vs Augmented CER/WER |
| `confidence_box(original_scores, augmented_scores)` | function | Plotly box plot of confidence distributions |
| `reward_line(log_entries)` | function | Plotly line chart of RL reward over steps |

**file_uploader**

| Symbol | Kind | Responsibility |
|--------|------|---------------|
| `ALLOWED_EXTENSIONS` | frozenset | Valid image file extensions |
| `is_valid_image_extension(filename)` | function | Extension membership check |
| `uploaded_file_to_pil(uploaded_file)` | function | `UploadedFile.getvalue()` → PIL Image RGB |
| `uploaded_files_to_pil(uploaded_files)` | function | List of `UploadedFile` → list of PIL Images |

**session_state**

| Symbol | Kind | Responsibility |
|--------|------|---------------|
| `SessionStateManager` | class | Typed wrappers around `st.session_state` string keys |
| `get/set_uploaded_image` | methods | `last_uploaded_image` key |
| `get/set_aug_image` | methods | `last_aug_image` key |
| `get/set_ocr_result` | methods | `last_ocr_result` key |
| `get/set_eval_results` | methods | `eval_results` key |
| `is/set_training_running` | methods | `training_running` key |
| `get_training_log / append_training_log` | methods | `training_log` key (list) |
| `get/set_batch_results` | methods | `batch_results` key |
| `get/set_batch_elapsed` | methods | `batch_elapsed` key |
| `clear()` | method | Reset all managed keys to defaults |

### Configuration

No `.env` settings.

---

## Implementation

### Files

| Path | Role |
|------|------|
| `src/document_simulator/ui/components/image_display.py` | `overlay_bboxes`, `image_to_bytes`, `show_side_by_side` |
| `src/document_simulator/ui/components/metrics_charts.py` | `cer_wer_bar`, `confidence_box`, `reward_line` |
| `src/document_simulator/ui/components/file_uploader.py` | `uploaded_file_to_pil`, extension validation |
| `src/document_simulator/ui/state/session_state.py` | `SessionStateManager` class |

### Key Architectural Decisions

1. **`SessionStateManager` over raw string keys** — Pages would need to know `"last_ocr_result"` as a string. A typo (`"last_ocr_Results"`) silently stores to a different key. `SessionStateManager.set_ocr_result()` centralises the key and makes refactoring trivial.

2. **Plotly over Matplotlib** — Plotly charts are interactive (zoom, hover) and render correctly in Streamlit without DPI or thread issues that affect Matplotlib in server mode.

3. **`overlay_bboxes` works on a copy** — `image.copy()` before drawing prevents mutation of the PIL Image stored in `session_state`. A caller that calls `overlay_bboxes` twice would otherwise accumulate bboxes.

4. **`_confidence_colour` linear interpolation** — Green `(0, 200, 0)` at score=1.0, red `(220, 0, 0)` at score=0.0, linear in between. Simple and visually clear without requiring a colour library.

5. **`image_to_bytes` uses `io.BytesIO`** — Streamlit's `st.download_button(data=bytes)` requires `bytes`. PIL's `Image.save(buf, format=fmt)` on a `BytesIO` is the standard pattern.

### Known Edge Cases & Constraints

- `overlay_bboxes` expects boxes as `list[list[[x,y]]]` (quadrilateral polygon). Axis-aligned `[x_min, y_min, x_max, y_max]` boxes are not supported directly.
- `AppTest` in Streamlit 1.54 does not expose `at.plotly_chart` or `at.download_button` as named widget accessors — integration tests check `at.metric` and `at.session_state` instead.
- `SessionStateManager` methods that call `st.session_state` require a Streamlit context. Unit tests patch `streamlit.session_state` with a plain dict.

---

## Tests

### Test Files

| File | Type | Count | What is covered |
|------|------|-------|-----------------|
| `tests/ui/unit/test_image_display.py` | unit | 14 | `_confidence_colour` (3), `overlay_bboxes` (5), `image_to_bytes` (3), `show_side_by_side` via mock (3) |
| `tests/ui/unit/test_metrics_charts.py` | unit | 14 | `cer_wer_bar` (5), `confidence_box` (4), `reward_line` (5) |
| `tests/ui/unit/test_file_uploader.py` | unit | 14 | `is_valid_image_extension` (6), `uploaded_file_to_pil` (4), `uploaded_files_to_pil` (4) |
| `tests/ui/unit/test_session_state.py` | unit | 18 | All getters/setters, `clear()`, training log, batch helpers |

**Total: 60 unit tests across 4 files** (56 counted in the full suite, variance is due to parametrize expansion).

### TDD Cycle Summary

**Red — first failing tests written:**

| Test name | File | Initial failure reason |
|-----------|------|----------------------|
| `test_confidence_colour_high_score` | `test_image_display.py` | `ImportError: cannot import name '_confidence_colour'` |
| `test_cer_wer_bar_returns_figure` | `test_metrics_charts.py` | `ImportError: cannot import name 'cer_wer_bar'` |
| `test_valid_image_extension_jpg` | `test_file_uploader.py` | `ImportError: cannot import name 'is_valid_image_extension'` |
| `test_session_state_imports` | `test_session_state.py` | `ImportError: cannot import name 'SessionStateManager'` |
| `test_get_uploaded_image_returns_none_when_unset` | `test_session_state.py` | `AttributeError: 'dict' object has no attribute 'get'` — `st.session_state` was not patched yet |

**Green — minimal implementation:**

- `image_display`: Implemented `overlay_bboxes` using `ImageDraw.polygon`. Implemented `_confidence_colour` as a linear interpolation between red and green. All `image_display` tests passed.
- `metrics_charts`: Used `plotly.graph_objects.Figure` with `go.Bar` and `go.Box` objects. `reward_line` required a guard for empty `log_entries` to avoid `KeyError` on `log[0]["step"]`.
- `file_uploader`: `ALLOWED_EXTENSIONS` frozenset + `is_valid_image_extension` via `Path(filename).suffix.lower() in ALLOWED_EXTENSIONS`. `uploaded_file_to_pil` via `Image.open(BytesIO(file.getvalue()))`.
- `session_state`: All methods via `st.session_state.get(key, default)` pattern. Unit tests patch `streamlit.session_state` with a plain `{}`.

**Refactor — improvements made after green:**

| What changed | Why |
|--------------|-----|
| Replaced `st.session_state.get()` with `st.session_state[key] if key in st.session_state else default` | Streamlit's `SafeSessionState` in AppTest does not implement `.get()` — `"key" in st.session_state` is the safe pattern |
| Added `reward_line` secondary CER trace | RL training page needed to overlay CER alongside reward when `info` dict contains `"cer"` key |

### How to Run

```bash
# All component unit tests
uv run pytest tests/ui/unit/ -v

# Single module
uv run pytest tests/ui/unit/test_image_display.py -v
uv run pytest tests/ui/unit/test_session_state.py -v

# With coverage
uv run pytest tests/ui/unit/ --cov=document_simulator.ui
```

---

## Dependencies

### Requires

| Dependency | Kind | Why |
|------------|------|-----|
| `PIL` (Pillow) | external | Image drawing in `overlay_bboxes` |
| `plotly` | external | `go.Figure`, `go.Bar`, `go.Box`, `go.Scatter` |
| `streamlit` | external | `st.session_state`, `st.columns`, `st.image` |
| `io` | stdlib | `BytesIO` for `image_to_bytes` and `uploaded_file_to_pil` |

### Required By

| Consumer | How it uses this feature |
|----------|------------------------|
| `ui/pages/01_augmentation_lab.py` | `show_side_by_side`, `image_to_bytes`, `uploaded_file_to_pil`, `SessionStateManager` |
| `ui/pages/02_ocr_engine.py` | `overlay_bboxes`, `image_to_bytes`, `uploaded_file_to_pil`, `SessionStateManager` |
| `ui/pages/03_batch_processing.py` | `uploaded_files_to_pil`, `SessionStateManager` |
| `ui/pages/04_evaluation.py` | `cer_wer_bar`, `confidence_box`, `SessionStateManager` |
| `ui/pages/05_rl_training.py` | `reward_line`, `SessionStateManager` |

---

## Usage Examples

### Minimal

```python
from document_simulator.ui.components.image_display import overlay_bboxes
annotated = overlay_bboxes(image, result["boxes"], result["scores"])
st.image(annotated)
```

### Typical

```python
from document_simulator.ui.components.metrics_charts import cer_wer_bar
from document_simulator.ui.state.session_state import SessionStateManager
import streamlit as st

state = SessionStateManager()
metrics = state.get_eval_results()
if metrics:
    st.plotly_chart(cer_wer_bar(metrics), use_container_width=True)
```

### Advanced / Edge Case

```python
# Download annotated image
from document_simulator.ui.components.image_display import overlay_bboxes, image_to_bytes
import streamlit as st

annotated = overlay_bboxes(src, boxes, scores, show_scores=True, line_width=3)
st.download_button(
    "Download annotated image",
    data=image_to_bytes(annotated, fmt="PNG"),
    file_name="annotated.png",
    mime="image/png",
)
```

---

## Future Work

- [ ] Add `overlay_bboxes` support for axis-aligned `[x_min, y_min, x_max, y_max]` box format.
- [ ] Add `reward_line` smoothing (rolling average) for noisy training curves.
- [ ] Add `SessionStateManager.get_rl_model_path()` / `set_rl_model_path()` for the model save/load flow on the RL page.

---

## References

- [UI_PLAN.md](../UI_PLAN.md)
- [feature_ui_augmentation_lab.md](feature_ui_augmentation_lab.md)
