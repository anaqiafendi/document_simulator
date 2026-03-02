# Feature: Image I/O Utilities

> **GitHub Issue:** `#6`
> **Status:** `complete`
> **Module:** `document_simulator.utils.image_io`

---

## Summary

`ImageHandler` provides a single static interface for loading images from five source types (file path, str, PIL Image, numpy array, bytes) and saving images to disk. It always returns PIL Images in RGB mode, eliminating type-checking boilerplate throughout the codebase.

---

## Motivation

### Problem Statement

Every module that handles images (augmentation, dataset loading, batch processing) was writing its own `isinstance(image, Path)` / `Image.open()` / `np.array()` conversion chains independently. This was duplicated, untested, and handled edge cases (grayscale, RGBA, bytes) inconsistently.

### Value Delivered

- One place to fix image loading bugs — four lines change everywhere simultaneously.
- Callers receive `PIL Image RGB` unconditionally; no downstream mode checks needed.
- `FileNotFoundError` and `TypeError` with descriptive messages rather than cryptic PIL exceptions.
- `load_batch()` makes dataset loaders a one-liner.

---

## User Stories

| Role | Goal | So That |
|------|------|---------|
| Developer | I call `ImageHandler.load(source)` with any type | I always get a PIL Image RGB back |
| Batch processor | I call `load_batch(sources)` | I can mix paths and arrays in one call |
| Augmenter | I call `save(image, path)` | Parent directories are created automatically |

---

## Acceptance Criteria

- [ ] AC-1: `ImageHandler.load(Path("img.png"))` returns a PIL Image of mode `"RGB"`.
- [ ] AC-2: `ImageHandler.load(pil_image)` returns a PIL Image (no copy required).
- [ ] AC-3: `ImageHandler.load(numpy_array)` returns a PIL Image.
- [ ] AC-4: `ImageHandler.load(bytes_data)` returns a PIL Image of the correct size.
- [ ] AC-5: `ImageHandler.load("/nonexistent")` raises `FileNotFoundError`.
- [ ] AC-6: `ImageHandler.load(b"garbage")` raises `UnidentifiedImageError` or similar.
- [ ] AC-7: `ImageHandler.load(12345)` raises `TypeError`.
- [ ] AC-8: `ImageHandler.save(image, nested/path/img.png)` creates parent directories.
- [ ] AC-9: `ImageHandler.to_numpy(pil_image)` returns a `np.ndarray` with `dtype=uint8`.
- [ ] AC-10: `ImageHandler.to_grayscale(image)` returns a PIL Image with mode `"L"`.

---

## Design

### Public API

```python
from document_simulator.utils.image_io import ImageHandler

img: Image.Image = ImageHandler.load(source)       # str | Path | PIL | numpy | bytes
ImageHandler.save(image, Path("out/img.png"))       # creates parent dirs
arr: np.ndarray  = ImageHandler.to_numpy(image)
pil: Image.Image = ImageHandler.to_pil(image)
gray: Image.Image = ImageHandler.to_grayscale(image)
imgs: list[Image.Image] = ImageHandler.load_batch(sources)
```

### Data Flow

```
ImageHandler.load(source)
    │
    ├─► isinstance str/Path → Image.open(path).convert("RGB")
    ├─► isinstance PIL      → source.convert("RGB")
    ├─► isinstance numpy    → Image.fromarray(source).convert("RGB")
    ├─► isinstance bytes    → Image.open(BytesIO(source)).convert("RGB")
    └─► else                → raise TypeError
```

### Key Interfaces

| Symbol | Kind | Responsibility |
|--------|------|---------------|
| `ImageHandler.load(source)` | static method | Multi-type load → RGB PIL |
| `ImageHandler.save(image, path)` | static method | PIL or numpy → disk; creates dirs |
| `ImageHandler.to_numpy(image)` | static method | PIL or numpy → uint8 ndarray (identity for numpy) |
| `ImageHandler.to_pil(image)` | static method | numpy or PIL → RGB PIL |
| `ImageHandler.to_grayscale(image)` | static method | Any → PIL mode 'L' |
| `ImageHandler.load_batch(sources)` | static method | List of any source → list of PIL |

### Configuration

No `.env` settings.

---

## Implementation

### Files

| Path | Role |
|------|------|
| `src/document_simulator/utils/image_io.py` | Complete implementation — single class, all static methods |

### Key Architectural Decisions

1. **Always convert to RGB** — RGBA, L (grayscale), P (palette) inputs silently break downstream numpy shape assumptions (`(H, W, 3)` expected everywhere). A single `.convert("RGB")` at load time is simpler than defending every consumer.

2. **All static methods** — `ImageHandler` holds no state. Using a class rather than module-level functions allows `from document_simulator.utils.image_io import ImageHandler` as a single clean import.

3. **`to_numpy` is identity for numpy input** — Returns the array as-is (no copy) to avoid the overhead of a redundant conversion when the caller already has a numpy array. This is documented and tested (`assert arr is rgb_numpy`).

4. **Specific exceptions with context** — `FileNotFoundError(f"Image file not found: {path}")` is more actionable than PIL's `FileNotFoundError: [Errno 2]`. `TypeError` includes the actual type name for quick diagnosis.

### Known Edge Cases & Constraints

- `load(pil_image)` always calls `.convert("RGB")` even if the image is already RGB. This is a safe no-op in PIL but creates a copy.
- Very large images are loaded entirely into memory — no streaming support.

---

## Tests

### Test Files

| File | Type | Count | What is covered |
|------|------|-------|-----------------|
| `tests/unit/test_image_handlers.py` | unit | 18 | `load()` (9), `save()` (3), `to_numpy`/`to_pil` (4), `to_grayscale` (1), `load_batch` (1) |

### TDD Cycle Summary

**Red — first failing tests written:**

| Test name | File | Initial failure reason |
|-----------|------|----------------------|
| `test_load_from_path` | `tests/unit/test_image_handlers.py` | `ImportError: cannot import name 'ImageHandler'` |
| `test_load_invalid_path` | `tests/unit/test_image_handlers.py` | `ImportError: cannot import name 'ImageHandler'` |
| `test_load_unsupported_type` | `tests/unit/test_image_handlers.py` | `ImportError: cannot import name 'ImageHandler'` |
| `test_save_creates_parent_dirs` | `tests/unit/test_image_handlers.py` | `ImportError: cannot import name 'ImageHandler'` |

**Green — minimal implementation:**

Implemented `load()` with `isinstance` chain in the order: `str/Path → PIL → numpy → bytes → raise TypeError`. Added `save()` with `path.parent.mkdir(parents=True, exist_ok=True)`. All 18 tests passed after the initial implementation — no partial green phase.

**Refactor — improvements made after green:**

| What changed | Why |
|--------------|-----|
| Added `load_batch()` convenience method | `DocumentDataset` and `BatchAugmenter` both needed to load lists of images; extracting the loop avoided duplication |
| Used `io.BytesIO` in the bytes branch rather than `tempfile` | Avoids disk I/O in the bytes loading path; `BytesIO` is already available from stdlib |

### How to Run

```bash
uv run pytest tests/unit/test_image_handlers.py -v
uv run pytest tests/unit/test_image_handlers.py --cov=document_simulator.utils.image_io
```

---

## Dependencies

### Requires

| Dependency | Kind | Why |
|------------|------|-----|
| `PIL` (Pillow) | external | Image loading, conversion, saving |
| `numpy` | external | Array conversion |
| `io` | stdlib | `BytesIO` for bytes-to-image loading |
| `pathlib` | stdlib | Path handling |

### Required By

| Consumer | How it uses this feature |
|----------|------------------------|
| `augmentation/batch.py` | `load()` for path inputs; `save()` in `augment_directory()` |
| `data/datasets.py` | `load()` in `__getitem__()` |
| `ui/components/image_display.py` | `to_numpy()` implicitly via PIL conversion for bbox drawing |

---

## Usage Examples

### Minimal

```python
from document_simulator.utils.image_io import ImageHandler

image = ImageHandler.load("scan.tiff")
```

### Typical

```python
from document_simulator.utils.image_io import ImageHandler
from pathlib import Path

# Load, process, save
image = ImageHandler.load(Path("input/doc.jpg"))
arr = ImageHandler.to_numpy(image)
# ... process arr ...
ImageHandler.save(Image.fromarray(arr), Path("output/doc_processed.png"))
```

### Advanced / Edge Case

```python
# Load from raw bytes (e.g., from an HTTP response or uploaded file)
response_bytes = requests.get(url).content
image = ImageHandler.load(response_bytes)

# Batch load mixed sources
images = ImageHandler.load_batch([
    Path("scan1.jpg"),
    existing_pil_image,
    numpy_array,
])
```

---

## Future Work

- [ ] Add streaming load for very large images (tile-based).
- [ ] Add `load_from_url(url)` using `requests` + `BytesIO`.
- [ ] Add format detection and EXIF-based auto-rotation.

---

## References

- [IMPLEMENTATION_PLAN.md — Phase 2](../IMPLEMENTATION_PLAN.md)
