# Feature: Document Dataset

> **GitHub Issue:** `#8`
> **Status:** `complete`
> **Module:** `document_simulator.data.datasets`

---

## Summary

`DocumentDataset` is a PyTorch-compatible `Dataset` that auto-discovers image/annotation pairs in a directory (matching `.png`/`.jpg` etc. against `.json`/`.xml` siblings), exposes them via `__getitem__`, and provides a reproducible train/val/test split via `split()`.

---

## Motivation

### Problem Statement

The RL environment and the evaluator need to iterate labelled document samples. Without a standard dataset abstraction, both would need to re-implement directory scanning, annotation loading, and train/val splitting — and would be incompatible with PyTorch `DataLoader`.

### Value Delivered

- Drop-in with PyTorch `DataLoader(dataset, batch_size=...)`.
- Auto-discovery: no manifest file required, only a predictable directory layout.
- Reproducible splits via a seeded `random.Random` — the same seed always produces the same partition.
- Unannotated images (no matching `.json` / `.xml`) are silently skipped.
- Optional `transform` callable applied at load time.

---

## User Stories

| Role | Goal | So That |
|------|------|---------|
| ML researcher | I pass `DocumentDataset(data_dir)` to `DataLoader` | I get batches of (image, ground_truth) pairs |
| Evaluator | I call `evaluator.evaluate_dataset(dataset)` | CER/WER is computed across a full labelled set |
| RL trainer | I pass `dataset_path` to `DocumentEnv` | The environment draws random samples from real documents |

---

## Acceptance Criteria

- [ ] AC-1: `DocumentDataset(dir_with_5_pairs)` has `len() == 5`.
- [ ] AC-2: `dataset[0]` returns `(PIL Image, GroundTruth)`.
- [ ] AC-3: An empty directory returns `len() == 0`.
- [ ] AC-4: A directory with images but no annotations returns `len() == 0`.
- [ ] AC-5: `split(val_ratio=0.2, test_ratio=0.2)` returns three subsets that together cover all samples with no overlap.
- [ ] AC-6: Same `seed` produces the same partition on two separate calls.
- [ ] AC-7: A `transform` callable is applied to the image in `__getitem__`.

---

## Design

### Public API

```python
from document_simulator.data.datasets import DocumentDataset

dataset = DocumentDataset(Path("data/train"))
train, val, test = dataset.split(val_ratio=0.1, test_ratio=0.1, seed=42)

image, gt = dataset[0]      # PIL Image, GroundTruth
len(dataset)                # number of discovered image/annotation pairs
```

### Data Flow

```
DocumentDataset(data_dir)
    │
    ▼
_discover_samples()
    iterate sorted(data_dir.iterdir())
    for each image file → look for .json or .xml sibling
    collect (img_path, gt_path) pairs
    │
    ▼
__getitem__(idx)
    │
    ├─► ImageHandler.load(img_path)     → PIL Image
    ├─► GroundTruthLoader.detect_and_load(gt_path) → GroundTruth
    └─► transform(image) if transform is not None
    │
    ▼
(PIL Image, GroundTruth)
```

### Key Interfaces

| Symbol | Kind | Responsibility |
|--------|------|---------------|
| `DocumentDataset(data_dir, image_extensions, transform)` | class | Auto-discover pairs and expose PyTorch Dataset protocol |
| `__len__()` | method | Number of discovered pairs |
| `__getitem__(idx)` | method | Load and return (image, gt) at index |
| `split(val_ratio, test_ratio, seed)` | method | Reproducible train/val/test partitions |
| `_SubsetDataset(parent, indices)` | internal class | Index-based view, bypasses `__init__` scanning |

### Configuration

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `image_extensions` | `list[str]` | `{".jpg", ".jpeg", ".png", ".tiff", ".bmp"}` | File extensions treated as images |

---

## Implementation

### Files

| Path | Role |
|------|------|
| `src/document_simulator/data/datasets.py` | Primary implementation + `_SubsetDataset` |
| `src/document_simulator/data/ground_truth.py` | `GroundTruthLoader.detect_and_load()` called in `__getitem__` |
| `src/document_simulator/utils/image_io.py` | `ImageHandler.load()` called in `__getitem__` |

### Key Architectural Decisions

1. **Discovery at `__init__`, loading at `__getitem__`** — Scanning the directory once at construction is fast (metadata only). Loading images at access time avoids holding the entire dataset in memory, which is the standard PyTorch pattern.

2. **`_SubsetDataset` bypasses `__init__`** — Subsets are created by `_SubsetDataset.__init__`, which directly assigns the pre-filtered `_samples` list without re-scanning the directory. This avoids creating temporary directories for split views.

3. **`random.Random(seed)` not `numpy.random`** — Using stdlib `random.Random` means the split is reproducible without NumPy and does not interfere with NumPy's global seed (which affects RL training).

4. **`split()` guarantees no overlap** — Test indices are taken first, then val, then train. This matches the convention that test set composition is fixed before any training decision.

### Known Edge Cases & Constraints

- Images without a matching annotation file are silently skipped — no warning is logged. This is intentional to handle mixed directories, but may be confusing if annotations are accidentally misnamed.
- Very large datasets with thousands of files may have a noticeable `__init__` scan time.

---

## Tests

### Test Files

| File | Type | Count | What is covered |
|------|------|-------|-----------------|
| `tests/test_datasets.py` | unit | 10 | Load (4), empty dir (1), unannotated skip (1), split coverage/no-overlap/reproducibility (3), transform (1) |
| `tests/integration/test_augmentation_ocr.py` | integration | 1 | Dataset load + augmentation round-trip |

### TDD Cycle Summary

**Red — first failing tests written:**

| Test name | File | Initial failure reason |
|-----------|------|----------------------|
| `test_load_custom_dataset` | `tests/test_datasets.py` | `ImportError: cannot import name 'DocumentDataset'` |
| `test_dataset_split_no_overlap` | `tests/test_datasets.py` | `ImportError: cannot import name 'DocumentDataset'` |
| `test_dataset_ignores_files_without_annotation` | `tests/test_datasets.py` | `ImportError: cannot import name 'DocumentDataset'` |

**Green — minimal implementation:**

Created `DocumentDataset` with `_discover_samples()` iterating `data_dir.iterdir()`, `__len__`, and `__getitem__`. Implemented `split()` using `random.shuffle` on an index list. All 10 tests passed after the initial implementation.

**Refactor — improvements made after green:**

| What changed | Why |
|--------------|-----|
| Replaced `random.shuffle(indices)` with `random.Random(seed).shuffle(indices)` | `test_dataset_split_reproducible` revealed that the global `random.shuffle` was seeded by the previous test's randomness — the same seed argument produced different results across pytest runs |
| Extracted `_SubsetDataset` | `split()` originally returned three new `DocumentDataset` instances with filtered `_samples`, but constructing a `DocumentDataset` re-scans the directory. `_SubsetDataset` bypasses the scan entirely |

### How to Run

```bash
uv run pytest tests/test_datasets.py -v
uv run pytest tests/test_datasets.py --cov=document_simulator.data.datasets
```

---

## Dependencies

### Requires

| Dependency | Kind | Why |
|------------|------|-----|
| `torch.utils.data.Dataset` | external | Base class for PyTorch compatibility |
| `data/ground_truth.py` | internal | `GroundTruthLoader.detect_and_load()` |
| `utils/image_io.py` | internal | `ImageHandler.load()` |
| `random` | stdlib | Seeded shuffle for reproducible splits |

### Required By

| Consumer | How it uses this feature |
|----------|------------------------|
| `evaluation/evaluator.py` | `evaluate_dataset(dataset)` iterates all samples |
| `rl/environment.py` | `DocumentEnv.__init__` constructs `DocumentDataset(dataset_path)` |
| `ui/pages/04_evaluation.py` | Constructs `DocumentDataset(data_dir)` from user-provided path |

---

## Usage Examples

### Minimal

```python
from document_simulator.data.datasets import DocumentDataset

dataset = DocumentDataset(Path("data/train"))
image, gt = dataset[0]
```

### Typical

```python
from document_simulator.data.datasets import DocumentDataset
from torch.utils.data import DataLoader

dataset = DocumentDataset(Path("data/labelled"))
train, val, test = dataset.split(val_ratio=0.1, test_ratio=0.1, seed=42)
loader = DataLoader(train, batch_size=8, shuffle=True)
```

### Advanced / Edge Case

```python
import torchvision.transforms as T

transform = T.Compose([T.Resize((224, 224)), T.ToTensor()])
dataset = DocumentDataset(Path("data"), transform=transform)
image, gt = dataset[0]
# image is now a torch.Tensor of shape (3, 224, 224)
```

---

## Future Work

- [ ] Add `augment_dataset(augmenter)` that returns a new dataset of augmented pairs.
- [ ] Support recursive directory traversal.
- [ ] Log a warning when images without matching annotations are skipped.

---

## References

- [feature_ground_truth.md](feature_ground_truth.md)
- [IMPLEMENTATION_PLAN.md — Phase 2](../IMPLEMENTATION_PLAN.md)
