# Feature: Robust Ground Truth Bundling

> **GitHub Issue:** `#26`
> **Status:** `complete`
> **Module:** `document_simulator.synthesis.ground_truth_writer`, `document_simulator.synthesis.batch_integrity`

---

## Summary

Hardens ground truth generation for the LLM-inferred-schema flow. Every generated image is guaranteed a paired GT file with bounding boxes per field. A new `GroundTruthRecord` schema is self-describing (field_name, text_value, bbox_pixels, bbox_normalized, font_info, confidence). `BatchIntegrityChecker` verifies N GT files exist for N images. Three export formats are supported: per-image JSON sidecar, JSONL manifest for whole batch, COCO-style JSON.

---

## Motivation

### Problem Statement

Anand's feedback (2026-04-06) confirmed the existing GT generation works for the template-based flow but is insufficient for the LLM-inferred-schema flow:

1. No batch integrity verification — a partial write or crash leaves orphaned images without GT
2. Bounding boxes exist in pixel space only — normalized coordinates required for OCR fine-tuning
3. No `field_name` field — `label` is human-readable but not machine-canonical
4. No `confidence` semantics distinguishing synthetic GT (1.0) from LLM-inferred GT (<1.0)
5. No JSONL manifest or COCO export — downstream PaddleOCR fine-tuning requires these

### Air Canada Use Case

Generated datasets will fine-tune OCR models for receipt field extraction from photos of international travel receipts. GT reliability is non-negotiable: every image in the training set must have a corresponding GT file, and every field must have both pixel and normalized bounding boxes.

---

## Acceptance Criteria

- [x] `GroundTruthRecord` Pydantic model includes: `field_name`, `text_value`, `bbox_pixels` `[x,y,w,h]`, `bbox_normalized` `[x,y,w,h]`, `font_info` dict, `confidence` float
- [x] `GroundTruthWriter.write_sidecar()` saves enhanced per-image JSON with `schema_version="2.0"`
- [x] `GroundTruthWriter.write_jsonl()` saves a JSONL manifest (one record per line)
- [x] `GroundTruthWriter.write_coco()` saves COCO-format JSON (images + annotations arrays)
- [x] `BatchIntegrityChecker.check()` raises `BatchIntegrityError` if image count != GT count
- [x] `BatchIntegrityChecker.check()` raises `BatchIntegrityError` if any GT `image_path` points to a non-existent file
- [x] `SyntheticDocumentGenerator.generate()` accepts `write_manifest` and `write_coco` flags
- [x] All new code has unit tests (TDD: red → green → refactor) — 39 new tests, all passing
- [x] Existing test suite passes without regressions (252 passed, 1 pre-existing Faxify/Numba failure)
- [x] `AnnotationBuilder` backward compatibility preserved (no changes to `AnnotationBuilder`)

---

## Design

### `GroundTruthRecord` (new Pydantic model)

Replaces / wraps `TextRegion` for the enhanced export formats. Lives in `synthesis/ground_truth_writer.py`.

```python
class GroundTruthRecord(BaseModel):
    field_name: str             # canonical field identifier (= zone label)
    text_value: str             # rendered text
    bbox_pixels: list[float]    # [x, y, w, h] axis-aligned, pixel coords
    bbox_normalized: list[float]  # [x, y, w, h] in [0, 1] relative to image dims
    font_info: dict             # {"family": str, "size": int, "color": str, "style": str}
    confidence: float           # 1.0 for synthetic; < 1.0 for LLM-inferred
    page: int                   # 0-indexed PDF page
    quad_pixels: list[list[float]]  # [[x1,y1],[x2,y2],[x3,y3],[x4,y4]] original quad
```

Parent record:

```python
class EnhancedGroundTruth(BaseModel):
    image_path: str
    image_width: int
    image_height: int
    synthetic: bool
    seed: Optional[int]
    generation_timestamp: str
    schema_version: str         # "2.0" for this format
    fields: list[GroundTruthRecord]
```

### `GroundTruthWriter`

```python
class GroundTruthWriter:
    @staticmethod
    def from_ground_truth(gt: GroundTruth, image_width: int, image_height: int) -> EnhancedGroundTruth
    @staticmethod
    def write_sidecar(egt: EnhancedGroundTruth, path: Path) -> None
    @staticmethod
    def write_jsonl(records: list[EnhancedGroundTruth], path: Path) -> None
    @staticmethod
    def write_coco(records: list[EnhancedGroundTruth], path: Path) -> None
```

### `BatchIntegrityChecker`

```python
class BatchIntegrityError(Exception): ...

class BatchIntegrityChecker:
    @staticmethod
    def check(output_dir: Path, expected_n: int, ext: str = ".png") -> BatchIntegrityReport
```

Returns a `BatchIntegrityReport` dataclass with `ok: bool`, `missing_gt: list[str]`, `missing_images: list[str]`, `orphaned_gt: list[str]`.

### Integration with `SyntheticDocumentGenerator`

`generate()` gains optional keyword arguments:
- `write_manifest: bool = False` — after batch, call `GroundTruthWriter.write_jsonl()`
- `write_coco: bool = False` — after batch, call `GroundTruthWriter.write_coco()`

When `write=True`, the per-image JSON sidecar now uses the enhanced `EnhancedGroundTruth` schema (schema_version "2.0"). Legacy `AnnotationBuilder.save()` is preserved for existing callers.

---

## File Manifest

| File | Action | Description |
|------|--------|-------------|
| `src/document_simulator/synthesis/ground_truth_writer.py` | CREATE | `GroundTruthRecord`, `EnhancedGroundTruth`, `GroundTruthWriter` |
| `src/document_simulator/synthesis/batch_integrity.py` | CREATE | `BatchIntegrityError`, `BatchIntegrityReport`, `BatchIntegrityChecker` |
| `src/document_simulator/synthesis/generator.py` | MODIFY | Add `write_manifest`, `write_coco` args; use `GroundTruthWriter` for sidecars |
| `src/document_simulator/synthesis/__init__.py` | MODIFY | Export new classes |
| `tests/synthesis/test_ground_truth_writer.py` | CREATE | Unit tests for `GroundTruthWriter` |
| `tests/synthesis/test_batch_integrity.py` | CREATE | Unit tests for `BatchIntegrityChecker` |
| `tests/synthesis/test_generator_gt.py` | CREATE | Integration tests for enhanced generator output |

---

## TDD Test Plan

### `test_ground_truth_writer.py`

1. `test_from_ground_truth_computes_bbox_pixels` — quad → axis-aligned bbox `[x,y,w,h]`
2. `test_from_ground_truth_computes_bbox_normalized` — pixel bbox divided by image dims
3. `test_from_ground_truth_sets_schema_version_2` — `schema_version == "2.0"`
4. `test_from_ground_truth_maps_label_to_field_name` — `label` → `field_name`
5. `test_write_sidecar_creates_json_file` — file exists after call
6. `test_write_sidecar_readable_back` — round-trip via `json.load`
7. `test_write_jsonl_creates_one_line_per_record` — N records → N lines
8. `test_write_jsonl_each_line_is_valid_json` — each line parses as JSON
9. `test_write_coco_has_images_and_annotations_keys` — top-level COCO structure
10. `test_write_coco_annotation_count_matches_fields` — sum of fields == len(annotations)
11. `test_write_coco_bbox_is_xywh` — annotations[*].bbox is [x, y, w, h]
12. `test_confidence_preserved` — 0.7 confidence round-trips through sidecar

### `test_batch_integrity.py`

1. `test_check_passes_when_all_pairs_present` — N images + N GT → ok=True
2. `test_check_fails_when_gt_missing` — N images, N-1 GT → raises `BatchIntegrityError`
3. `test_check_fails_when_image_missing` — N GT pointing to missing image → raises
4. `test_check_report_lists_missing_gt` — `report.missing_gt` contains correct filename
5. `test_check_report_lists_missing_images` — `report.missing_images` correct
6. `test_check_zero_documents` — empty dir with expected_n=0 → ok=True
7. `test_check_pdf_extension` — works with `.pdf` ext

### `test_generator_gt.py`

1. `test_generate_write_produces_enhanced_sidecar` — JSON has `schema_version` key
2. `test_generate_write_manifest_creates_jsonl` — `batch_manifest.jsonl` created
3. `test_generate_write_coco_creates_coco_json` — `coco_annotations.json` created
4. `test_batch_integrity_passes_after_generate` — integrity check ok after generation

---

## Dependencies

No new PyPI packages required. All implementation uses stdlib + existing Pydantic models.

---

## Signoff

| Role | Name | Date | Status |
|------|------|------|--------|
| Author | Amuhamad Afendi | 2026-04-06 | complete |
| Reviewer | — | — | pending |
