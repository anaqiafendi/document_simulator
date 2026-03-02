# Feature: OCR Engine

> **GitHub Issue:** `#4`
> **Status:** `complete`
> **Module:** `document_simulator.ocr.engine`

---

## Summary

`OCREngine` wraps PaddleOCR 3.x behind a stable `recognize()` interface that accepts PIL Images, numpy arrays, or file paths and returns a normalised dict of `{text, boxes, scores, raw}`. It handles CPU/GPU selection, conditional model-directory injection, and PaddleOCR 3.x's breaking API changes transparently.

---

## Motivation

### Problem Statement

PaddleOCR 3.x changed its constructor signature, result format, and inference method from 2.x. All callers would break on upgrade, and the raw output format (an `OCRResult` dict-like object with `rec_texts`, `rec_scores`, `rec_polys` keys) is inconvenient for downstream use.

### Value Delivered

- Single stable dict schema across PaddleOCR versions and language configs.
- Polygon bounding boxes normalised to plain `list[list[float]]`.
- GPU selection via a single `use_gpu` bool — no direct device string management.
- Model dirs only injected when the path exists on disk, preventing PaddleOCR 3.x `AssertionError` on missing directories.
- `@st.cache_resource` compatible — the engine is constructed once and reused.

---

## User Stories

| Role | Goal | So That |
|------|------|---------|
| Developer | I call `engine.recognize(image)` | I get a clean dict without parsing PaddleOCR internals |
| UI user | I click "Run OCR" | Extracted text and bounding boxes appear immediately |
| CLI user | I run `ocr document.jpg` | Text is printed or saved to a file |
| Evaluator | I pass OCR results to `calculate_cer()` | I get a CER score without format conversion |

---

## Acceptance Criteria

- [ ] AC-1: `OCREngine(use_gpu=False, lang="en")` initialises without raising.
- [ ] AC-2: `recognize(pil_image)` returns a dict with keys `text`, `boxes`, `scores`, `raw`.
- [ ] AC-3: `recognize()` with an image that contains no text returns `{"text": "", "boxes": [], "scores": []}`.
- [ ] AC-4: `recognize_file(path)` produces the same structure as `recognize()`.
- [ ] AC-5: `use_gpu=True` sets `device="gpu"` in the PaddleOCR constructor; `False` sets `device="cpu"`.

---

## Design

### Public API

```python
from document_simulator.ocr import OCREngine

engine = OCREngine(use_gpu=False, lang="en")
result = engine.recognize(image)   # PIL Image, numpy array, or str/Path
# result = {"text": "Invoice\nTotal: $42", "boxes": [...], "scores": [...], "raw": ...}
```

```bash
uv run python -m document_simulator ocr document.jpg
uv run python -m document_simulator ocr document.jpg --output extracted.txt --use-gpu
```

### Data Flow

```
recognize(image: PIL | numpy | str | Path)
    │
    ├─► Convert PIL → numpy array  (str/Path left as-is)
    │
    ▼
self.ocr.predict(image_path)
    │                           ← PaddleOCR 3.x inference
    ▼
result[0]  →  OCRResult dict
    │
    ├─► rec_texts   → texts: list[str]
    ├─► rec_scores  → scores: list[float]
    └─► rec_polys   → boxes: list[list[[x, y]]] (normalised from numpy arrays)
    │
    ▼
{"text": "\n".join(texts), "boxes": boxes, "scores": scores, "raw": result}
```

### Key Interfaces

| Symbol | Kind | Responsibility |
|--------|------|---------------|
| `OCREngine(use_gpu, lang, det_model_dir, rec_model_dir, cls_model_dir)` | class | Constructs PaddleOCR 3.x instance |
| `recognize(image)` | method | Single-image OCR, returns normalised dict |
| `recognize_file(input_path)` | method | Path-in, dict-out convenience wrapper |
| `recognize_batch(images)` | method | Sequentially calls `recognize()` per image |

### Configuration

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `PADDLEOCR_USE_GPU` | `bool` | `false` | Override `use_gpu` from environment |
| `PADDLEOCR_LANG` | `str` | `"en"` | Override `lang` from environment |
| `PADDLEOCR_DET_MODEL_DIR` | `str` | `""` | Custom detection model directory (only used if path exists) |
| `PADDLEOCR_REC_MODEL_DIR` | `str` | `""` | Custom recognition model directory (only used if path exists) |

---

## Implementation

### Files

| Path | Role |
|------|------|
| `src/document_simulator/ocr/engine.py` | Primary implementation |
| `src/document_simulator/config.py` | `settings.paddleocr_*` attributes consumed by `__init__` |

### Key Architectural Decisions

1. **PaddleOCR 3.x constructor args only** — Removed all 2.x args: `use_angle_cls`, `use_gpu`, `show_log`, `det_model_dir`, `cls_model_dir`. Using `device="gpu"/"cpu"` and `text_detection_model_dir` / `text_recognition_model_dir` instead. This was a breaking upgrade; the error was caught via `error_logs/ocr_engine.log` and fixed iteratively.

2. **Conditional model dir injection** — PaddleOCR 3.x `assert path.exists()` before downloading. `settings.paddleocr_det_model_dir` defaults to `"models/paddle/det"` which does not exist in a fresh clone. The engine only passes a model dir kwarg when `Path(dir).exists()` is true, allowing auto-download otherwise.

3. **`predict()` over `ocr()`** — `ocr.ocr()` is deprecated in 3.x. `ocr.predict()` is the new inference method returning `list[OCRResult]`.

4. **Polygon normalisation** — PaddleOCR 3.x returns `rec_polys` as a list of numpy arrays of shape `(N, 2)`. These are converted to `list[list[float]]` so the output is JSON-serialisable and `overlay_bboxes()` can draw them without numpy.

5. **`@st.cache_resource` awareness** — The engine is expensive to construct (model download + load). The UI page caches it with `@st.cache_resource`. A "Clear engine cache" button calls `st.cache_resource.clear()` to allow re-initialisation after config changes.

### Known Edge Cases & Constraints

- Blank or very low-contrast images often return an empty result rather than raising.
- PaddleOCR downloads model weights on first use (~200 MB). Subsequent runs are fast.
- `cls_model_dir` is accepted as a constructor parameter for API compatibility but is ignored in 3.x (the cls model is no longer separate).
- `recognize_batch()` is sequential — it does not use PaddleOCR's native batching.

---

## Tests

### Test Files

| File | Type | Count | What is covered |
|------|------|-------|-----------------|
| `tests/ui/integration/test_ocr_engine_page.py` | integration | 8 | Page load, Run button, language selectbox, warning on no image, confidence metric, region table, region count metric |

*Note: Unit tests for `OCREngine` itself mock PaddleOCR at the integration level (UI page tests) rather than in isolation, because PaddleOCR's model download makes pure unit tests slow.*

### TDD Cycle Summary

**Red — first failing tests written:**

| Test name | File | Initial failure reason |
|-----------|------|----------------------|
| `test_ocr_page_loads` | `tests/ui/integration/test_ocr_engine_page.py` | `ValueError: Unknown argument: show_log` (PaddleOCR 2.x constructor in `_get_ocr_engine`) |
| `test_ocr_page_warning_when_no_image` | `tests/ui/integration/test_ocr_engine_page.py` | Same root cause |
| `test_ocr_page_shows_metrics_when_result_in_state` | `tests/ui/integration/test_ocr_engine_page.py` | `AttributeError: 'list' object has no attribute 'get'` (2.x result parsing) |

**Green — minimal implementation:**

1. Replaced PaddleOCR 2.x constructor with `PaddleOCR(lang=..., device=...)` — removed all invalid kwargs.
2. Replaced `ocr.ocr(image, cls=True)` with `ocr.predict(image)`.
3. Replaced `[[box, (text, score)]]` parsing with `result[0].get("rec_texts", [])` etc.
4. Added conditional model dir logic (`if det_dir and Path(det_dir).exists()`).

All 8 OCR page integration tests passed after these changes.

**Refactor — improvements made after green:**

| What changed | Why |
|--------------|-----|
| Added "Clear engine cache" button to `02_ocr_engine.py` sidebar | Streamlit's `@st.cache_resource` preserved the old broken engine instance across the code fix; users needed a way to evict it without restarting the server |
| Verified stale log file by cross-referencing logged line number against fixed code | Error log showed `line 40` which was a comment in the fixed version, confirming the fix was applied before the log was re-read |

### How to Run

```bash
uv run pytest tests/ui/integration/test_ocr_engine_page.py -v
```

---

## Dependencies

### Requires

| Dependency | Kind | Why |
|------------|------|-----|
| `paddleocr==3.4.0` | external | Core OCR inference engine |
| `numpy` | external | Image array representation; polygon coordinate extraction |
| `PIL` | external | Input image format |
| `config.py` | internal | `settings.paddleocr_*` default values |

### Required By

| Consumer | How it uses this feature |
|----------|------------------------|
| `cli.py` | `ocr` subcommand calls `OCREngine().recognize_file()` |
| `evaluation/evaluator.py` | `Evaluator` calls `ocr_engine.recognize(image)` per sample |
| `rl/environment.py` | `DocumentEnv._calculate_reward()` calls `self._ocr.recognize(aug_arr)` |
| `ui/pages/02_ocr_engine.py` | Cached via `@st.cache_resource _get_ocr_engine()`, called on button click |

---

## Usage Examples

### Minimal

```python
from document_simulator.ocr import OCREngine

engine = OCREngine()
result = engine.recognize("document.jpg")
print(result["text"])
```

### Typical

```python
from document_simulator.ocr import OCREngine
from PIL import Image

engine = OCREngine(use_gpu=False, lang="en")
image = Image.open("invoice.png")
result = engine.recognize(image)

for i, (text, score) in enumerate(zip(result["boxes"], result["scores"])):
    print(f"Region {i}: score={score:.2f}")
print(result["text"])
```

### Advanced / Edge Case

```python
# Custom detection model — only injected if path exists
engine = OCREngine(
    use_gpu=True,
    lang="ch",
    det_model_dir="/models/paddle/ch_det",
)
result = engine.recognize(numpy_array)
```

---

## Future Work

- [ ] Add `recognize_batch()` that uses PaddleOCR's native batch inference.
- [ ] Expose preprocessing options (deskew, contrast enhancement) as constructor params.
- [ ] Add dedicated unit tests for `OCREngine` using a mocked `PaddleOCR` to run without model download.

---

## References

- [feature_ocr_metrics.md](feature_ocr_metrics.md)
- [PaddleOCR 3.x Migration Guide](https://paddlepaddle.github.io/PaddleOCR/)
