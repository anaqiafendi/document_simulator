# Feature: UI — Augmentation Lab

> **GitHub Issue:** `#14`
> **Status:** `complete`
> **Module:** `document_simulator.ui.pages.01_augmentation_lab`

---

## Summary

A Streamlit page where a user uploads a document image, selects a degradation preset (or fine-tunes 12 sliders), clicks Augment, and sees a side-by-side before/after view with a download button for the result.

---

## Motivation

### Problem Statement

`DocumentAugmenter` and `PresetFactory` are powerful but require code. A visual interface lets non-developers explore and compare augmentation intensities interactively, and lets developers verify that preset parameter changes produce the expected visual effect.

### Value Delivered

- Preset selection without writing Python.
- 12-slider advanced panel for precise parameter control.
- Side-by-side display for immediate visual comparison.
- Download button for saving the augmented result.
- Warning if the user clicks Augment without uploading an image.

---

## User Stories

| Role | Goal | So That |
|------|------|---------|
| Researcher | I upload a scan and toggle heavy/light | I see how aggressively each preset degrades the document |
| Developer | I adjust the InkBleed slider | I confirm the parameter range produces the expected visual |
| Data engineer | I click Download | I save an augmented sample for my training set |

---

## Acceptance Criteria

- [ ] AC-1: Page loads without error.
- [ ] AC-2: A preset radio button is present with options `light`, `medium`, `heavy`.
- [ ] AC-3: An "Augment" button is visible.
- [ ] AC-4: An "Advanced Parameters" expander is visible with ≥10 sliders.
- [ ] AC-5: Clicking Augment with no image shows a `st.warning`.
- [ ] AC-6: After Augment with an image, `"last_aug_image"` appears in session state.

---

## Design

### Public API

No Python API — this is a Streamlit page launched via `streamlit run`.

```bash
uv run streamlit run src/document_simulator/ui/app.py
# Navigate to Augmentation Lab in sidebar
```

### Data Flow

```
User uploads image → state.set_uploaded_image(pil)
User selects preset / adjusts sliders
User clicks "Augment"
    │
    ▼
DocumentAugmenter(preset).augment(src)  ← runs in st.spinner
    │
    ▼
state.set_aug_image(augmented)
show_side_by_side(original, augmented)
st.download_button(data=image_to_bytes(augmented))
```

### Key Interfaces

| Symbol | Kind | Responsibility |
|--------|------|---------------|
| Preset radio | widget | Maps to `PresetFactory.create(name)` |
| 12 sliders (in expander) | widgets | Map to augmentation probabilities / intensities |
| Augment button | widget | Triggers `DocumentAugmenter(preset).augment(src)` |
| `st.session_state["last_aug_image"]` | state key | Persists augmented image across reruns |

---

## Implementation

### Files

| Path | Role |
|------|------|
| `src/document_simulator/ui/pages/01_augmentation_lab.py` | Complete page implementation |
| `src/document_simulator/ui/components/image_display.py` | `show_side_by_side`, `image_to_bytes` |
| `src/document_simulator/ui/components/file_uploader.py` | `uploaded_file_to_pil` |
| `src/document_simulator/ui/state/session_state.py` | `SessionStateManager` |

### Key Architectural Decisions

1. **No business logic in the page** — The page calls `DocumentAugmenter(preset).augment(image)` and `image_to_bytes()`. All augmentation logic lives in the package; the page is pure UI.
2. **Sliders in an expander, not always visible** — 12 sliders make the page noisy. The `st.expander("Advanced Parameters")` hides them by default, keeping the primary flow (upload → preset → augment) clean.
3. **Preset radio drives the default slider values** — When the user switches preset, sliders update to the preset's parameter values. This makes the relationship between preset and sliders transparent.

### Known Edge Cases & Constraints

- `AppTest` cannot interact with `st.file_uploader` directly. Integration tests inject an image via `at.session_state["last_uploaded_image"]`.
- `st.download_button` is not accessible as `at.download_button` in AppTest 1.54 — tests check `"last_aug_image" in at.session_state` instead.

---

## Tests

### Test Files

| File | Type | Count | What is covered |
|------|------|-------|-----------------|
| `tests/ui/integration/test_augmentation_lab.py` | integration | 8 | Load (1), preset radio (2), Augment button (1), expander (1), sliders ≥10 (1), warning on no image (1), session state after run (1) |

### TDD Cycle Summary

**Red — first failing tests written:**

| Test name | File | Initial failure reason |
|-----------|------|----------------------|
| `test_augmentation_lab_loads_without_error` | `test_augmentation_lab.py` | `FileNotFoundError: 01_augmentation_lab.py does not exist` |
| `test_augmentation_lab_has_preset_radio` | `test_augmentation_lab.py` | Page existed but had no radio widget |
| `test_augmentation_lab_stores_aug_image_after_run` | `test_augmentation_lab.py` | `AttributeError: SafeSessionState has no .get()` |

**Green — minimal implementation:**

Created the page file with a file uploader, preset radio, Augment button, and the augmentation call. Added 12 sliders in an expander. Fixed `SafeSessionState` issue by switching test assertion from `.get()` to `"key" in at.session_state`.

**Refactor — improvements made after green:**

| What changed | Why |
|--------------|-----|
| Added `show_side_by_side()` replacing two plain `st.image()` calls | Visual comparison requires the two images to be aligned horizontally |
| Added JSON expander showing augmentation parameters | Useful for reproducibility — users can see exactly which parameters were used |

### How to Run

```bash
uv run pytest tests/ui/integration/test_augmentation_lab.py -v
```

---

## Dependencies

### Requires

| Dependency | Kind | Why |
|------------|------|-----|
| `augmentation/augmenter.py` | internal | `DocumentAugmenter` |
| `ui/components/image_display.py` | internal | `show_side_by_side`, `image_to_bytes` |
| `ui/components/file_uploader.py` | internal | `uploaded_file_to_pil` |
| `ui/state/session_state.py` | internal | `SessionStateManager` |
| `streamlit` | external | Page rendering |

---

## Future Work

- [ ] Add a "Reset to preset defaults" button that restores all sliders.
- [ ] Add a histogram comparing pixel intensity distributions before/after.
- [ ] Add a "Save parameters to `.env`" button.

---

## References

- [feature_ui_components.md](feature_ui_components.md)
- [feature_augmentation_presets.md](feature_augmentation_presets.md)
- [UI_PLAN.md](../UI_PLAN.md)
