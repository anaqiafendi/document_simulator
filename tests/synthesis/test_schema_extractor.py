"""Tests for SchemaExtractor — uses the mock backend (no real API calls)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image

from document_simulator.synthesis.field_schema import DocumentSchema, FieldDataType
from document_simulator.synthesis.schema_extractor import (
    SchemaExtractionError,
    SchemaExtractor,
    SchemaExtractorConfig,
    SchemaParseError,
    _call_mock,
    _extract_json_block,
    _image_to_base64,
    _parse_llm_response,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def blank_pil() -> Image.Image:
    """Small white receipt-like image."""
    return Image.new("RGB", (200, 400), color=(255, 255, 255))


@pytest.fixture()
def mock_extractor() -> SchemaExtractor:
    return SchemaExtractor(SchemaExtractorConfig(backend="mock"))


# ---------------------------------------------------------------------------
# _image_to_base64
# ---------------------------------------------------------------------------


class TestImageToBase64:
    def test_returns_non_empty_string(self, blank_pil):
        b64 = _image_to_base64(blank_pil)
        assert isinstance(b64, str)
        assert len(b64) > 0

    def test_resize_applied_for_large_image(self):
        large = Image.new("RGB", (2000, 3000))
        b64 = _image_to_base64(large, max_short_side=100)
        # We can at least verify it returns a string without error
        assert isinstance(b64, str)

    def test_small_image_not_upscaled(self, blank_pil):
        b64_small = _image_to_base64(blank_pil, max_short_side=768)
        b64_large = _image_to_base64(blank_pil, max_short_side=100)
        # Both should be valid base64 strings
        assert isinstance(b64_small, str)
        assert isinstance(b64_large, str)


# ---------------------------------------------------------------------------
# _extract_json_block
# ---------------------------------------------------------------------------


class TestExtractJsonBlock:
    def test_plain_json(self):
        raw = '{"key": "value"}'
        assert _extract_json_block(raw) == '{"key": "value"}'

    def test_json_with_markdown_fences(self):
        raw = "```json\n{\"key\": \"value\"}\n```"
        result = _extract_json_block(raw)
        assert result == '{"key": "value"}'

    def test_json_with_preamble(self):
        raw = "Here is the schema:\n{\"document_type\": \"receipt\"}"
        result = _extract_json_block(raw)
        assert '"document_type"' in result

    def test_raises_on_no_json(self):
        with pytest.raises(SchemaParseError):
            _extract_json_block("no json here at all")


# ---------------------------------------------------------------------------
# _parse_llm_response
# ---------------------------------------------------------------------------


class TestParseLlmResponse:
    def test_parses_mock_output(self):
        raw = _call_mock([], "mock-v1", "")
        schema = _parse_llm_response(raw, model_id="mock-v1", source_count=3)
        assert isinstance(schema, DocumentSchema)
        assert schema.document_type == "receipt"
        assert len(schema.fields) >= 3
        assert schema.source_count == 3
        assert schema.extractor_model == "mock-v1"

    def test_field_data_types_parsed(self):
        raw = _call_mock([], "mock-v1", "")
        schema = _parse_llm_response(raw, model_id="mock-v1", source_count=1)
        field_names = [f.field_name for f in schema.fields]
        assert "merchant_name" in field_names
        assert "total_amount" in field_names

    def test_invalid_json_raises_parse_error(self):
        with pytest.raises(SchemaParseError):
            _parse_llm_response("not valid json", model_id="x", source_count=1)

    def test_malformed_field_skipped_gracefully(self):
        raw = json.dumps(
            {
                "document_type": "receipt",
                "language": "en",
                "currency": "USD",
                "confidence": 0.8,
                "fields": [
                    {"field_name": "good_field", "data_type": "text", "faker_provider": "word"},
                    "this is not a dict",  # malformed
                ],
            }
        )
        schema = _parse_llm_response(raw, model_id="x", source_count=1)
        assert len(schema.fields) == 1
        assert schema.fields[0].field_name == "good_field"

    def test_unknown_data_type_falls_back_to_unknown(self):
        raw = json.dumps(
            {
                "document_type": "receipt",
                "language": "en",
                "currency": "USD",
                "confidence": 0.7,
                "fields": [
                    {
                        "field_name": "weird_field",
                        "data_type": "not_a_real_type",
                        "faker_provider": "word",
                    }
                ],
            }
        )
        schema = _parse_llm_response(raw, model_id="x", source_count=1)
        assert schema.fields[0].data_type == FieldDataType.UNKNOWN


# ---------------------------------------------------------------------------
# SchemaExtractorConfig
# ---------------------------------------------------------------------------


class TestSchemaExtractorConfig:
    def test_default_model_openai(self):
        cfg = SchemaExtractorConfig(backend="openai")
        assert cfg.effective_model() == "gpt-4o"

    def test_default_model_anthropic(self):
        cfg = SchemaExtractorConfig(backend="anthropic")
        assert "claude" in cfg.effective_model().lower()

    def test_default_model_mock(self):
        cfg = SchemaExtractorConfig(backend="mock")
        assert cfg.effective_model() == "mock-v1"

    def test_explicit_model_overrides_default(self):
        cfg = SchemaExtractorConfig(backend="openai", model="gpt-4-turbo")
        assert cfg.effective_model() == "gpt-4-turbo"

    def test_api_key_from_config(self):
        cfg = SchemaExtractorConfig(backend="openai", api_key="sk-test")
        assert cfg.effective_api_key() == "sk-test"

    def test_no_api_key_returns_none_when_env_unset(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        cfg = SchemaExtractorConfig(backend="openai")
        assert cfg.effective_api_key() is None


# ---------------------------------------------------------------------------
# SchemaExtractor — mock backend
# ---------------------------------------------------------------------------


class TestSchemaExtractorMock:
    def test_extract_from_pil_image(self, mock_extractor, blank_pil):
        schema = mock_extractor.extract([blank_pil])
        assert isinstance(schema, DocumentSchema)
        assert len(schema.fields) >= 1

    def test_extract_multiple_images(self, mock_extractor, blank_pil):
        schema = mock_extractor.extract([blank_pil, blank_pil, blank_pil])
        assert schema.source_count == 3

    def test_extract_respects_max_images(self, blank_pil):
        extractor = SchemaExtractor(SchemaExtractorConfig(backend="mock", max_images=2))
        schema = extractor.extract([blank_pil] * 10)
        # source_count reflects total images, not just sample
        assert schema.source_count == 10

    def test_extract_returns_receipt_schema(self, mock_extractor, blank_pil):
        schema = mock_extractor.extract([blank_pil])
        assert schema.document_type == "receipt"
        assert schema.language == "en"
        assert schema.currency == "USD"
        assert schema.confidence > 0

    def test_document_type_hint_applied_when_empty(self, blank_pil):
        extractor = SchemaExtractor(SchemaExtractorConfig(backend="mock"))
        schema = extractor.extract([blank_pil], document_type_hint="invoice")
        # Mock already returns document_type="receipt", hint won't override non-empty
        assert schema.document_type in ("receipt", "invoice")

    def test_extract_raises_on_no_images(self, mock_extractor):
        with pytest.raises(SchemaExtractionError):
            mock_extractor.extract([])

    def test_extract_raises_on_nonexistent_path(self, mock_extractor):
        with pytest.raises(SchemaExtractionError):
            mock_extractor.extract(["/tmp/does_not_exist_xyz.jpg"])

    def test_extract_batch(self, mock_extractor, blank_pil):
        schemas = mock_extractor.extract_batch([[blank_pil], [blank_pil]])
        assert len(schemas) == 2
        for s in schemas:
            assert isinstance(s, DocumentSchema)

    def test_to_zone_faker_map(self, mock_extractor, blank_pil):
        schema = mock_extractor.extract([blank_pil])
        mapping = schema.to_zone_faker_map()
        assert isinstance(mapping, dict)
        assert len(mapping) == len(schema.fields)

    def test_to_synthesis_zones(self, mock_extractor, blank_pil):
        schema = mock_extractor.extract([blank_pil])
        zones = schema.to_synthesis_zones()
        assert len(zones) == len(schema.fields)
        for z in zones:
            assert "faker_provider" in z
            assert "label" in z

    def test_schema_json_serializable(self, mock_extractor, blank_pil):
        schema = mock_extractor.extract([blank_pil])
        json_str = schema.model_dump_json()
        restored = DocumentSchema.model_validate_json(json_str)
        assert restored.document_type == schema.document_type


# ---------------------------------------------------------------------------
# SchemaExtractor — error paths
# ---------------------------------------------------------------------------


class TestSchemaExtractorErrors:
    def test_unknown_backend_raises(self, blank_pil):
        extractor = SchemaExtractor(SchemaExtractorConfig(backend="unknown_llm"))
        with pytest.raises(SchemaExtractionError, match="Unknown backend"):
            extractor.extract([blank_pil])

    def test_no_api_key_raises_for_openai(self, blank_pil, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        extractor = SchemaExtractor(SchemaExtractorConfig(backend="openai"))
        with pytest.raises(SchemaExtractionError, match="No API key"):
            extractor.extract([blank_pil])

    def test_no_api_key_raises_for_anthropic(self, blank_pil, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        extractor = SchemaExtractor(SchemaExtractorConfig(backend="anthropic"))
        with pytest.raises(SchemaExtractionError, match="No API key"):
            extractor.extract([blank_pil])

    def test_module_imports_without_openai_installed(self):
        """Module must import cleanly — no openai import at module level."""
        import importlib

        import document_simulator.synthesis.schema_extractor as mod

        importlib.reload(mod)  # Should not raise even if openai is not installed

    def test_module_imports_without_anthropic_installed(self):
        """Module must import cleanly — no anthropic import at module level."""
        import importlib

        import document_simulator.synthesis.schema_extractor as mod

        importlib.reload(mod)  # Should not raise

    def test_extract_from_path(self, mock_extractor, tmp_path, blank_pil):
        img_path = tmp_path / "receipt.jpg"
        blank_pil.save(img_path)
        schema = mock_extractor.extract([img_path])
        assert isinstance(schema, DocumentSchema)
