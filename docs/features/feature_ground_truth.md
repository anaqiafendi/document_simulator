# Feature: Ground Truth Loading

> **GitHub Issue:** `#7`
> **Status:** `complete`
> **Module:** `document_simulator.data.ground_truth`

---

## Summary

Pydantic data models (`TextRegion`, `GroundTruth`) and a static loader (`GroundTruthLoader`) that parses JSON and ICDAR-style XML annotation files into a validated, uniform structure. `detect_and_load()` auto-selects the format by file extension.

---

## Motivation

### Problem Statement

Annotation datasets come in at least two common formats (custom JSON and ICDAR XML). Without a normalised model, every consumer would need to parse raw dicts or XML elements inline, leading to brittle format-specific code spread across dataset loaders, evaluators, and tests.

### Value Delivered

- Single `GroundTruth` model used everywhere — dataset, evaluator, RL environment.
- Pydantic validators reject malformed boxes (not 4 points, not 2 coords) and confidence values outside `[0, 1]` at parse time.
- `GroundTruth.full_text` synthesises a string from regions if no flat `text` field exists.
- `detect_and_load()` eliminates format-switching logic from callers.

---

## User Stories

| Role | Goal | So That |
|------|------|---------|
| Dataset user | I call `GroundTruthLoader.detect_and_load(Path("gt.json"))` | I get a typed object without knowing the format |
| Evaluator | I access `ground_truth.text` | I can compute CER without additional parsing |
| Developer | I construct `TextRegion` with invalid confidence | I get a `ValueError` immediately |

---

## Acceptance Criteria

- [ ] AC-1: `TextRegion(box=VALID_BOX, text="hi", confidence=0.9)` constructs without error.
- [ ] AC-2: `TextRegion(box=[[0,0],[1,1]], ...)` raises `ValueError` (only 2 points).
- [ ] AC-3: `TextRegion(box=..., confidence=1.5)` raises `ValueError`.
- [ ] AC-4: `GroundTruth.full_text` returns joined region texts when regions are present.
- [ ] AC-5: `GroundTruth.full_text` falls back to `.text` when regions are empty.
- [ ] AC-6: `GroundTruthLoader.load_json(path)` parses a valid JSON file.
- [ ] AC-7: `GroundTruthLoader.load_xml(path)` parses a valid ICDAR XML file.
- [ ] AC-8: `detect_and_load(path.json)` dispatches to `load_json`.
- [ ] AC-9: `detect_and_load(path.unknown)` raises `ValueError`.

---

## Design

### Public API

```python
from document_simulator.data.ground_truth import GroundTruth, GroundTruthLoader, TextRegion

gt: GroundTruth = GroundTruthLoader.detect_and_load(Path("annotation.json"))
# or
gt: GroundTruth = GroundTruthLoader.detect_and_load(Path("annotation.xml"))

print(gt.full_text)      # All region texts joined by newline
print(gt.image_path)     # Associated image filename
print(len(gt.regions))   # Number of TextRegion objects
```

### Data Flow

```
GroundTruthLoader.detect_and_load(path)
    │
    ├─► .json  →  load_json() → json.load() → GroundTruth(**data)
    │
    └─► .xml   →  load_xml()  → ET.parse()
                               → for each <text_region>:
                                     extract coords + text + confidence
                                 → list[TextRegion]
                               → GroundTruth(image_path, text, regions)
    │
    ▼
GroundTruth  (Pydantic model, validated)
```

### Key Interfaces

| Symbol | Kind | Responsibility |
|--------|------|---------------|
| `TextRegion` | Pydantic BaseModel | Single annotated text region: box (4×2 floats), text, confidence |
| `GroundTruth` | Pydantic BaseModel | Full document annotation: image_path, text, list of TextRegion |
| `GroundTruthLoader.load_json(path)` | static method | Parses JSON → `GroundTruth` |
| `GroundTruthLoader.load_xml(path)` | static method | Parses ICDAR XML → `GroundTruth` |
| `GroundTruthLoader.detect_and_load(path)` | static method | Auto-dispatch by extension |

### Configuration

No `.env` settings.

---

## Implementation

### Files

| Path | Role |
|------|------|
| `src/document_simulator/data/ground_truth.py` | Models + loader; all logic in ~145 lines |

### Key Architectural Decisions

1. **Pydantic validators, not manual checks** — `@field_validator("box")` and `@field_validator("confidence")` run on every construction, including from dicts parsed by `GroundTruth(**data)`. This means JSON files are validated the same way as programmatic construction.

2. **XML schema: ICDAR-style attributes** — `<coords x1="..." y1="..." .../>` matches the ICDAR 2013/2015 annotation format for interoperability. The schema is not enforced beyond what the loader reads — extra attributes are ignored.

3. **`full_text` is a property, not a field** — Computing the joined string at construction time and storing it would duplicate data. A property is evaluated on demand and stays in sync with `regions` automatically.

4. **Confidence defaults to 1.0** — Ground truth annotations typically don't have a confidence field (they're human-verified). Defaulting to 1.0 means the model is correct for annotations created without a confidence score.

### Known Edge Cases & Constraints

- XML `<text_region>` elements missing `<coords>` or `<text>` are silently skipped.
- JSON parsing does not validate that `image_path` actually exists on disk.
- `full_text` joining always uses `"\n"` — callers expecting space-separated text must join differently.

---

## Tests

### Test Files

| File | Type | Count | What is covered |
|------|------|-------|-----------------|
| `tests/test_ground_truth.py` | unit | 13 | `TextRegion` validation (4), `GroundTruth.full_text` (2), JSON loading (2), XML loading (1), `detect_and_load` (3) |

### TDD Cycle Summary

**Red — first failing tests written:**

| Test name | File | Initial failure reason |
|-----------|------|----------------------|
| `test_text_region_invalid_box_wrong_points` | `tests/test_ground_truth.py` | `ImportError: cannot import name 'TextRegion'` |
| `test_load_json_ground_truth` | `tests/test_ground_truth.py` | `ImportError: cannot import name 'GroundTruthLoader'` |
| `test_load_xml_ground_truth` | `tests/test_ground_truth.py` | `ImportError: cannot import name 'GroundTruthLoader'` |

**Green — minimal implementation:**

Created `TextRegion` and `GroundTruth` as Pydantic `BaseModel` subclasses with the field validators. Wrote `GroundTruthLoader` with `load_json` (trivial `GroundTruth(**json.load(fh))`) and `load_xml` (iterating `<text_region>` elements).

`test_text_region_invalid_box_wrong_points` failed first because the validator was not checking `len(v) != 4` — the check was added.

**Refactor — improvements made after green:**

| What changed | Why |
|--------------|-----|
| Added `detect_and_load()` | Every test that exercised loading needed to choose `load_json` vs `load_xml` by hand; a single dispatch method is cleaner and makes `DocumentDataset` simpler |
| Moved confidence attribute from `TextRegion.get()` to `region_el.get("confidence", 1.0)` in XML loader | Attribute was accidentally being read from `<text_region>` elem rather than `<coords>` — caught by `test_load_xml_ground_truth` |

### How to Run

```bash
uv run pytest tests/test_ground_truth.py -v
uv run pytest tests/test_ground_truth.py --cov=document_simulator.data.ground_truth
```

---

## Dependencies

### Requires

| Dependency | Kind | Why |
|------------|------|-----|
| `pydantic` | external | `BaseModel`, `field_validator` |
| `json` | stdlib | JSON parsing |
| `xml.etree.ElementTree` | stdlib | XML parsing |

### Required By

| Consumer | How it uses this feature |
|----------|------------------------|
| `data/datasets.py` | `GroundTruthLoader.detect_and_load()` in `__getitem__()` |
| `evaluation/evaluator.py` | `ground_truth.text` for CER/WER computation |
| `rl/environment.py` | `gt.text` for `_current_gt_text` |

---

## Usage Examples

### Minimal

```python
from document_simulator.data.ground_truth import GroundTruthLoader

gt = GroundTruthLoader.detect_and_load(Path("annotation.json"))
print(gt.text)
```

### Typical

```python
from document_simulator.data.ground_truth import GroundTruth, GroundTruthLoader
from document_simulator.ocr.metrics import calculate_cer

gt = GroundTruthLoader.detect_and_load(Path("form_002.xml"))
result = ocr_engine.recognize(image)
cer = calculate_cer(result["text"], gt.full_text)
```

### Advanced / Edge Case

```python
# Programmatic construction with validation
from document_simulator.data.ground_truth import TextRegion, GroundTruth

try:
    region = TextRegion(
        box=[[0,0],[100,0],[100,20],[0,20]],
        text="Invoice",
        confidence=0.98,
    )
except ValueError as e:
    print(f"Invalid annotation: {e}")
```

---

## Future Work

- [ ] Add `load_icdar2015(path)` for the multi-file ICDAR 2015 format (one text file per image).
- [ ] Add `GroundTruth.to_json(path)` for round-trip serialisation.
- [ ] Validate `image_path` existence during loading (opt-in flag).

---

## References

- [feature_document_dataset.md](feature_document_dataset.md)
- [IMPLEMENTATION_PLAN.md — Phase 2](../IMPLEMENTATION_PLAN.md)
