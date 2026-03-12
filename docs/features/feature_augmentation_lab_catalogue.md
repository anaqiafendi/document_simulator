# Feature: Augmentation Lab Catalogue

> **GitHub Issue:** `#21`
> **Status:** `in-progress`
> **Module:** `document_simulator.augmentation.catalogue`, `document_simulator.ui.pages.01_augmentation_lab`

---

## Summary

Adds a **Catalogue** tab to the Augmentation Lab page where every Augraphy augmentation available in version 8.2.6 appears as an interactive card grouped by pipeline phase (Ink / Paper / Post). Users toggle individual augmentations on/off, tune per-augmentation parameters via sliders, preview the effect as a lazily-generated thumbnail, then compose a fully custom pipeline and augment their uploaded document.

---

## Motivation

### Problem Statement

The existing Augmentation Lab page offers only three coarse presets (light / medium / heavy). Users who want to isolate the visual effect of a single augmentation (e.g., `ShadowCast` vs `BleedThrough`), or compose a novel pipeline, have no UI path — they must write Python. The 12 sliders in the advanced expander exist but are display-only and do not feed back into `DocumentAugmenter`.

### Value Delivered

- Browse all 23 catalogue entries (covering the most useful subset of augraphy 8.2.6's 51 classes) as visual thumbnail cards.
- Toggle any augmentation on/off without writing code.
- Tune 1–3 key parameters per augmentation via sliders that actually drive the preview.
- Thumbnails generated lazily on toggle and cached in session state — never blocks the full page render.
- Custom pipeline composed from enabled augmentations runs via `DocumentAugmenter(custom_augmentations=[...])`.
- Preset mode (light / medium / heavy) remains fully unchanged — existing tests continue to pass.

---

## User Stories

| Role | Goal | So That |
|------|------|---------|
| Researcher | I enable InkBleed and BadPhotoCopy and adjust their sliders | I see exactly how each augmentation degrades my document independently |
| Data engineer | I compose a custom 4-augmentation pipeline in the Catalogue tab | I generate a specific degradation pattern not available in the presets |
| Developer | I toggle Jpeg and see the thumbnail update instantly | I verify the JPEG quality slider is wired correctly |
| QA reviewer | I switch back to the Preset tab | I confirm the original preset workflow is completely unchanged |

---

## Acceptance Criteria

- [ ] AC-1: Page loads without error with a "Catalogue" tab visible alongside preset mode.
- [ ] AC-2: `augmentation/catalogue.py` exports `CATALOGUE` dict with ≥20 entries, each having `phase`, `display_name`, `default_params` keys.
- [ ] AC-3: `DocumentAugmenter(custom_augmentations=[...])` runs the supplied list instead of a preset.
- [ ] AC-4: Catalogue tab shows augmentation cards grouped by phase (Ink / Paper / Post) in a 4-column grid.
- [ ] AC-5: Each card has a checkbox to enable/disable the augmentation.
- [ ] AC-6: Each enabled card has sliders for its key parameters.
- [ ] AC-7: Thumbnail for each enabled augmentation is generated lazily (on toggle, not on page load) and cached in session state.
- [ ] AC-8: "Generate (catalogue)" button applies the composed custom pipeline and shows before/after.
- [ ] AC-9: Preset mode (light/medium/heavy) continues to work unchanged.
- [ ] AC-10: Existing augmentation lab tests pass unchanged.

---

## Design

### Public API

```python
# New module — static catalogue
from document_simulator.augmentation.catalogue import CATALOGUE, get_phase_augmentations, apply_single

# Dict with ≥20 entries
entry = CATALOGUE["InkBleed"]
# {"display_name": "Ink Bleed", "phase": "ink", "description": "...",
#  "slow": False, "default_params": {...}}

# Get all ink-phase augmentations
ink_augs = get_phase_augmentations("ink")

# Apply a single augmentation by name
result_pil = apply_single("Jpeg", pil_image, params={"quality_range": (40, 80), "p": 1.0})

# DocumentAugmenter — new custom_augmentations param (backward-compatible)
from document_simulator.augmentation import DocumentAugmenter
import augraphy.augmentations as aug_module

aug = DocumentAugmenter(
    custom_augmentations=[
        aug_module.Jpeg(quality_range=(40, 80), p=1.0),
        aug_module.Gamma(p=1.0),
    ]
)
result = aug.augment(pil_image)
```

### Data Flow

```
User uploads image
    │
    ▼
Image resized to 256×256 → stored as aug_catalogue_source in session state
    │
    ▼
User toggles checkbox for "Jpeg" ON
    │
    ▼
apply_single("Jpeg", thumbnail, params) called
    │
    ▼
Result cached as PNG bytes in st.session_state["aug_catalogue_thumbnails"]["Jpeg"]
    │
    ▼
Card shows cached thumbnail
    │
    ▼
User clicks "Generate (catalogue)"
    │
    ▼
DocumentAugmenter(custom_augmentations=[enabled_augs]).augment(full_src)
    │
    ▼
show_side_by_side(original, result) + download button
```

### Key Interfaces

| Symbol | Kind | Responsibility |
|--------|------|---------------|
| `CATALOGUE` | `dict[str, dict]` | Static metadata for all 23 catalogue entries |
| `get_phase_augmentations(phase)` | function | Filter CATALOGUE by phase string |
| `apply_single(aug_name, image, params)` | function | Instantiate + run one augmentation |
| `DocumentAugmenter(custom_augmentations=[...])` | class | Custom pipeline path bypassing PresetFactory |
| `SessionStateManager.get/set_aug_mode()` | method | "preset" or "catalogue" |
| `SessionStateManager.get/set_aug_catalogue_enabled()` | method | `{aug_name: bool}` |
| `SessionStateManager.get/set_aug_catalogue_params()` | method | `{aug_name: {param: value}}` |
| `SessionStateManager.get/set_aug_catalogue_thumbnails()` | method | `{aug_name: png_bytes}` |

### Configuration

No new `.env` settings — all configuration is driven through the UI.

---

## Implementation

### Files

| Path | Role |
|------|------|
| `src/document_simulator/augmentation/catalogue.py` | New — static catalogue dict + helpers |
| `src/document_simulator/augmentation/augmenter.py` | Modified — add `custom_augmentations` param |
| `src/document_simulator/ui/pages/01_augmentation_lab.py` | Modified — add Catalogue tab |
| `src/document_simulator/ui/state/session_state.py` | Modified — add 4 new catalogue state keys |
| `tests/augmentation/__init__.py` | New — empty package marker |
| `tests/augmentation/test_catalogue.py` | New — unit tests for catalogue module |
| `tests/unit/test_augmentation_custom.py` | New — unit tests for custom_augmentations param |
| `tests/ui/integration/test_augmentation_lab_catalogue.py` | New — UI integration tests |

### Key Architectural Decisions

1. **Static catalogue dict, not runtime inspection** — Importing all 51 Augraphy classes at page load adds ~0.5–1 s. A static dict avoids this; the dict is the single source of truth for phase, display name, and default params.

2. **Phase separation via CATALOGUE metadata** — Augraphy augmentation objects don't carry a `_phase` attribute. The catalogue dict tracks phase externally. `DocumentAugmenter` looks up each object's class name in `CATALOGUE` to split into ink/paper/post lists; anything not in the catalogue defaults to `post_phase`.

3. **Lazy thumbnail generation** — Thumbnails are generated only when the user toggles a card on, not at page load. This avoids a 30–90 s sequential generation of all 51 augmentations. Fast-tier augmentations (Jpeg, Gamma, SubtleNoise, etc.) respond in < 200 ms; slow-tier (BookBinding, Folding) show a placeholder.

4. **`apply_single` uses AugraphyPipeline wrapper** — Calling the augmentation object directly can skip pipeline bookkeeping. Wrapping in `AugraphyPipeline` ensures consistent behavior.

5. **Preset tab is untouched** — All existing sidebar controls, sliders, and Augment button are moved verbatim into Tab 1 (Preset). The page layout change is purely additive.

### Known Edge Cases & Constraints

- `slow=True` augmentations (BookBinding, Folding) show a text placeholder instead of auto-generating a thumbnail. The user can still include them in the custom pipeline via the checkbox.
- `Brightness` and `Dithering` use Numba JIT; `numba_jit=0` is hardcoded in their `default_params` to avoid a cold-start penalty in the UI.
- `Stains` can produce an all-black output on images smaller than 200×200 px; the 256×256 thumbnail size avoids this.
- `AppTest` in Streamlit 1.54 has no `at.tabs` accessor — tests verify page load (`not at.exception`) and session state keys instead.

---

## Tests

### Test Files

| File | Type | Count | What is covered |
|------|------|-------|-----------------|
| `tests/augmentation/test_catalogue.py` | unit | 8 | CATALOGUE size, required keys, phase filter, apply_single for Jpeg/Gamma/Brightness, unknown name raises |
| `tests/unit/test_augmentation_custom.py` | unit | 3 | custom_augmentations runs, empty list, preset still works when custom is None |
| `tests/ui/integration/test_augmentation_lab_catalogue.py` | integration | 5 | Page loads, no image, image in session state, enabled aug cached, preset mode unchanged |

### TDD Cycle Summary

**Red — first failing tests written:**

| Test name | File | Initial failure reason |
|-----------|------|----------------------|
| `test_catalogue_has_at_least_20_entries` | `test_catalogue.py` | `ModuleNotFoundError: catalogue` |
| `test_custom_augmentations_runs_without_error` | `test_augmentation_custom.py` | `TypeError: __init__() got unexpected keyword argument 'custom_augmentations'` |
| `test_augmentation_lab_loads_with_catalogue_tab` | `test_augmentation_lab_catalogue.py` | `ImportError: cannot import name CATALOGUE` |

**Green — minimal implementation:**

Created `catalogue.py` with static `CATALOGUE` dict and `apply_single()`. Added `custom_augmentations` parameter to `DocumentAugmenter.__init__`. Restructured page with `st.tabs(["Preset", "Catalogue"])` — existing preset code moved into Tab 1 unchanged.

**Refactor — improvements made after green:**

| What changed | Why |
|--------------|-----|
| Added `get_phase_augmentations()` helper | Reduces repetition in the page's phase-tab loop |
| Added typed `SessionStateManager` accessors for 4 new keys | Consistent with existing codebase pattern |
| Hardcoded `numba_jit=0` in Brightness/Dithering default_params | Avoids JIT cold-start in UI thumbnails |

### How to Run

```bash
# Catalogue unit tests
uv run pytest tests/augmentation/test_catalogue.py -v --no-cov

# Custom augmentations unit tests
uv run pytest tests/unit/test_augmentation_custom.py -v --no-cov

# All new catalogue tests
uv run pytest tests/augmentation/ tests/unit/test_augmentation_custom.py tests/ui/integration/test_augmentation_lab_catalogue.py -q --no-cov

# Existing lab tests (must still pass)
uv run pytest tests/ui/integration/test_augmentation_lab.py -v --no-cov

# Full fast suite
uv run pytest tests/ -q --no-cov -x --ignore=tests/integration --ignore=tests/e2e
```

---

## Dependencies

### Requires

| Dependency | Kind | Why |
|------------|------|-----|
| `augraphy>=8.2.0` | external | All augmentation classes in CATALOGUE |
| `augmentation/augmenter.py` | internal | `DocumentAugmenter` modified |
| `augmentation/presets.py` | internal | Preset path unchanged |
| `ui/state/session_state.py` | internal | New catalogue state keys |
| `ui/components/image_display.py` | internal | `show_side_by_side`, `image_to_bytes` |

### Required By

| Consumer | How it uses this feature |
|----------|------------------------|
| `ui/pages/01_augmentation_lab.py` | Imports `CATALOGUE`, `apply_single` for Catalogue tab |
| `augmentation/augmenter.py` | Uses `CATALOGUE` to split custom_augmentations by phase |

---

## Usage Examples

### Minimal

```python
from document_simulator.augmentation.catalogue import apply_single
from PIL import Image

result = apply_single("Jpeg", Image.open("doc.jpg"))
```

### Typical

```python
from document_simulator.augmentation import DocumentAugmenter
import augraphy.augmentations as aug_module

aug = DocumentAugmenter(
    custom_augmentations=[
        aug_module.InkBleed(intensity_range=(0.1, 0.3), p=1.0),
        aug_module.NoiseTexturize(sigma_range=(3, 10), p=1.0),
        aug_module.Jpeg(quality_range=(40, 80), p=1.0),
    ]
)
result = aug.augment(pil_image)
```

### Advanced / Edge Case

```python
# Disable Numba JIT for Brightness to avoid cold-start in tests
from document_simulator.augmentation.catalogue import apply_single
result = apply_single("Brightness", img, {"numba_jit": 0, "brightness_range": (0.7, 1.3), "p": 1.0})
```

---

## Future Work

- [ ] Add drag-to-reorder for enabled augmentations in the custom pipeline tab.
- [ ] Add all 51 augraphy 8.2.6 classes to CATALOGUE (currently 23 most useful).
- [ ] Add a "Save pipeline to .env" button.
- [ ] Add histogram comparison (before/after pixel intensity) per augmentation card.
- [ ] Pre-warm Numba JIT for Brightness/Dithering in a background thread on first upload.

---

## References

- [RESEARCH_FINDINGS.md — 2026-03-07 section](../RESEARCH_FINDINGS.md)
- [feature_ui_augmentation_lab.md](feature_ui_augmentation_lab.md)
- [Augraphy 8.2.6 augmentations list](https://augraphy.readthedocs.io/en/latest/doc/source/list_of_augmentations.html)
- [st.cache_data — Streamlit Docs](https://docs.streamlit.io/library/api-reference/performance/st.cache)
