# Feature: Evaluation Framework

> **GitHub Issue:** `#11`
> **Status:** `complete`
> **Module:** `document_simulator.evaluation.evaluator`

---

## Summary

`Evaluator` runs a `DocumentAugmenter` and an OCR engine over every sample in a `DocumentDataset`, computing per-sample CER, WER, and confidence for both the original and augmented images, then aggregates into mean/std metrics via `_aggregate_results`.

---

## Motivation

### Problem Statement

Measuring how much augmentation degrades OCR quality across an entire labelled dataset requires coordinating `DocumentAugmenter`, `OCREngine`, and `calculate_cer()` in a loop with error handling, aggregation, and progress reporting. Without `Evaluator`, every consumer would reimplement this loop.

### Value Delivered

- Single `evaluate_dataset(dataset)` call returns a complete metrics dict.
- Per-sample failures (augmentation or OCR errors) are caught and logged — evaluation continues.
- `_aggregate_results()` produces `mean_*` and `std_*` keys ready for display and comparison.
- `evaluate_single()` for spot-checking a single image/text pair.
- Works with any mock OCR engine that exposes `recognize(image) → {"text", "scores"}`.

---

## User Stories

| Role | Goal | So That |
|------|------|---------|
| Researcher | I call `evaluator.evaluate_dataset(test_set)` | I get mean CER/WER/confidence before and after augmentation |
| UI user | I point the Evaluation page at a labelled directory | Charts appear showing original vs augmented quality degradation |
| Developer | I mock the OCR engine in tests | Evaluation tests run without PaddleOCR model downloads |

---

## Acceptance Criteria

- [ ] AC-1: `evaluate_single(image, gt_text)` returns a dict with all 6 metric keys.
- [ ] AC-2: A mock OCR returning perfect text produces `original_cer == 0.0` and `original_confidence == 1.0`.
- [ ] AC-3: `evaluate_dataset(dataset_of_3)` returns `n_samples == 3`.
- [ ] AC-4: Result includes `mean_original_cer`, `std_original_cer`, `mean_augmented_confidence`.
- [ ] AC-5: `evaluate_dataset(empty_dataset)` returns `{"n_samples": 0}`.
- [ ] AC-6: `_aggregate_results([])` returns `{"n_samples": 0}`.

---

## Design

### Public API

```python
from document_simulator.evaluation.evaluator import Evaluator

ev = Evaluator(augmenter, ocr_engine)

# Dataset-level
metrics = ev.evaluate_dataset(dataset)
# {"n_samples": N, "mean_original_cer": ..., "std_augmented_wer": ..., ...}

# Single image
result = ev.evaluate_single(image, ground_truth_text)
# {"original_cer": ..., "augmented_cer": ..., "original_confidence": ..., ...}
```

### Data Flow

```
evaluate_dataset(dataset)
    │
    for (image, ground_truth) in dataset:
    │
    ├─► ocr.recognize(image)               → orig_cer, orig_wer, orig_conf
    │
    ├─► augmenter.augment(image)
    │   ocr.recognize(aug_image)           → aug_cer, aug_wer, aug_conf
    │
    └─► append per-sample dict to results[]
    │
    ▼
_aggregate_results(results)
    → {mean_*, std_*} for all 6 metrics + n_samples
```

### Key Interfaces

| Symbol | Kind | Responsibility |
|--------|------|---------------|
| `Evaluator(augmenter, ocr_engine, show_progress)` | class | Holds augmenter + OCR engine references |
| `evaluate_dataset(dataset)` | method | Full dataset evaluation with aggregation |
| `evaluate_single(image, gt_text)` | method | Per-sample evaluation without aggregation |
| `_aggregate_results(results)` | static method | `mean_*` + `std_*` over a list of metric dicts |

### Configuration

No `.env` settings — all configuration passed at construction time.

---

## Implementation

### Files

| Path | Role |
|------|------|
| `src/document_simulator/evaluation/evaluator.py` | Primary implementation |
| `src/document_simulator/ocr/metrics.py` | `calculate_cer`, `calculate_wer`, `aggregate_confidence` |
| `src/document_simulator/data/datasets.py` | `DocumentDataset` — iterable input |

### Key Architectural Decisions

1. **Per-sample exception catching** — If one image fails (corrupt file, augmentation bug), the loop continues with `cer=1.0, wer=1.0, conf=0.0` worst-case values and a `logger.warning`. Failing the entire evaluation for one bad sample would be worse for large datasets.

2. **`_aggregate_results` is a static method** — It operates only on a list of dicts and has no dependency on the evaluator state. Making it static and directly callable makes it testable in isolation (`test_aggregate_empty_results`).

3. **Duck-typed OCR engine** — `Evaluator` does not import `OCREngine`. Any object with `recognize(image) → {"text": str, "scores": list}` works. This is how the test mocks work and how the UI uses a cached engine.

4. **numpy for aggregation** — `np.mean()` and `np.std()` on a list of floats is correct and concise. Using stdlib `statistics.mean` would require an additional import for the same result.

### Known Edge Cases & Constraints

- The augmenter's `augment()` and the OCR engine's `recognize()` are both called in the main loop. For large datasets, this is slow. There is no parallelism at the evaluator level.
- `std_*` for a single sample is always 0.0 (not undefined).

---

## Tests

### Test Files

| File | Type | Count | What is covered |
|------|------|-------|-----------------|
| `tests/test_evaluation.py` | unit | 5 | `evaluate_single` keys (1), perfect OCR (1), `evaluate_dataset` n_samples (1), aggregate keys (1), empty results (1) |

### TDD Cycle Summary

**Red — first failing tests written:**

| Test name | File | Initial failure reason |
|-----------|------|----------------------|
| `test_evaluate_single_returns_all_keys` | `tests/test_evaluation.py` | `ImportError: cannot import name 'Evaluator'` |
| `test_evaluate_on_test_set` | `tests/test_evaluation.py` | `ImportError: cannot import name 'Evaluator'` |
| `test_aggregate_empty_results` | `tests/test_evaluation.py` | `ImportError: cannot import name 'Evaluator'` |

**Green — minimal implementation:**

Created `Evaluator.__init__`, `evaluate_single`, and `evaluate_dataset` with a plain Python loop and direct calls to `calculate_cer`, `calculate_wer`, `aggregate_confidence`. Added `_aggregate_results` as a static method using `numpy` mean/std.

All 5 tests passed without a refactor phase.

**Refactor — improvements made after green:**

| What changed | Why |
|--------------|-----|
| Added `try/except` around each `ocr.recognize()` and `augmenter.augment()` call | Integration test with `test_evaluation.py::test_evaluate_dataset_empty` passed but a planned stress test showed that a single corrupt image raised, aborting the entire loop — fault tolerance was added proactively |
| Added `tqdm` progress bar controlled by `show_progress` | The UI page runs evaluation over potentially hundreds of images; a progress bar is essential UX |

### How to Run

```bash
uv run pytest tests/test_evaluation.py -v
uv run pytest tests/test_evaluation.py --cov=document_simulator.evaluation.evaluator
```

---

## Dependencies

### Requires

| Dependency | Kind | Why |
|------------|------|-----|
| `numpy` | external | `np.mean`, `np.std` in `_aggregate_results` |
| `tqdm` | external | Progress bar in `evaluate_dataset` |
| `ocr/metrics.py` | internal | `calculate_cer`, `calculate_wer`, `aggregate_confidence` |
| `augmentation/augmenter.py` | internal | Type hint only; duck-typed at runtime |
| `data/datasets.py` | internal | `DocumentDataset` iterable interface |

### Required By

| Consumer | How it uses this feature |
|----------|------------------------|
| `ui/pages/04_evaluation.py` | Constructs `Evaluator(augmenter, ocr)`, calls `evaluate_dataset(dataset)`, displays results |

---

## Usage Examples

### Minimal

```python
from document_simulator.evaluation.evaluator import Evaluator

ev = Evaluator(augmenter, ocr_engine)
result = ev.evaluate_single(image, "Hello World")
```

### Typical

```python
from document_simulator.augmentation import DocumentAugmenter
from document_simulator.ocr import OCREngine
from document_simulator.data.datasets import DocumentDataset
from document_simulator.evaluation.evaluator import Evaluator
from pathlib import Path

augmenter = DocumentAugmenter("medium")
ocr = OCREngine(use_gpu=False)
dataset = DocumentDataset(Path("data/test"))

ev = Evaluator(augmenter, ocr, show_progress=True)
metrics = ev.evaluate_dataset(dataset)

print(f"Mean original CER:   {metrics['mean_original_cer']:.3f}")
print(f"Mean augmented CER:  {metrics['mean_augmented_cer']:.3f}")
print(f"Samples:             {metrics['n_samples']}")
```

### Advanced / Edge Case

```python
# Use a mock OCR engine — no PaddleOCR needed
from unittest.mock import MagicMock

mock_ocr = MagicMock()
mock_ocr.recognize.return_value = {"text": "Hello", "scores": [0.9], "boxes": []}

ev = Evaluator(augmenter, mock_ocr)
result = ev.evaluate_single(image, "Hello")
assert result["original_cer"] == 0.0
```

---

## Future Work

- [ ] Add parallelised evaluation using `concurrent.futures.ThreadPoolExecutor`.
- [ ] Add `evaluate_dataset_split()` that accepts `(train, val, test)` and returns metrics for each split.
- [ ] Export results to JSON / CSV.

---

## References

- [feature_ocr_metrics.md](feature_ocr_metrics.md)
- [feature_document_dataset.md](feature_document_dataset.md)
- [IMPLEMENTATION_PLAN.md — Phase 4](../IMPLEMENTATION_PLAN.md)
