# Feature: Batch Processing

> **GitHub Issue:** `#3`
> **Status:** `complete`
> **Module:** `document_simulator.augmentation.batch`

---

## Summary

`BatchAugmenter` augments a list of images (or a directory of image files) either sequentially or in parallel using Python's `multiprocessing.Pool`. It returns results in input order and delegates individual augmentation to `DocumentAugmenter`.

---

## Motivation

### Problem Statement

Augmenting hundreds of documents one at a time blocks the main process for minutes. A multiprocessing approach is needed, but `multiprocessing.Pool` requires picklable callables — Augraphy pipelines contain closures that are not picklable by default.

### Value Delivered

- CPU-bound augmentation parallelised across all available cores.
- Input order preserved regardless of process scheduling.
- Accepts either in-memory PIL Images or file paths — no pre-loading required.
- `augment_directory()` handles discovery, augmentation, and writing in one call.
- Progress bar via `tqdm` (optional) for long-running jobs.

---

## User Stories

| Role | Goal | So That |
|------|------|---------|
| ML researcher | I can call `augment_batch(images, parallel=True)` | I fill a training dataset from a small sample set in seconds |
| UI user | I can upload multiple files and click Run | I download a ZIP of all augmented versions |
| Script author | I can point `augment_directory()` at a folder | All images are processed without writing a loop |

---

## Acceptance Criteria

- [ ] AC-1: `augment_batch(images, parallel=False)` returns a list of the same length as input.
- [ ] AC-2: Each returned item is a `PIL Image` of the same dimensions as the input.
- [ ] AC-3: `augment_batch([], ...)` returns an empty list without error.
- [ ] AC-4: `augment_batch(file_paths, ...)` loads paths automatically.
- [ ] AC-5: `augment_directory(input_dir, output_dir)` writes one output file per input image.
- [ ] AC-6: `augment_directory()` creates `output_dir` if it does not exist.
- [ ] AC-7: `augment_directory()` on an empty directory returns `[]`.

---

## Design

### Public API

```python
from document_simulator.augmentation.batch import BatchAugmenter

batch = BatchAugmenter(augmenter="light", num_workers=4)

# List of PIL Images or file paths
results: list[Image.Image] = batch.augment_batch(images, parallel=True)

# Directory of images
output_paths = batch.augment_directory(Path("data/raw"), Path("data/aug"))
```

### Data Flow

```
augment_batch(images, parallel=True)
    │
    ├─► Load any Path/str inputs → PIL Images via ImageHandler.load()
    │
    ├─► [parallel=True, num_workers > 1]
    │       multiprocessing.Pool.imap(_augment_one, args)
    │       → preserves order via imap (not imap_unordered)
    │
    └─► [parallel=False or num_workers=1]
            Sequential loop: augmenter.augment(img) for each image
    │
    ▼
List[PIL Image] (same order as input)
```

### Key Interfaces

| Symbol | Kind | Responsibility |
|--------|------|---------------|
| `BatchAugmenter(augmenter, num_workers, show_progress)` | class | Orchestrates parallel/sequential augmentation |
| `augment_batch(images, parallel)` | method | List → List, with optional multiprocessing |
| `augment_directory(input_dir, output_dir, ...)` | method | Directory discovery → batch augment → write results |
| `_augment_one(args)` | module-level function | Picklable worker called by `Pool.imap` |

### Configuration

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `num_workers` | `int` | `4` | Number of worker processes; set to `1` to disable multiprocessing |
| `show_progress` | `bool` | `False` | Show `tqdm` progress bar |

---

## Implementation

### Files

| Path | Role |
|------|------|
| `src/document_simulator/augmentation/batch.py` | Primary implementation |
| `src/document_simulator/augmentation/augmenter.py` | `DocumentAugmenter` used per worker |
| `src/document_simulator/utils/image_io.py` | `ImageHandler.load()` for path inputs; `.save()` in `augment_directory` |

### Key Architectural Decisions

1. **`_augment_one` is a module-level function, not a method or lambda** — `multiprocessing.Pool` uses `pickle` to serialise tasks to worker processes. Methods and lambdas are not picklable. A module-level function with a `(augmenter, image)` tuple arg is the standard pattern.

2. **`imap` over `imap_unordered`** — `imap` preserves submission order. The caller (especially the ZIP-building UI page) depends on results matching the order of uploaded filenames.

3. **`num_workers=1` disables multiprocessing** — Rather than branching on a flag, the implementation silently falls back to a sequential loop when `num_workers <= 1` or `parallel=False`. This avoids `Pool(1)` overhead and simplifies testing (no subprocess forking in pytest).

4. **String constructor argument** — `BatchAugmenter(augmenter="heavy")` constructs a `DocumentAugmenter("heavy")` internally. This means the UI page can pass a string from a selectbox directly.

### Known Edge Cases & Constraints

- On macOS, `multiprocessing` uses `spawn` by default in Python 3.11+, which can be slow for the first job. Set `num_workers=1` in tests.
- Very large batches hold all output PIL Images in memory before returning. For extremely large datasets, stream results to disk via `augment_directory` instead.

---

## Tests

### Test Files

| File | Type | Count | What is covered |
|------|------|-------|-----------------|
| `tests/test_batch_processing.py` | unit | 8 | Sequential batch, path inputs, empty list, order preservation, directory augmentation (4 cases) |
| `tests/integration/test_augmentation_ocr.py` | integration | 1 | `BatchAugmenter.augment_directory()` writes correct file count |

### TDD Cycle Summary

**Red — first failing tests written:**

| Test name | File | Initial failure reason |
|-----------|------|----------------------|
| `test_batch_augmentation_sequential` | `tests/test_batch_processing.py` | `ImportError: cannot import name 'BatchAugmenter'` |
| `test_batch_empty_list` | `tests/test_batch_processing.py` | `ImportError: cannot import name 'BatchAugmenter'` |
| `test_augment_directory` | `tests/test_batch_processing.py` | `ImportError: cannot import name 'BatchAugmenter'` |

**Green — minimal implementation:**

Created `BatchAugmenter.__init__` accepting `augmenter` and `num_workers`, and `augment_batch()` with a sequential loop only (no multiprocessing). `augment_directory` was a minimal scan + `augment_batch` + `ImageHandler.save()` loop. All 8 tests passed sequentially.

**Refactor — improvements made after green:**

| What changed | Why |
|--------------|-----|
| Added `_augment_one` module-level function and `multiprocessing.Pool` branch | Required to actually achieve parallel execution; pickling error caught when first attempting a lambda |
| Added `tqdm` progress bar | Better user feedback for long batches; guarded with `disable=not self.show_progress` to keep tests clean |
| Accepted `str` for `augmenter` arg | UI page needed to pass a selectbox string value without constructing `DocumentAugmenter` separately |

No additional tests were added post-refactor; parallel execution is not tested (avoids subprocess overhead in CI).

### How to Run

```bash
uv run pytest tests/test_batch_processing.py -v
uv run pytest tests/test_batch_processing.py --cov=document_simulator.augmentation.batch
```

---

## Dependencies

### Requires

| Dependency | Kind | Why |
|------------|------|-----|
| `augmentation/augmenter.py` | internal | `DocumentAugmenter` — the per-image worker |
| `utils/image_io.py` | internal | Load paths; save output images in `augment_directory` |
| `multiprocessing` | stdlib | `Pool.imap` for parallelism |
| `tqdm` | external | Progress bar (optional) |

### Required By

| Consumer | How it uses this feature |
|----------|------------------------|
| `ui/pages/03_batch_processing.py` | Constructs `BatchAugmenter` from UI controls, calls `augment_batch()`, builds ZIP |
| `tests/integration/test_augmentation_ocr.py` | Tests `augment_directory()` as an integration scenario |

---

## Usage Examples

### Minimal

```python
from document_simulator.augmentation.batch import BatchAugmenter

results = BatchAugmenter(num_workers=1).augment_batch(images, parallel=False)
```

### Typical

```python
from document_simulator.augmentation.batch import BatchAugmenter
from pathlib import Path

batch = BatchAugmenter(augmenter="medium", num_workers=4, show_progress=True)
batch.augment_directory(Path("data/raw"), Path("data/augmented"))
```

### Advanced / Edge Case

```python
# Mix PIL Images and file paths in the same batch
from PIL import Image
from pathlib import Path

batch = BatchAugmenter("light", num_workers=1)
mixed_inputs = [Image.open("a.jpg"), Path("b.png")]
results = batch.augment_batch(mixed_inputs, parallel=False)
```

---

## Future Work

- [ ] Add `augment_directory()` support for recursive subdirectory traversal.
- [ ] Expose `chunk_size` parameter to tune `Pool.imap` memory usage for very large batches.
- [ ] Stream results to disk in `augment_batch()` when a `output_dir` kwarg is provided.

---

## References

- [feature_document_augmenter.md](feature_document_augmenter.md)
- [IMPLEMENTATION_PLAN.md — Phase 1](../IMPLEMENTATION_PLAN.md)
