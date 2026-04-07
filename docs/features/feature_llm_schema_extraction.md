# Feature: LLM-Powered Field Schema Extraction

> **GitHub Issue:** `#27`
> **Status:** `complete`
> **Module:** `document_simulator.synthesis.schema_extractor` + `document_simulator.synthesis.field_schema`

---

## Summary

Given a batch of real-world document scans (receipts, invoices, forms), a vision-capable LLM (GPT-4o or Claude claude-sonnet-4-6) analyses the images, identifies the fields present, infers data types and value patterns, and returns a structured `DocumentSchema` that the synthetic document generator can consume to produce realistic per-field fake values — replacing the manual zone-tagging step for clients who have existing data but no clean templates.

---

## Motivation

### Problem Statement

The synthetic document generator currently requires a manually authored `SynthesisConfig` with explicit `ZoneConfig` entries per field. Clients who have thousands of real receipts but no clean PDF templates must hand-label every field — an impractical upfront cost.

Air Canada's expense-receipt use case is the canonical example: international receipts photographed by employees on phones, in multiple languages, with varying layouts. There is no single template to tag.

### Value Delivered

- Eliminates manual zone-tagging for clients who already have real document samples.
- Supports multi-language documents (LLM detects language and currency automatically).
- Produces a `DocumentSchema` that directly maps to `ZoneDataSampler` provider keys.
- LLM integration is optional — module imports without any API key; CI runs without network.
- Enables the full pipeline: real scans → inferred schema → synthetic variants → OCR fine-tuning dataset.

---

## User Stories

| Role | Goal | So That |
|------|------|---------|
| Data engineer | I can pass a folder of real receipts to `SchemaExtractor` | I get a `DocumentSchema` without any manual field tagging |
| Developer | I can use the `mock` backend | I can develop and test without an API key |
| Pipeline operator | I can serialize the `DocumentSchema` to JSON | I can reuse it across generation runs without re-calling the LLM |
| Client (Air Canada) | I can feed 10,000 international receipts | The system infers multi-language field schemas automatically |

---

## Acceptance Criteria

- [x] AC-1: `SchemaExtractor(SchemaExtractorConfig(backend="mock")).extract([pil_image])` returns a `DocumentSchema` with ≥1 field — no API key required.
- [x] AC-2: `DocumentSchema` and `FieldSchema` are Pydantic models with JSON serialisation roundtrip.
- [x] AC-3: `FieldSchema.field_name` is normalised to `snake_case` (spaces and hyphens → `_`).
- [x] AC-4: `DocumentSchema.confidence` is clamped to `[0.0, 1.0]`.
- [x] AC-5: Calling `extract()` with no images raises `SchemaExtractionError`.
- [x] AC-6: Calling `extract()` with a non-existent path raises `SchemaExtractionError`.
- [x] AC-7: Calling `extract()` with `backend="openai"` and no `OPENAI_API_KEY` raises `SchemaExtractionError("No API key …")`.
- [x] AC-8: Module imports cleanly without `openai` or `anthropic` installed.
- [x] AC-9: `DocumentSchema.to_zone_faker_map()` returns `{field_name: faker_provider}` for all fields.
- [x] AC-10: `DocumentSchema.to_synthesis_zones()` returns zone dicts without `box` or `zone_id`.
- [x] AC-11: `SchemaExtractor.extract_batch()` runs extraction on multiple batches.
- [x] AC-12: All new tests pass (`uv run pytest tests/synthesis/test_field_schema.py tests/synthesis/test_schema_extractor.py -q --no-cov`).

---

## Design

### Public API

```python
from document_simulator.synthesis.schema_extractor import (
    SchemaExtractor,
    SchemaExtractorConfig,
    SchemaExtractionError,
)
from document_simulator.synthesis.field_schema import DocumentSchema, FieldSchema, FieldDataType

# Mock backend (no API key needed)
extractor = SchemaExtractor(SchemaExtractorConfig(backend="mock"))
schema: DocumentSchema = extractor.extract(["receipt1.jpg", "receipt2.jpg"])

# OpenAI backend
extractor = SchemaExtractor(SchemaExtractorConfig(backend="openai"))
schema = extractor.extract(pil_images, document_type_hint="receipt")

# Anthropic backend
extractor = SchemaExtractor(SchemaExtractorConfig(backend="anthropic", model="claude-sonnet-4-6"))
schema = extractor.extract(pil_images)

# Serialise and reload
json_str = schema.model_dump_json()
schema2 = DocumentSchema.model_validate_json(json_str)

# Feed into synthesis pipeline
faker_map = schema.to_zone_faker_map()   # {field_name: faker_provider}
zones = schema.to_synthesis_zones()      # partial ZoneConfig dicts (no box/zone_id)
```

### Data Flow

```
Input: list[str | Path | PIL.Image]
    │
    ▼
SchemaExtractor._load_images()
    │  → validate paths, convert to PIL
    ▼
_image_to_base64(img, max_short_side=768)
    │  → resize (if needed) + JPEG encode + base64
    ▼
backend_fn(images_b64, model, api_key)   ← openai | anthropic | mock
    │  → raw JSON string from LLM
    ▼
_extract_json_block(raw)
    │  → strip markdown fences, extract first {...} block
    ▼
_parse_llm_response(raw, model_id, source_count)
    │  → json.loads → construct FieldSchema list → DocumentSchema
    ▼
Output: DocumentSchema
    ├── .fields: list[FieldSchema]
    ├── .to_zone_faker_map() → dict[str, str]
    └── .to_synthesis_zones() → list[dict]  ← feed to SyntheticDocumentGenerator
```

### Key Interfaces

| Symbol | Kind | Responsibility |
|--------|------|---------------|
| `FieldDataType` | `str` Enum | Semantic data type vocabulary (16 values) |
| `FieldSchema` | Pydantic model | One extracted field with name, type, examples, faker hint |
| `DocumentSchema` | Pydantic model | Full document schema: fields + language + currency + confidence |
| `SchemaExtractorConfig` | Pydantic model | Backend, model, API key, resize params |
| `SchemaExtractor` | class | Orchestrates image loading, LLM call, response parsing |
| `SchemaExtractionError` | exception | API key missing, network failure, no images |
| `SchemaParseError` | exception (subclass) | LLM response not parseable as DocumentSchema |

### Configuration

Settings exposed via `.env` / environment variables:

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `OPENAI_API_KEY` | `str` | `""` | OpenAI API key (read by `SchemaExtractorConfig.effective_api_key()`) |
| `ANTHROPIC_API_KEY` | `str` | `""` | Anthropic API key |

`SchemaExtractorConfig` fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `backend` | `str` | `"openai"` | `"openai"` \| `"anthropic"` \| `"mock"` |
| `model` | `str` | `""` | Model ID; `""` → per-backend default |
| `api_key` | `str\|None` | `None` | Override env var |
| `max_images` | `int` | `5` | Max images per LLM call |
| `max_short_side` | `int` | `768` | Resize shorter side to this before encoding |

---

## Implementation

### Files

| Path | Role |
|------|------|
| `src/document_simulator/synthesis/field_schema.py` | `FieldDataType`, `FieldSchema`, `DocumentSchema` Pydantic models |
| `src/document_simulator/synthesis/schema_extractor.py` | `SchemaExtractor`, `SchemaExtractorConfig`, backend functions, system prompt |
| `tests/synthesis/test_field_schema.py` | Unit tests for models (20 tests) |
| `tests/synthesis/test_schema_extractor.py` | Unit tests for extractor, all backends, error paths (30 tests) |

### Key Architectural Decisions

1. **Lazy imports for `openai` and `anthropic`** — both are imported inside their respective backend functions (`_call_openai`, `_call_anthropic`). The module-level import list contains neither. This means `import document_simulator.synthesis.schema_extractor` never fails regardless of whether these packages are installed, satisfying the "LLM integration is optional" requirement.

2. **`mock` backend for TDD and CI** — a deterministic `_call_mock` function returns a hardcoded JSON string representing a receipt schema. All tests run against this backend; no network call is ever made in the test suite.

3. **System prompt requests `faker_provider` in the LLM response** — the LLM is instructed to suggest a `faker_provider` key from the codebase's known provider vocabulary. This bridges the LLM's understanding of "this field is a date" to the exact string `"date_numeric"` that `ZoneDataSampler` understands.

4. **`DocumentSchema.to_synthesis_zones()` omits `box` and `zone_id`** — these require layout information not available at schema-extraction time. The method returns partial dicts; callers (typically a layout-aware tool or the zone editor UI) add spatial coordinates before constructing `ZoneConfig` objects.

5. **`FieldDataType` as `str` enum** — JSON serialisation uses plain string values, keeping the schema human-readable and forward-compatible with new type values.

### Known Edge Cases & Constraints

- Images with very low resolution or heavy blur may yield low-confidence schemas; `schema.confidence` reflects the LLM's self-assessment.
- The LLM may hallucinate field names or data types for noisy scans; caller should inspect `schema.confidence` and optionally request human review when `confidence < 0.7`.
- `max_images=5` is conservative for cost; for large batches (100+ receipts), callers should sample a representative subset before calling `extract()`.
- `openai` JSON mode (`response_format={"type":"json_object"}`) is not yet enabled to keep the implementation backend-agnostic; `_extract_json_block` handles both plain and fenced JSON from either backend.

---

## Tests

### Test Files

| File | Type | Count | What is covered |
|------|------|-------|-----------------|
| `tests/synthesis/test_field_schema.py` | unit | 18 | `FieldSchema` validation, `DocumentSchema` methods, JSON roundtrip |
| `tests/synthesis/test_schema_extractor.py` | unit | 30 | Image loading, base64 encoding, JSON parsing, mock backend, error paths |

### TDD Cycle Summary

**Red — first failing tests written:**

| Test name | File | Initial failure reason |
|-----------|------|----------------------|
| `test_minimal_construction` | `test_field_schema.py` | `ImportError: cannot import name 'FieldSchema'` |
| `test_extract_from_pil_image` | `test_schema_extractor.py` | `ImportError: cannot import name 'SchemaExtractor'` |
| `test_no_api_key_raises_for_openai` | `test_schema_extractor.py` | `ImportError` |

**Green — minimal implementation:**

`field_schema.py` provided the Pydantic models; `schema_extractor.py` provided `SchemaExtractor` with `mock`, `openai`, and `anthropic` backends plus `_call_mock`, `_extract_json_block`, `_parse_llm_response` helpers. All tests pass without any real LLM API call.

**Refactor — improvements made after green:**

| What changed | Why |
|--------------|-----|
| Added `_SYSTEM_PROMPT` constant with `faker_provider` instructions | Ensures LLM outputs provider keys compatible with `ZoneDataSampler` |
| `SchemaExtractorConfig.effective_model()` with per-backend defaults | Avoids callers having to know model IDs |
| `DocumentSchema.to_synthesis_zones()` | Convenience method for downstream consumers |
| `FieldSchema.cap_examples` validator | Prevents oversized schemas from verbose LLMs |

### How to Run

```bash
# All tests for this feature
uv run pytest tests/synthesis/test_field_schema.py tests/synthesis/test_schema_extractor.py -v --no-cov

# Fast (no coverage overhead)
uv run pytest tests/synthesis/test_field_schema.py tests/synthesis/test_schema_extractor.py -q --no-cov

# Full suite
uv run pytest tests/ -q --no-cov
```

---

## Dependencies

### Requires

| Dependency | Kind | Why |
|------------|------|-----|
| `pydantic>=2.6.0` | external (already in core deps) | `FieldSchema`, `DocumentSchema` models |
| `pillow>=10.2.0` | external (already in core deps) | Image loading and resizing |
| `loguru>=0.7.2` | external (already in core deps) | Structured logging |
| `openai` | external (optional, lazy import) | OpenAI GPT-4o vision calls |
| `anthropic` | external (optional, lazy import) | Anthropic Claude vision calls |

### Required By

| Consumer | How it uses this feature |
|----------|------------------------|
| `synthesis.generator.SyntheticDocumentGenerator` | Consumes `DocumentSchema.to_synthesis_zones()` to build `ZoneConfig` list |
| Zone editor UI / React frontend | Displays extracted fields for user review before generation |

---

## Usage Examples

### Minimal

```python
from document_simulator.synthesis.schema_extractor import SchemaExtractor, SchemaExtractorConfig

extractor = SchemaExtractor(SchemaExtractorConfig(backend="mock"))
schema = extractor.extract(["receipt.jpg"])
print(schema.model_dump_json(indent=2))
```

### Typical

```python
import os
from pathlib import Path
from document_simulator.synthesis.schema_extractor import SchemaExtractor, SchemaExtractorConfig

# Extract from 5 sample receipts using GPT-4o
receipt_paths = list(Path("data/receipts/").glob("*.jpg"))[:5]
extractor = SchemaExtractor(SchemaExtractorConfig(backend="openai"))
schema = extractor.extract(receipt_paths, document_type_hint="receipt")

print(f"Document type: {schema.document_type}")
print(f"Language: {schema.language}, Currency: {schema.currency}")
print(f"Confidence: {schema.confidence:.2%}")
for field in schema.fields:
    print(f"  {field.field_name}: {field.data_type.value} → {field.faker_provider}")

# Save schema for reuse
Path("receipt_schema.json").write_text(schema.model_dump_json(indent=2))
```

### Advanced / Edge Case

```python
from document_simulator.synthesis.schema_extractor import SchemaExtractor, SchemaExtractorConfig
from document_simulator.synthesis.zones import ZoneConfig, SynthesisConfig

# Extract schema, then integrate with synthesis pipeline
extractor = SchemaExtractor(SchemaExtractorConfig(backend="anthropic"))
schema = extractor.extract(receipt_images)

# Get partial zone dicts (no box/zone_id — add layout later)
partial_zones = schema.to_synthesis_zones()

# In a layout-aware UI, user specifies boxes; then construct ZoneConfig:
zones = [
    ZoneConfig(
        zone_id=f"zone_{i}",
        box=[[x1, y1], [x2, y1], [x2, y2], [x1, y2]],  # from UI
        **partial_zone,
    )
    for i, (partial_zone, (x1, y1, x2, y2)) in enumerate(
        zip(partial_zones, layout_boxes)
    )
]
config = SynthesisConfig(zones=zones)
```

---

## Future Work

- [ ] Enable OpenAI JSON mode (`response_format={"type":"json_object"}`) when `backend="openai"` for guaranteed JSON output.
- [ ] Add `extract_from_pdf()` convenience method that rasterises PDF pages via PyMuPDF before extraction.
- [ ] Support `batch_size` > 1 in a single LLM call for cost efficiency (currently all images sent in one call, capped by `max_images`).
- [ ] Add UI page in React zone editor to display extracted schema for human review before generating.
- [ ] Confidence-based human-in-the-loop: flag schemas with `confidence < 0.7` for manual review.
- [ ] Add `extract_merge()` to merge multiple schemas from different document variants into a unified schema.

---

## References

- [Research Findings — LLM Schema Extraction section](../RESEARCH_FINDINGS.md)
- [Feedback from Anand 2026-04-06](../../0_docs/doc simulator/feedback-anand-2026-04-06.md)
- [OpenAI Vision API](https://platform.openai.com/docs/guides/vision)
- [Anthropic Vision API](https://docs.anthropic.com/en/docs/build-with-claude/vision)

---

## Signoff

| Role | Name | Date | Notes |
|------|------|------|-------|
| Implementer | Claude (claude-sonnet-4-6) | 2026-04-06 | Full TDD cycle, mock backend, lazy LLM imports |
| Reviewer | — | — | Pending |
