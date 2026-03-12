# Feature: Multi-Template Batch Augmentation

> **GitHub Issue:** `#22`
> **Status:** `done`
> **Module:** `document_simulator.augmentation.batch` + `document_simulator.ui.pages.03_batch_processing`

---

## Summary

Extends `BatchAugmenter` and the Batch Processing UI page to support **multi-template batch
augmentation**: given N input document images, generate M total augmented outputs where each
output randomly picks one input template as its source, then applies the selected augmentation
pipeline on top.

Two modes are supported:

- **N×M mode (`per_template`)** — generate `copies_per_template` augmented copies of every input,
  producing `N × copies_per_template` total outputs.
- **M-total mode (`random_sample`)** — generate exactly `total_outputs` outputs by sampling
  randomly (with replacement) from the N input templates.

---

## Motivation

### Problem Statement

The existing `BatchAugmenter.augment_batch` produces one augmented copy per input image (1:1
mapping). Generating a large training set from a small number of document templates requires
either calling the method multiple times or writing custom loops. Neither scales well from the
Streamlit UI.

### Value Delivered

- Generate large augmented training datasets from a handful of reference templates in one click.
- N×M mode guarantees balanced representation across all templates.
- M-total random mode produces a naturally distributed dataset useful for testing model
  generalisation.
- Seeded random selection makes runs reproducible.
- Backward-compatible — the existing single-template batch flow is unchanged.

---

## User Stories

| Role | Goal | So That |
|------|------|---------|
| ML engineer | I can upload 5 receipt templates and generate 200 augmented copies | I have a balanced training set without scripting |
| Data scientist | I can set a fixed random seed for M-total mode | My augmented dataset is reproducible across runs |
| Non-technical user | I can see how many outputs will be generated before I run | I avoid accidentally generating 500 images |

---

## Acceptance Criteria

- [x] AC-1: `BatchAugmenter.augment_multi_template(sources, mode="per_template", copies_per_template=3)` with N=2 sources returns exactly 6 `(Image, stem)` tuples.
- [x] AC-2: `BatchAugmenter.augment_multi_template(sources, mode="random_sample", total_outputs=10, seed=42)` with N=3 sources returns exactly 10 tuples and the same sequence is returned with the same seed on a second call.
- [x] AC-3: `augment_multi_template` with `copies_per_template=0` raises `ValueError`.
- [x] AC-4: `augment_multi_template` with `total_outputs=0` raises `ValueError`.
- [x] AC-5: `augment_multi_template` with an empty `sources` list raises `ValueError`.
- [x] AC-6: Each returned tuple is `(PIL.Image.Image, str)` where the string is a safe filename stem.
- [x] AC-7: The existing `augment_batch` method signature and behaviour are unchanged; all 8 existing `test_batch_processing.py` tests pass.
- [x] AC-8: The Batch Processing page loads without error after UI changes.
- [x] AC-9: The sidebar exposes an "Augmentation mode" radio with at least three options.
- [x] AC-10: Selecting N×M mode shows a "Copies per template" number input.
- [x] AC-11: Selecting M-total mode shows a "Total outputs (M)" number input.
- [x] AC-12: When results from `augment_multi_template` are in session state, the "Processed" metric reflects the correct count.
- [x] AC-13: ZIP filename pattern for N×M mode is `{source_stem}_{copy_idx:03d}.png`.
- [x] AC-14: ZIP filename pattern for M-total mode is `{source_stem}_{global_idx:04d}.png`.
- [x] AC-15: `SessionStateManager` exposes typed getters/setters for all new batch keys.

---

## Design

### Public API

```python
from document_simulator.augmentation.batch import BatchAugmenter
from PIL import Image

sources = [Image.open("template_a.png"), Image.open("template_b.png")]

# N×M mode: 2 templates × 3 copies = 6 outputs
batch = BatchAugmenter(augmenter="medium", num_workers=4)
results = batch.augment_multi_template(
    sources,
    mode="per_template",
    copies_per_template=3,
)
# results: List[tuple[Image.Image, str]]
# e.g. [(aug_img, "template_a"), (aug_img, "template_a"), ..., (aug_img, "template_b"), ...]

# M-total mode: 10 outputs sampled randomly from 2 templates
results = batch.augment_multi_template(
    sources,
    mode="random_sample",
    total_outputs=10,
    seed=42,
)
```

### Data Flow

```
User uploads N images (templates)
    │
    ▼
User selects mode: "per_template" | "random_sample"
User enters copies_per_template  OR  total_outputs
(Optional) User enters random seed
User clicks "Run Batch Augmentation"
    │
    ▼
[Mode: per_template]
  Expand: [(img_0, stem_0)×M, (img_1, stem_1)×M, ...]
    │
[Mode: random_sample]
  random.Random(seed).choices(sources_with_stems, k=total_outputs)
    │
    ▼
augment_batch(selected_images)   ← reuses existing parallel machinery
    │
    ▼
Pair results with stems → List[tuple[Image, str]]
    │
    ▼
state.set_batch_results(images)
Build ZIP: {stem}_{idx:03d}.png / {stem}_{idx:04d}.png
st.download_button(zip_bytes)
Thumbnail grid (up to 8)
```

### Key Interfaces

| Symbol | Kind | Responsibility |
|--------|------|---------------|
| `BatchAugmenter.augment_multi_template` | method | Core multi-template logic; returns `List[tuple[Image, str]]` |
| `SessionStateManager.get/set_batch_mode` | methods | Typed accessor for `"batch_mode"` key |
| `SessionStateManager.get/set_batch_copies_per_tpl` | methods | Typed accessor for `"batch_copies_per_tpl"` key |
| `SessionStateManager.get/set_batch_total_outputs` | methods | Typed accessor for `"batch_total_outputs"` key |
| `SessionStateManager.get/set_batch_seed` | methods | Typed accessor for `"batch_seed"` key |

### Configuration

No new `.env` settings. All parameters are runtime inputs via the Streamlit UI or direct API call.

---

## Implementation

### Files

| Path | Role |
|------|------|
| `src/document_simulator/augmentation/batch.py` | Add `augment_multi_template` method |
| `src/document_simulator/ui/pages/03_batch_processing.py` | Add mode radio, conditional inputs, new ZIP logic |
| `src/document_simulator/ui/state/session_state.py` | Add four new batch key constants and typed accessors |
| `tests/unit/test_multi_template_batch.py` | Unit tests for `augment_multi_template` |
| `tests/ui/integration/test_multi_template_batch_ui.py` | UI integration tests for the updated page |

### Key Architectural Decisions

1. **New method, not modified signature** — `augment_multi_template` is a separate method so
   `augment_batch` remains unchanged. This preserves backward compatibility for all existing callers
   including the CLI and existing tests.

2. **Returns `List[tuple[Image, str]]`** — bundling the source stem with the image avoids a
   separate parallel list for ZIP naming. The UI page unpacks the tuples when building the ZIP.

3. **`random.Random(seed)` instance** — avoids global random state mutation, which would break
   tests running in the same process that rely on deterministic random values elsewhere.

4. **Reuses `augment_batch` internally** — after expanding/sampling the source list,
   `augment_multi_template` calls `self.augment_batch(selected_images, parallel=parallel)` to
   reuse the existing Pool machinery. This avoids duplicating the multiprocessing logic.

5. **`seed=None` means unseeded** — when `seed` is `None`, a fresh `random.Random()` instance is
   used (system entropy), so each run produces a different sample. When `seed=0` is passed
   explicitly from the UI number input, it is treated as a real seed.

### Known Edge Cases & Constraints

- `copies_per_template` must be >= 1; validated with `ValueError`.
- `total_outputs` must be >= 1; validated with `ValueError`.
- `sources` must be non-empty; validated with `ValueError`.
- ZIP collisions in M-total mode are prevented by the global index suffix.
- Multiprocessing `spawn` on macOS has process-start overhead; first run is slower.
- `st.download_button` is not accessible in AppTest — tests check `at.metric` counts.

---

## Tests

### Test Files

| File | Type | Count | What is covered |
|------|------|-------|-----------------|
| `tests/unit/test_multi_template_batch.py` | unit | 13 | `augment_multi_template` per_template count, random_sample count, seed reproducibility, ValueError cases, stem naming, grouping, existing `augment_batch` backward compat |
| `tests/ui/integration/test_multi_template_batch_ui.py` | integration | 10 | Page load, run button, preset selectbox, worker slider, mode radio present, 3+ options, copies input for N×M, total input for M-total, metrics after results, processed count correct |

### TDD Cycle Summary

**Red — first failing tests written:**

| Test name | File | Initial failure reason |
|-----------|------|----------------------|
| `test_per_template_output_count` | `test_multi_template_batch.py` | `AttributeError: 'BatchAugmenter' object has no attribute 'augment_multi_template'` |
| `test_random_sample_output_count` | `test_multi_template_batch.py` | same |
| `test_seed_reproducibility` | `test_multi_template_batch.py` | same |
| `test_multi_template_ui_has_mode_radio` | `test_multi_template_batch_ui.py` | `AssertionError: no radio widget found` |

**Green — minimal implementation:**

Added `augment_multi_template` to `BatchAugmenter` with per_template and random_sample branches.
Added mode radio and conditional inputs to `03_batch_processing.py`. Added new keys to
`SessionStateManager`. All 23 new tests green; all 338 project tests green.

**Refactor — improvements made after green:**

| What changed | Why |
|--------------|-----|
| Extracted `_build_zip_multi` helper in page | ZIP logic was duplicated for both new modes |
| Added stem sanitisation (`re.sub`) | Filenames from PDF page labels contained spaces and dashes |

### How to Run

```bash
# Unit tests for new multi-template logic
uv run pytest tests/unit/test_multi_template_batch.py -v

# UI integration tests
uv run pytest tests/ui/integration/test_multi_template_batch_ui.py -v

# All batch tests (must still pass)
uv run pytest tests/test_batch_processing.py tests/ui/integration/test_batch_processing.py -v

# Full suite
uv run pytest tests/ -q --no-cov
```

---

## Dependencies

### Requires

| Dependency | Kind | Why |
|------------|------|-----|
| `augmentation/batch.py` | internal | Extended with new method |
| `ui/state/session_state.py` | internal | New typed accessors |
| `random` | stdlib | Seeded sampling via `random.Random` |
| `PIL` | external | Source images |

### Required By

| Consumer | How it uses this feature |
|----------|------------------------|
| `ui/pages/03_batch_processing.py` | Calls `augment_multi_template` in N×M and M-total modes |

---

## Usage Examples

### Minimal

```python
from document_simulator.augmentation.batch import BatchAugmenter
from PIL import Image

sources = [Image.new("RGB", (200, 200), color) for color in ["white", "lightgrey"]]
batch = BatchAugmenter(num_workers=1)
results = batch.augment_multi_template(sources, mode="per_template", copies_per_template=2)
# 4 (image, stem) tuples
```

### Typical

```python
# Generate 50 training samples from 5 templates, reproducibly
batch = BatchAugmenter(augmenter="medium", num_workers=4)
results = batch.augment_multi_template(
    sources=source_images,     # List[PIL.Image], N=5
    mode="random_sample",
    total_outputs=50,
    seed=2026,
    parallel=True,
)
for aug_img, stem in results:
    aug_img.save(f"output/{stem}.png")
```

### Advanced / Edge Case

```python
# N×M: 10 templates × 20 copies = 200 augmented outputs
results = batch.augment_multi_template(
    sources,
    mode="per_template",
    copies_per_template=20,
)
# Results grouped: first 20 entries come from sources[0], next 20 from sources[1], etc.
for i, (img, stem) in enumerate(results):
    img.save(f"output/{stem}_{i:03d}.png")
```

---

## Future Work

- [ ] Weighted sampling — allow per-template weights so underrepresented document types are over-sampled.
- [ ] Progress reporting per-template in N×M mode (currently progress bar covers the full batch).
- [ ] Support `augment_directory` multi-template variant for CLI use.

---

## Signoff

| Role | Name | Date | Status |
|------|------|------|--------|
| Author | Claude Sonnet 4.6 | 2026-03-07 | approved |
| Tests | 338 passing (23 new) | 2026-03-07 | green |
| Branch | `feature/multi-template-batch-augmentation` | 2026-03-07 | merged via PR |

---

## References

- [feature_batch_processing.md](feature_batch_processing.md)
- [feature_ui_batch_processing.md](feature_ui_batch_processing.md)
- [RESEARCH_FINDINGS.md — Multi-Template Batch Augmentation section](../RESEARCH_FINDINGS.md)
- [Python `random.Random` documentation](https://docs.python.org/3/library/random.html#random.Random)
