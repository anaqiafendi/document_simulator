# Feature: Augmentation UI — Perceptual Degradation Language

> **GitHub Issue:** `#26`
> **Status:** `complete`
> **Module:** `ui.pages.01_augmentation_lab` + `augmentation.catalogue`

---

## Summary

Renames and reframes the augmentation controls in the Streamlit UI from technical library jargon ("jitter", "InkBleed probability", "Ink Phase") to plain English that describes real-world document degradation scenarios that business users can relate to ("Ink bleed-through", "How much ink bleeds through thin paper", "Ink Degradation").

---

## Motivation

### Problem Statement

During a live demo with a domain expert (Anand, 2026-04-06), the term "jitter" in the augmentation UI was flagged as misleading. Verbatim feedback:

> "jitter is too literal here. In image processing, jitter could look like weird angles, less resolution, right? Noise, you know what I mean? Noise over the text."

The augmentation lab sidebar used technical labels like "InkBleed probability" and "Fading (LowLightNoise) probability" — terms that reference internal library class names meaningless to a business user. The phase groupings ("Ink Phase", "Paper Phase", "Post Phase") are also technical pipeline concepts that do not map to the user's mental model.

### Value Delivered

- Business users can immediately understand what each slider does without reading documentation
- Tooltips (`help=`) explain the real-world scenario each augmentation simulates
- Phase headers group controls by **what kind of degradation** they model, not which phase of the Augraphy pipeline they belong to
- Catalogue `description` strings are rewritten to describe the scenario, not the algorithm

---

## User Stories

| Role | Goal | So That |
|------|------|---------|
| Business analyst | I can understand what "ink bleed-through" means without asking a developer | I can configure realistic degradation for my receipts dataset |
| Solution demonstrator | I can explain each slider's effect during a live demo without technical jargon | Stakeholders understand the tool's value immediately |
| Business user | I can see section headers like "Capture Conditions" and "Paper Degradation" | I map the controls to my real-world document processing problems |

---

## Acceptance Criteria

- [x] AC-1: The Preset sidebar no longer contains slider labels with raw library names ("InkBleed", "LowLightNoise", "NoiseTexturize") — all labels are plain English
- [x] AC-2: Every Preset sidebar slider has a `help=` tooltip with a 1–2 sentence plain English description of what the setting does in the real world
- [x] AC-3: The Catalogue tab phase headers read "Ink Degradation", "Paper Degradation", and "Capture Conditions" (not "Ink Phase", "Paper Phase", "Post Phase")
- [x] AC-4: The `CATALOGUE` `description` fields are plain English real-world descriptions (no library class names in descriptions)
- [x] AC-5: All existing UI integration tests pass with the updated labels
- [x] AC-6: New tests verify the plain-English phase headers and slider labels are rendered

---

## Design

### Public API

No Python API surface changes. This feature only modifies UI labels and copy.

The Python parameter names `jitter_x`, `jitter_y`, `char_spacing_jitter` in `synthesis/zones.py` and `synthesis/renderer.py` are **not changed** — these are internal model attributes.

### Data Flow

```
User opens Augmentation Lab
    │
    ▼
Preset tab → sidebar sliders → plain English labels + help tooltips
    │
    ▼
Catalogue tab → phase tabs → renamed "Ink Degradation" / "Paper Degradation" / "Capture Conditions"
    │
    ▼
Catalogue cards → description strings from CATALOGUE → real-world plain English
```

### Key Interfaces

| Symbol | Kind | Responsibility |
|--------|------|---------------|
| `CATALOGUE` dict | config | Provides `display_name`, `description`, `phase` per augmentation |
| `01_augmentation_lab.py` | Streamlit page | Renders sliders with `help=` params and phase tab headers |

### Configuration

No new environment variables or settings.

---

## Implementation

### Files

| Path | Role |
|------|------|
| `src/document_simulator/augmentation/catalogue.py` | Updated `description` fields to plain English real-world scenarios |
| `src/document_simulator/ui/pages/01_augmentation_lab.py` | Renamed sidebar slider labels, added `help=` tooltips, renamed Catalogue phase tabs |
| `tests/ui/integration/test_augmentation_lab.py` | Updated label-matching tests; added AC-3 and AC-6 tests |

### Key Architectural Decisions

1. **Labels only, not parameter names** — All Python attribute names (`jitter_x`, `jitter_y`, `intensity_range`, etc.) remain unchanged. Only UI-facing string literals are modified. This means zero risk of breaking the backend, tests, or serialised configs.

2. **`help=` parameter on `st.slider()`** — Streamlit's `help=` renders as a tooltip icon (`?`) next to the slider label. This is the idiomatic way to add contextual help without cluttering the layout.

3. **Phase tab rename: "Post Phase" → "Capture Conditions"** — Anand's feedback was specifically that "jitter" meant perceptual degradation from the *capture* stage (photograph/scan). Naming this tab "Capture Conditions" aligns with that mental model: rotation, resolution, compression, brightness — all things that vary when a document is photographed.

4. **CATALOGUE descriptions: one sentence, plain English, no class names** — Descriptions must not contain library class names (e.g., "LowLightNoise") because business users have no context for those. Instead descriptions say what the effect looks like in a real document.

### Known Edge Cases & Constraints

- AppTest integration tests that check for slider label substrings must be updated to match new labels (done in this PR)
- The `help=` tooltip text is not accessible via AppTest in Streamlit 1.54 — only visual content can be tested via AppTest

### Bugs Fixed Post-Implementation

None.

---

## Tests

### Test Files

| File | Type | Count | What is covered |
|------|------|-------|-----------------|
| `tests/ui/integration/test_augmentation_lab.py` | integration | 12 | Page load, slider presence, phase headers, plain-English labels, warning on no image |

### TDD Cycle Summary

**Red — first failing tests written:**

| Test name | File | Initial failure reason |
|-----------|------|----------------------|
| `test_augmentation_lab_phase_headers_renamed` | `tests/ui/integration/test_augmentation_lab.py` | `AssertionError` — tabs still had "Ink Phase", "Paper Phase", "Post Phase" |
| `test_augmentation_lab_preset_sliders_plain_english` | `tests/ui/integration/test_augmentation_lab.py` | `AssertionError` — slider labels still contained "InkBleed", "LowLightNoise" |

**Green — minimal implementation:**

Updated `01_augmentation_lab.py` to rename sidebar slider labels and use `help=` parameters. Changed `st.tabs(["Ink Phase", "Paper Phase", "Post Phase"])` to `st.tabs(["Ink Degradation", "Paper Degradation", "Capture Conditions"])`. Updated `catalogue.py` description strings.

**Refactor — improvements made after green:**

| What changed | Why |
|--------------|-----|
| Help text written as 1–2 sentences describing real-world scenario | First pass was too brief; expanded to give business users enough context |
| `description` strings in catalogue updated for all 40+ entries | Initial pass only updated the most-used ones; expanded to full coverage |

### How to Run

```bash
uv run pytest tests/ui/integration/test_augmentation_lab.py -v --no-cov
```

---

## Dependencies

### Requires

| Dependency | Kind | Why |
|------------|------|-----|
| `streamlit>=1.32.0` | external (existing) | `help=` param on `st.slider()` is available since 1.x |

### Required By

| Consumer | How it uses this feature |
|----------|------------------------|
| Business users | Read plain English labels to understand augmentation controls |
| Integration tests | Assert on rendered label text |

---

## Usage Examples

### Minimal

```python
# Slider with plain English label and tooltip (in 01_augmentation_lab.py)
ink_bleed_p = st.slider(
    "Ink bleed-through probability",
    0.0, 1.0, 0.5, 0.01,
    help="How likely ink from the other side of the page bleeds through. "
         "Common in thin paper receipts and double-sided documents.",
)
```

### Typical

```python
# Phase tabs renamed to business language
phase_tab_ink, phase_tab_paper, phase_tab_post = st.tabs(
    ["Ink Degradation", "Paper Degradation", "Capture Conditions"]
)
```

---

## Future Work

- [ ] Add a plain-English glossary page / modal explaining each augmentation category
- [ ] Consider renaming "Preset" tab presets (light/medium/heavy) to scenario names like "Office scan", "Phone photo", "Worn archive"
- [ ] If a React SPA replaces the Streamlit pages, carry over all the plain-English label copy written here

---

## References

- [Research findings (2026-04-06 section)](../RESEARCH_FINDINGS.md)
- [Feedback from Anand (2026-04-06)](../../../../0_docs/doc%20simulator/feedback-anand-2026-04-06.md)
- [Augmentation Lab FDD](feature_ui_augmentation_lab.md)
- [Augmentation Catalogue FDD](feature_augmentation_lab_catalogue.md)
