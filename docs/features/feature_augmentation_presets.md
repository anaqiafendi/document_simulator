# Feature: Augmentation Presets

> **GitHub Issue:** `#1`
> **Status:** `complete`
> **Module:** `document_simulator.augmentation.presets`

---

## Summary

Defines three named degradation profiles — `light`, `medium`, and `heavy` — each a pre-configured Augraphy pipeline, plus a `PresetFactory` that instantiates them by name. This gives every caller a consistent, validated starting point without needing to know Augraphy's API directly.

---

## Motivation

### Problem Statement

Augraphy has 100+ augmentations with non-obvious parameter ranges. Every subsystem that needs document degradation (CLI, UI, RL environment) would otherwise duplicate configuration, leading to drift and untested combinations.

### Value Delivered

- Single source of truth for augmentation configuration across CLI, UI, and RL training.
- Probabilities and intensity values validated at construction time — invalid configs fail fast.
- Callers can say `"light"` or `"heavy"` without knowing any Augraphy internals.
- `"default"` maps to `"medium"` so code that omits a preset choice still gets a sensible result.

---

## User Stories

| Role | Goal | So That |
|------|------|---------|
| CLI user | I can pass `--pipeline heavy` | I get strong degradation without writing config |
| UI user | I can pick a preset from a radio button | I see a meaningful before/after difference |
| RL agent | I can build a pipeline by name at each episode reset | The environment is deterministic per preset |
| Developer | I can add a new preset once | All callers automatically gain access to it |

---

## Acceptance Criteria

- [ ] AC-1: `PresetFactory.create("light")`, `"medium"`, `"heavy"`, and `"default"` all return an `AugmentationPreset`.
- [ ] AC-2: `PresetFactory.create("unknown")` raises `KeyError`.
- [ ] AC-3: Every preset has at least one augmentation in each of ink, paper, and post phases.
- [ ] AC-4: All augmentation probabilities (`p` attribute) are in `[0.0, 1.0]`.
- [ ] AC-5: Heavy preset contains at least as many augmentations as light.

---

## Design

### Public API

```python
from document_simulator.augmentation.presets import PresetFactory, AugmentationPreset

preset: AugmentationPreset = PresetFactory.create("heavy")
# preset.ink_phase, preset.paper_phase, preset.post_phase → lists of Augraphy augmentors
```

### Data Flow

```
PresetFactory.create(name)
    │
    ▼
_validate_preset(preset)    ← raises ValueError on bad probabilities
    │
    ▼
AugmentationPreset(name, ink_phase, paper_phase, post_phase)
    │
    ▼
Passed to AugraphyPipeline(ink_phase=..., paper_phase=..., post_phase=...)
```

### Key Interfaces

| Symbol | Kind | Responsibility |
|--------|------|---------------|
| `AugmentationPreset` | dataclass | Container: name + three phase lists |
| `PresetFactory` | class | Factory: maps name string → configured `AugmentationPreset` |
| `_validate_preset(preset)` | function | Raises `ValueError` if any `aug.p` is outside `[0, 1]` |

### Configuration

No `.env` settings — presets use hardcoded parameter classes (`_LightParams`, `_MediumParams`, `_HeavyParams`) as the source of truth.

---

## Implementation

### Files

| Path | Role |
|------|------|
| `src/document_simulator/augmentation/presets.py` | Full implementation: dataclass, factory, validator, three preset builders |

### Key Architectural Decisions

1. **Hardcoded parameter classes, not `.env`** — Preset parameters are intentional design choices, not deployment-time config. Putting them in `.env` would invite inconsistent environments and make Git diffs of parameter changes invisible.

2. **`_validate_preset` called at construction** — Rather than trusting the constants to be correct, every `create_*` method validates its output. This means a typo like `p=1.2` raises at import time during tests, not silently at runtime.

3. **`"default"` aliased to `"medium"`** — Avoids a fourth code path. Callers that don't care about intensity get a sensible middle ground; callers that do care pick explicitly.

4. **augraphy 8.2.6 quirks baked in** — `ColorShift` takes separate `color_shift_offset_x_range` / `color_shift_offset_y_range` args; `LowLightNoise` is used in place of the missing `Fading` class. These are centralised here so no other module needs to know.

### Known Edge Cases & Constraints

- Augraphy 8.2.6 is pinned. A future upgrade may rename or remove augmentation classes referenced in the presets.
- `_validate_preset` only checks the `p` attribute; it does not validate intensity range bounds.

---

## Tests

### Test Files

| File | Type | Count | What is covered |
|------|------|-------|-----------------|
| `tests/unit/test_presets.py` | unit | 15 | Factory lookup, phase non-emptiness, probability bounds, name attribute, heavy ≥ light |

### TDD Cycle Summary

**Red — first failing tests written:**

| Test name | File | Initial failure reason |
|-----------|------|----------------------|
| `test_preset_factory_known_names[light]` | `tests/unit/test_presets.py` | `ImportError: cannot import name 'PresetFactory'` |
| `test_preset_has_all_phases[create_light]` | `tests/unit/test_presets.py` | `ImportError: cannot import name 'PresetFactory'` |
| `test_preset_parameter_bounds[create_heavy]` | `tests/unit/test_presets.py` | `ImportError: cannot import name 'PresetFactory'` |

**Green — minimal implementation:**

Created `AugmentationPreset` dataclass and `PresetFactory` with stubs returning empty phase lists. Tests for non-empty phases immediately failed. Filled in the actual Augraphy augmentation objects phase by phase, running `test_preset_has_all_phases` after each phase was populated.

**Refactor — improvements made after green:**

| What changed | Why |
|--------------|-----|
| Extracted `_LightParams`, `_MediumParams`, `_HeavyParams` inner classes | Augmenter constructor calls were cluttered with magic numbers; named constants made diffs readable |
| Added `_validate_preset()` and called it from every `create_*` method | Caught a typo (`p=1.2` on `InkBleed` in heavy) that the probability-bounds test exposed |

No additional tests were added post-refactor; the existing bounds test already covered validation.

### How to Run

```bash
# All preset tests
uv run pytest tests/unit/test_presets.py -v

# Single parametrized case
uv run pytest "tests/unit/test_presets.py::test_preset_factory_known_names[heavy]" -v

# With coverage
uv run pytest tests/unit/test_presets.py --cov=document_simulator.augmentation.presets
```

---

## Dependencies

### Requires

| Dependency | Kind | Why |
|------------|------|-----|
| `augraphy==8.2.6` | external | Provides `InkBleed`, `LowLightNoise`, `Markup`, `NoiseTexturize`, `ColorShift`, `Brightness`, `Gamma`, `Dithering`, `Jpeg` |

### Required By

| Consumer | How it uses this feature |
|----------|------------------------|
| `augmentation/augmenter.py` | `DocumentAugmenter._create_pipeline()` calls `PresetFactory.create(preset)` |
| `ui/pages/01_augmentation_lab.py` | Preset radio button maps to `PresetFactory.create(name)` |
| `rl/environment.py` | `DocumentEnv._build_augmenter()` constructs Augraphy phases using the same augmentation classes |

---

## Usage Examples

### Minimal

```python
from document_simulator.augmentation.presets import PresetFactory

preset = PresetFactory.create("light")
```

### Typical

```python
from augraphy import AugraphyPipeline
from document_simulator.augmentation.presets import PresetFactory

preset = PresetFactory.create("medium")
pipeline = AugraphyPipeline(
    ink_phase=preset.ink_phase,
    paper_phase=preset.paper_phase,
    post_phase=preset.post_phase,
)
augmented = pipeline(image_array)
```

### Advanced / Edge Case

```python
# Inspect augmentation probabilities before using the preset
preset = PresetFactory.create("heavy")
for aug in preset.post_phase:
    print(type(aug).__name__, getattr(aug, "p", "n/a"))
```

---

## Future Work

- [ ] Allow preset parameters to be overridden via a `params` dict argument to `PresetFactory.create()`.
- [ ] Add a `"custom"` preset that reads from `.env` variables.
- [ ] Validate intensity range bounds in `_validate_preset`, not just probability.

---

## References

- [IMPLEMENTATION_PLAN.md — Phase 1](../IMPLEMENTATION_PLAN.md)
- [Augraphy documentation](https://augraphy.readthedocs.io/)
