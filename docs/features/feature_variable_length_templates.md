# Feature: Variable-Length Multi-Template Document Generation

**Feature ID:** #27  
**Module:** `synthesis.document_template`, `synthesis.template_registry`, `synthesis.sections`  
**Status:** complete  
**Branch:** `feature/variable-length-multi-template`  
**Created:** 2026-04-06  
**Author:** Amuhamad Afendi

---

## Summary

Extend the synthetic document generator to support:

1. **Variable-length sections** — repeating rows (e.g. receipt line items) whose count is
   determined at generation time, not baked into the template.
2. **Named document templates** — a `DocumentTemplate` class that encapsulates layout,
   default styles, and section structure for a specific document type × visual style.
3. **TemplateRegistry** — a registry that maps `(document_type, style_name)` →
   `DocumentTemplate`, enabling multi-template batch generation.

Primary motivation: Air Canada expense receipts from international travel come from many
merchants with wildly different visual layouts and variable line-item counts. The existing
flat `SynthesisConfig` / `ZoneConfig` approach requires a new static config per merchant,
which does not scale.

---

## Background

### Problem

The current `SyntheticDocumentGenerator` accepts a `SynthesisConfig` with a flat
`list[ZoneConfig]` applied to a fixed-height canvas:

```
SynthesisConfig
  ├── respondents: list[RespondentConfig]
  ├── zones: list[ZoneConfig]          ← flat, static
  └── generator: GeneratorConfig       ← fixed image_width / image_height
```

This works well for fixed-field forms (one signature field, one date field, etc.)
but cannot represent:
- A receipt with an unknown number of line items.
- Different visual layouts for different merchant types.

### Goal

Add a `sections` layer on top of zones, and a template abstraction layer on top of
`SynthesisConfig`, while keeping full backward compatibility with existing flat-zone configs.

---

## Architecture

### New Classes

#### `Section` (base, in `sections.py`)
Abstract base for a block of the document. Has a `top_y` property and returns
a `list[ZoneConfig]` when asked to materialise itself.

#### `StaticSection` (in `sections.py`)
A section with a fixed set of zones — equivalent to today's flat zone list.
Used for headers, footers, and any non-repeating block.

#### `RepeatingSection` (in `sections.py`)
A section that repeats a "row template" (list of relative-Y zones) N times.
`num_rows` is sampled at generation time from a range.

```python
RepeatingSection(
    section_id="line_items",
    row_template=[...],   # ZoneConfig with box relative to section top (y=0)
    row_height=25,        # pixels per row
    num_rows_range=(2, 12),
)
```

#### `DocumentTemplate` (in `document_template.py`)
Encapsulates all sections + respondents + default generator config for one
document type × visual style. Exposes:

```python
template.to_synthesis_config(num_line_items: int | None = None, seed: int = 42) -> SynthesisConfig
```

The `to_synthesis_config()` call:
1. Samples `num_rows` for each `RepeatingSection` (seeded).
2. Materialises all sections into a flat `list[ZoneConfig]` with absolute Y coordinates.
3. Computes the total document height dynamically.
4. Returns a standard `SynthesisConfig` that the existing generator can consume unchanged.

#### `TemplateRegistry` (in `template_registry.py`)
Singleton-style registry mapping `(document_type, style_name)` → `DocumentTemplate`.

```python
registry = TemplateRegistry()
registry.register("receipt", "thermal", thermal_receipt_template)
tpl = registry.get("receipt", "thermal")
styles = registry.list_styles("receipt")
types = registry.list_types()
```

#### Bundled templates (in `templates/`)
- `receipt_thermal.py` — 58mm-wide thermal receipt (typical fast-food / transit).
- `receipt_a4.py` — A4 portrait invoice-style receipt (hotels / airlines).

---

## Data Model Changes

### `GeneratorConfig` — `image_height` becomes optional

```python
class GeneratorConfig(BaseModel):
    n: int = 1
    seed: int = 42
    output_dir: str = "output"
    image_width: int = 794
    image_height: int | None = None   # None = dynamic (computed from sections)
```

### `SynthesisConfig` — backward-compatible addition

No structural change. `DocumentTemplate.to_synthesis_config()` produces a standard
`SynthesisConfig` with the correct (dynamic) `image_height` set in `GeneratorConfig`.

---

## Acceptance Criteria

- [x] AC-1: `RepeatingSection` materialises correct number of `ZoneConfig` rows, with Y
      coordinates offset correctly from `top_y`.
- [x] AC-2: `StaticSection` materialises identical zones to its input, offset by `top_y`.
- [x] AC-3: `DocumentTemplate.to_synthesis_config()` returns a `SynthesisConfig` with
      `generator.image_height` equal to the sum of all section heights.
- [x] AC-4: `DocumentTemplate.to_synthesis_config()` with the same `seed` and same
      `num_line_items` is deterministic (same zones, same height).
- [x] AC-5: `TemplateRegistry.register()` stores a template; `.get()` retrieves it;
      `.list_styles()` returns the registered style names; `.list_types()` returns types.
- [x] AC-6: `TemplateRegistry.get()` raises `KeyError` for unknown `(type, style)`.
- [x] AC-7: `receipt_thermal` template generates a valid `SynthesisConfig` with
      `num_line_items` between 2 and 12.
- [x] AC-8: `receipt_a4` template generates a valid `SynthesisConfig` with
      `num_line_items` between 2 and 20.
- [x] AC-9: `SyntheticDocumentGenerator` can consume a `SynthesisConfig` produced by
      `DocumentTemplate.to_synthesis_config()` and return a PIL `Image` with the correct
      height.
- [x] AC-10: All existing synthesis tests continue to pass (backward compatibility).

---

## Test Plan

All tests live in `tests/synthesis/test_variable_templates.py`.

| Test | AC |
|------|----|
| `test_repeating_section_materialises_correct_row_count` | AC-1 |
| `test_repeating_section_y_offsets_are_correct` | AC-1 |
| `test_static_section_materialises_zones_with_offset` | AC-2 |
| `test_document_template_image_height_equals_sum_of_sections` | AC-3 |
| `test_document_template_is_deterministic` | AC-4 |
| `test_registry_register_and_get` | AC-5 |
| `test_registry_list_styles` | AC-5 |
| `test_registry_list_types` | AC-5 |
| `test_registry_get_unknown_raises_key_error` | AC-6 |
| `test_receipt_thermal_template_valid_config` | AC-7 |
| `test_receipt_a4_template_valid_config` | AC-8 |
| `test_generator_consumes_template_config` | AC-9 |
| `test_existing_flat_zones_still_work` | AC-10 |

---

## Files Added / Modified

### New files
```
src/document_simulator/synthesis/sections.py
src/document_simulator/synthesis/document_template.py
src/document_simulator/synthesis/template_registry.py
src/document_simulator/synthesis/templates/
src/document_simulator/synthesis/templates/__init__.py
src/document_simulator/synthesis/templates/receipt_thermal.py
src/document_simulator/synthesis/templates/receipt_a4.py
tests/synthesis/test_variable_templates.py
```

### Modified files
```
src/document_simulator/synthesis/zones.py         — image_height: int | None
src/document_simulator/synthesis/__init__.py       — re-export new public API
docs/features/README.md                            — add #27
docs/RESEARCH_FINDINGS.md                          — Phase 2 research appended
```

---

## Dependencies

No new Python packages required. All new code uses only:
- `pydantic` (already a core dependency)
- `PIL` (already a core dependency)

---

## Signoff

| Role | Name | Date | Status |
|------|------|------|--------|
| Author | Amuhamad Afendi | 2026-04-06 | complete |
| Review | — | — | pending |
