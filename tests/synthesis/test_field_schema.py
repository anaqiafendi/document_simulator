"""Tests for FieldSchema and DocumentSchema models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from document_simulator.synthesis.field_schema import (
    DocumentSchema,
    FieldDataType,
    FieldSchema,
)


# ---------------------------------------------------------------------------
# FieldSchema
# ---------------------------------------------------------------------------


class TestFieldSchema:
    def test_minimal_construction(self):
        f = FieldSchema(field_name="merchant_name")
        assert f.field_name == "merchant_name"
        assert f.data_type == FieldDataType.UNKNOWN
        assert f.required is True
        assert f.example_values == []
        assert f.faker_provider == "word"

    def test_field_name_normalised(self):
        f = FieldSchema(field_name="Merchant Name")
        assert f.field_name == "merchant_name"

    def test_field_name_hyphen_normalised(self):
        f = FieldSchema(field_name="total-amount")
        assert f.field_name == "total_amount"

    def test_example_values_capped_at_10(self):
        f = FieldSchema(field_name="x", example_values=[str(i) for i in range(20)])
        assert len(f.example_values) == 10

    def test_data_type_enum_values(self):
        for member in FieldDataType:
            f = FieldSchema(field_name="x", data_type=member)
            assert f.data_type == member

    def test_full_construction(self):
        f = FieldSchema(
            field_name="transaction_date",
            display_label="Date",
            data_type=FieldDataType.DATE,
            required=True,
            example_values=["2024-03-15"],
            value_pattern=r"\d{4}-\d{2}-\d{2}",
            faker_provider="date_numeric",
            notes="ISO format",
        )
        assert f.display_label == "Date"
        assert f.data_type == FieldDataType.DATE
        assert f.value_pattern == r"\d{4}-\d{2}-\d{2}"


# ---------------------------------------------------------------------------
# DocumentSchema
# ---------------------------------------------------------------------------


class TestDocumentSchema:
    def _make_schema(self, n_fields: int = 3) -> DocumentSchema:
        fields = [
            FieldSchema(
                field_name=f"field_{i}",
                data_type=FieldDataType.TEXT,
                faker_provider="word",
            )
            for i in range(n_fields)
        ]
        return DocumentSchema(
            document_type="receipt",
            language="en",
            currency="USD",
            fields=fields,
            confidence=0.9,
            source_count=5,
        )

    def test_minimal_construction(self):
        schema = DocumentSchema()
        assert schema.document_type == "receipt"
        assert schema.language == "en"
        assert schema.fields == []
        assert schema.confidence == 0.0

    def test_confidence_clamped_high(self):
        schema = DocumentSchema(confidence=1.5)
        assert schema.confidence == 1.0

    def test_confidence_clamped_low(self):
        schema = DocumentSchema(confidence=-0.1)
        assert schema.confidence == 0.0

    def test_get_field_found(self):
        schema = self._make_schema()
        f = schema.get_field("field_0")
        assert f is not None
        assert f.field_name == "field_0"

    def test_get_field_not_found(self):
        schema = self._make_schema()
        assert schema.get_field("nonexistent") is None

    def test_to_zone_faker_map(self):
        schema = self._make_schema(2)
        mapping = schema.to_zone_faker_map()
        assert mapping == {"field_0": "word", "field_1": "word"}

    def test_to_synthesis_zones(self):
        schema = self._make_schema(2)
        zones = schema.to_synthesis_zones()
        assert len(zones) == 2
        assert "faker_provider" in zones[0]
        assert "label" in zones[0]
        # box and zone_id must NOT be present (caller fills them)
        assert "box" not in zones[0]
        assert "zone_id" not in zones[0]

    def test_json_serialization_roundtrip(self):
        schema = self._make_schema(2)
        json_str = schema.model_dump_json()
        restored = DocumentSchema.model_validate_json(json_str)
        assert restored.document_type == schema.document_type
        assert len(restored.fields) == len(schema.fields)

    def test_source_count_stored(self):
        schema = self._make_schema()
        schema2 = schema.model_copy(update={"source_count": 42})
        assert schema2.source_count == 42
