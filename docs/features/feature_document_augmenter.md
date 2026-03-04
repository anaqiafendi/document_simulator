# Feature: Document Augmenter

> **GitHub Issue:** `#2`
> **Status:** `complete`
> **Module:** `document_simulator.augmentation.augmenter`

---

## Summary

`DocumentAugmenter` wraps an Augraphy pipeline behind a type-preserving `augment()` method that accepts either a PIL Image or a numpy array and returns the same type. It delegates pipeline selection to `PresetFactory` and exposes a file-level convenience method for disk-to-disk augmentation.

---

## Motivation

### Problem Statement

Callers (CLI, RL environment, UI) work with different image representations — PIL for display, numpy for ML. Without a unifying adapter, each caller would need to handle PIL↔numpy conversion and Augraphy's numpy-only API independently.

### Value Delivered

- Single class to construct once and call repeatedly across a batch.
- Input type is preserved in output — PIL in → PIL out; numpy in → numpy out.
- Pipeline selection is a single string argument, no Augraphy knowledge required.
- `augment_file()` handles load/save so the CLI needs zero image I/O code.

---

## User Stories

| Role | Goal | So That |
|------|------|---------|
| CLI user | I can run `augment input.jpg output.jpg` | I get a degraded copy without writing Python |
| ML researcher | I can pass a numpy array and get a numpy array back | I can chain augmentation with PyTorch transforms |
| UI developer | I can call `augmenter.augment(pil_image)` | I can display the result directly with `st.image()` |

---

## Acceptance Criteria

- [ ] AC-1: `DocumentAugmenter(pipeline="default")` initialises without error.
- [ ] AC-2: `augment(PIL Image)` returns a `PIL Image` of the same size.
- [ ] AC-3: `augment(np.ndarray)` returns an `np.ndarray` of the same shape.
- [ ] AC-4: `augment_file(input_path, output_path)` writes a valid image to disk.

---

## Design

### Public API

```python
from document_simulator.augmentation import DocumentAugmenter

augmenter = DocumentAugmenter(pipeline="light")   # or "medium", "heavy", "default"
result = augmenter.augment(image)                 # PIL Image or numpy array
augmenter.augment_file(Path("in.jpg"), Path("out.jpg"))
```

```bash
uv run python -m document_simulator augment input.jpg output.jpg --pipeline heavy
```

### Data Flow

```
augment(image: PIL | numpy)
    │
    ├─► [if PIL] np.array(image) → image_array
    │
    ▼
AugraphyPipeline.__call__(image_array)  ← Augraphy applies ink/paper/post phases
    │
    ├─► [if input was PIL] Image.fromarray(augmented)
    │
    ▼
Returns same type as input
```

### Key Interfaces

| Symbol | Kind | Responsibility |
|--------|------|---------------|
| `DocumentAugmenter(pipeline)` | class | Instantiates an Augraphy pipeline via `PresetFactory` |
| `augment(image)` | method | Type-preserving single-image augmentation |
| `augment_file(input_path, output_path)` | method | Load → augment → save; creates parent dirs |

### Configuration

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| No `.env` settings | — | — | Pipeline chosen at construction time via `pipeline` arg |

---

## Implementation

### Files

| Path | Role |
|------|------|
| `src/document_simulator/augmentation/augmenter.py` | Primary implementation |
| `src/document_simulator/augmentation/presets.py` | Provides `PresetFactory` used in `_create_pipeline()` |

### Key Architectural Decisions

1. **Type preservation over simplicity** — Always returning numpy would be simpler, but PIL is the natural type for Streamlit display and for the `augment_file` path. Preserving the input type avoids silent type mismatches throughout the call stack.

2. **Pipeline built once, called many times** — `_create_pipeline()` is called in `__init__`, not in `augment()`. This amortises the Augraphy initialisation cost across an entire batch.

3. **No state between calls** — `augment()` has no mutable side effects, so a single `DocumentAugmenter` instance is safe to share across threads (e.g., in Streamlit's cached resource or a multiprocessing fork).

### Known Edge Cases & Constraints

- Augraphy may internally resize images at certain pipeline stages; the test asserts `result.size == sample_image.size` to catch regressions.
- Very small images (< 32×32) can cause Augraphy to produce artefacts or errors.

---

## Tests

### Test Files

| File | Type | Count | What is covered |
|------|------|-------|-----------------|
| `tests/test_augmentation.py` | unit | 3 | Init, PIL round-trip, numpy round-trip |
| `tests/integration/test_augmentation_ocr.py` | integration | 3 | Full pipeline produces image, numpy round-trip, augmented image passes to mock OCR |

### TDD Cycle Summary

**Red — first failing tests written:**

| Test name | File | Initial failure reason |
|-----------|------|----------------------|
| `test_augmenter_initialization` | `tests/test_augmentation.py` | `ImportError: cannot import name 'DocumentAugmenter'` |
| `test_augment_pil_image` | `tests/test_augmentation.py` | `ImportError: cannot import name 'DocumentAugmenter'` |
| `test_augment_numpy_array` | `tests/test_augmentation.py` | `ImportError: cannot import name 'DocumentAugmenter'` |

**Green — minimal implementation:**

Created `DocumentAugmenter.__init__` that called `PresetFactory.create()` and stored the pipeline, and `augment()` that ran `self._augraphy_pipeline(np.array(image))` but always returned numpy. The PIL test failed because a numpy array was returned. Added the `input_is_pil` flag and `Image.fromarray(augmented)` conversion to fix it.

**Refactor — improvements made after green:**

| What changed | Why |
|--------------|-----|
| Moved pipeline creation to `_create_pipeline()` private method | `__init__` was becoming long; the preset lookup logic is independently testable |
| Added `augment_file()` | CLI integration test (`test_cli_augment_command`) required disk-to-disk augmentation without the caller managing I/O |

### How to Run

```bash
uv run pytest tests/test_augmentation.py tests/integration/test_augmentation_ocr.py -v
uv run pytest tests/test_augmentation.py --cov=document_simulator.augmentation.augmenter
```

---

## Dependencies

### Requires

| Dependency | Kind | Why |
|------------|------|-----|
| `augraphy==8.2.6` | external | `AugraphyPipeline` — the augmentation engine |
| `augmentation/presets.py` | internal | `PresetFactory.create()` configures the pipeline |
| `PIL` | external | Input/output image type |
| `numpy` | external | Augraphy operates on numpy arrays internally |

### Required By

| Consumer | How it uses this feature |
|----------|------------------------|
| `augmentation/batch.py` | `BatchAugmenter` holds a `DocumentAugmenter` and calls `augment()` per image |
| `cli.py` | `augment` subcommand constructs `DocumentAugmenter` and calls `augment_file()` |
| `rl/environment.py` | `DocumentEnv._build_augmenter()` instantiates `DocumentAugmenter` from action params |
| `evaluation/evaluator.py` | `Evaluator` calls `augmenter.augment(image)` for each dataset sample |
| `ui/pages/01_augmentation_lab.py` | Constructs `DocumentAugmenter(preset)` on button click |

---

## Usage Examples

### Minimal

```python
from document_simulator.augmentation import DocumentAugmenter

result = DocumentAugmenter().augment(image)
```

### Typical

```python
from document_simulator.augmentation import DocumentAugmenter
from PIL import Image

augmenter = DocumentAugmenter(pipeline="medium")
image = Image.open("invoice.jpg")
degraded = augmenter.augment(image)
degraded.save("invoice_degraded.jpg")
```

### Advanced / Edge Case

```python
import numpy as np
from document_simulator.augmentation import DocumentAugmenter

# numpy in, numpy out — safe to pass directly to PyTorch transforms
augmenter = DocumentAugmenter(pipeline="heavy")
arr = np.array(image)   # uint8 HWC
result: np.ndarray = augmenter.augment(arr)
assert result.dtype == arr.dtype
```

---

## Future Work

- [ ] Add `augment_batch_file(input_dir, output_dir)` shortcut at the `DocumentAugmenter` level.
- [ ] Support per-call pipeline override without reconstructing the instance.

---

## References

- [feature_augmentation_presets.md](feature_augmentation_presets.md)
- [IMPLEMENTATION_PLAN.md — Phase 1](../IMPLEMENTATION_PLAN.md)
