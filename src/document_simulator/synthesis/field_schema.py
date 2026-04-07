"""FieldSchema and DocumentSchema — Pydantic models for LLM-extracted field schemas.

These models represent the structured output produced by ``SchemaExtractor`` and
consumed by ``SyntheticDocumentGenerator`` / ``ZoneDataSampler`` to generate
realistic per-field values without manual zone tagging.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class FieldDataType(str, Enum):
    """Semantic data type for a document field."""

    TEXT = "text"
    NAME = "name"
    DATE = "date"
    AMOUNT = "amount"
    PHONE = "phone"
    EMAIL = "email"
    ADDRESS = "address"
    NUMBER = "number"
    PERCENTAGE = "percentage"
    CURRENCY_CODE = "currency_code"
    LANGUAGE_CODE = "language_code"
    LINE_ITEMS = "line_items"
    BOOLEAN = "boolean"
    UNKNOWN = "unknown"


class FieldSchema(BaseModel):
    """Schema for a single field extracted from a document scan.

    Attributes:
        field_name:    Normalised machine-readable name (e.g. ``"merchant_name"``).
        display_label: Human-readable label as it appears in the document.
        data_type:     Semantic type used to drive Faker generation.
        required:      Whether the field is present in most documents.
        example_values: Up to 10 raw string examples observed by the LLM.
        value_pattern:  Optional regex or format hint inferred by the LLM.
        faker_provider: Suggested Faker provider / custom provider key.
        notes:          Free-form notes from the LLM (language, units, etc.).
    """

    field_name: str
    display_label: str = ""
    data_type: FieldDataType = FieldDataType.UNKNOWN
    required: bool = True
    example_values: list[str] = Field(default_factory=list)
    value_pattern: str | None = None
    faker_provider: str = "word"
    notes: str = ""

    @field_validator("field_name")
    @classmethod
    def normalise_field_name(cls, v: str) -> str:
        """Lower-case and replace spaces/hyphens with underscores."""
        return v.strip().lower().replace(" ", "_").replace("-", "_")

    @field_validator("example_values")
    @classmethod
    def cap_examples(cls, v: list[str]) -> list[str]:
        """Keep at most 10 examples to limit schema size."""
        return v[:10]


class DocumentSchema(BaseModel):
    """Complete schema for one document type, extracted from a batch of scans.

    Attributes:
        document_type:  High-level label (e.g. ``"receipt"``, ``"invoice"``).
        language:       Primary language detected (ISO 639-1 code, e.g. ``"en"``).
        currency:       Primary currency symbol or ISO code observed.
        fields:         Ordered list of :class:`FieldSchema` objects.
        confidence:     0–1 float; LLM self-reported extraction confidence.
        source_count:   Number of scans analysed to build this schema.
        raw_llm_output: The verbatim LLM JSON string (for debugging / replay).
        extractor_model: Model ID used for extraction (e.g. ``"gpt-4o"``).
    """

    document_type: str = "receipt"
    language: str = "en"
    currency: str = "USD"
    fields: list[FieldSchema] = Field(default_factory=list)
    confidence: float = 0.0
    source_count: int = 0
    raw_llm_output: str = ""
    extractor_model: str = ""

    @field_validator("confidence")
    @classmethod
    def clamp_confidence(cls, v: float) -> float:
        return max(0.0, min(1.0, v))

    def get_field(self, field_name: str) -> FieldSchema | None:
        """Return the :class:`FieldSchema` for *field_name*, or ``None``."""
        for f in self.fields:
            if f.field_name == field_name:
                return f
        return None

    def to_zone_faker_map(self) -> dict[str, str]:
        """Return ``{field_name: faker_provider}`` for all fields.

        Convenience method for downstream consumers that need to map field
        names to Faker provider strings.
        """
        return {f.field_name: f.faker_provider for f in self.fields}

    def to_synthesis_zones(self) -> list[dict[str, Any]]:
        """Convert fields to a list of partial ZoneConfig dicts.

        The returned dicts omit ``box`` and ``zone_id`` (which require layout
        information not available at schema-extraction time) but include all
        data-generation fields.  Callers should add ``box`` and ``zone_id``
        before constructing :class:`~document_simulator.synthesis.zones.ZoneConfig`.
        """
        zones = []
        for field in self.fields:
            zones.append(
                {
                    "label": field.display_label or field.field_name,
                    "faker_provider": field.faker_provider,
                    "custom_values": field.example_values[:5],
                }
            )
        return zones
