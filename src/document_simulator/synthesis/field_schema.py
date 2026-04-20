"""Pydantic models for LLM-extracted document field schemas.

These models describe the structured output produced by ``SchemaExtractor`` and
consumed by ``SyntheticDocumentGenerator`` / ``ZoneDataSampler`` to generate
realistic per-field values without manual zone tagging.

The model supports:
- Per-field semantic type, Faker provider, examples, description
- Per-field bounding box (normalised to [0, 1] image coordinates)
- Per-field language (BCP-47) and currency (ISO 4217) overrides for
  multi-lingual / multi-currency documents
- Line-items (each with its own currency + language + bbox)
- Per-image schemas — each uploaded scan yields its own ``DocumentSchema``
  so multi-image uploads are no longer force-consolidated
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class FieldDataType(str, Enum):
    """Semantic data type of a document field.

    Enum values are lowercase strings so the schema is easy to hand-edit
    and LLM outputs (which tend to be lowercase) map cleanly.
    """

    TEXT = "text"
    NAME = "name"
    DATE = "date"
    TIME = "time"
    DATETIME = "datetime"
    NUMBER = "number"
    AMOUNT = "amount"
    CURRENCY = "currency"
    PERCENTAGE = "percentage"
    CURRENCY_CODE = "currency_code"
    LANGUAGE_CODE = "language_code"
    PHONE = "phone"
    EMAIL = "email"
    ADDRESS = "address"
    COMPANY = "company"
    ID = "id"
    CHECKBOX = "checkbox"
    SIGNATURE = "signature"
    LINE_ITEMS = "line_items"
    BOOLEAN = "boolean"
    OTHER = "other"
    UNKNOWN = "unknown"


class BoundingBox(BaseModel):
    """Axis-aligned bounding box on a document image.

    Coordinates are normalised to [0, 1] so they're resolution-independent.
    Origin is the top-left corner of the image.
    """

    x1: float = Field(..., ge=0.0, le=1.0)
    y1: float = Field(..., ge=0.0, le=1.0)
    x2: float = Field(..., ge=0.0, le=1.0)
    y2: float = Field(..., ge=0.0, le=1.0)

    @field_validator("x2")
    @classmethod
    def _x2_ge_x1(cls, v: float, info: Any) -> float:
        x1 = info.data.get("x1", 0.0)
        return max(v, x1)

    @field_validator("y2")
    @classmethod
    def _y2_ge_y1(cls, v: float, info: Any) -> float:
        y1 = info.data.get("y1", 0.0)
        return max(v, y1)


class LineItem(BaseModel):
    """A single line item extracted from an invoice / receipt.

    Each line item carries its own language and currency so a receipt whose
    items are billed in USD but totalled in CAD can round-trip faithfully.
    """

    description: str = ""
    quantity: float | None = None
    unit_price: str | None = None  # kept as string to preserve "€19.99" style
    total: str | None = None
    currency: str | None = None  # ISO 4217
    language: str | None = None  # BCP-47 / ISO 639-1
    bbox: BoundingBox | None = None


class FieldSchema(BaseModel):
    """Schema for a single field extracted from a document scan.

    Backward-compatible surface (``display_label``, ``value_pattern``,
    ``notes``) is preserved so earlier tests and FDD examples keep working.
    New optional attributes carry per-field spatial + localisation metadata.
    """

    field_name: str
    display_label: str = ""
    data_type: FieldDataType = FieldDataType.UNKNOWN
    required: bool = True
    example_values: list[str] = Field(default_factory=list)
    value_pattern: str | None = None
    faker_provider: str = "word"
    description: str = ""
    notes: str = ""
    bbox: BoundingBox | None = None
    language: str | None = None
    currency: str | None = None

    @field_validator("field_name")
    @classmethod
    def _normalise_field_name(cls, v: str) -> str:
        """Lower-case and replace spaces/hyphens with underscores."""
        return v.strip().lower().replace(" ", "_").replace("-", "_")

    @field_validator("example_values")
    @classmethod
    def _cap_examples(cls, v: list[str]) -> list[str]:
        """Keep at most 10 examples to bound schema size."""
        return v[:10]

    @field_validator("data_type", mode="before")
    @classmethod
    def _coerce_data_type(cls, v: Any) -> Any:
        """Fall back to ``UNKNOWN`` for values the LLM invented."""
        if v is None or v == "":
            return FieldDataType.UNKNOWN
        if isinstance(v, FieldDataType):
            return v
        if isinstance(v, str):
            try:
                return FieldDataType(v.lower())
            except ValueError:
                return FieldDataType.UNKNOWN
        return FieldDataType.UNKNOWN


class DocumentSchema(BaseModel):
    """Full schema for one document, derived from one or more sample scans.

    Attributes:
        document_type:  High-level label (``"receipt"``, ``"invoice"``, …).
        language:       Primary language of the document (ISO 639-1 / BCP-47).
        currency:       Primary currency (ISO 4217).
        fields:         Ordered list of :class:`FieldSchema`.
        line_items:     Optional extracted line items (invoices/receipts).
        confidence:     0–1 float; LLM-reported extraction confidence.
        source_count:   Number of scans analysed to build this schema.
        source_image_index: Index of the source image (0-based) when the
            schema was extracted per-image.
        source_image_width/height: Original image dimensions — used by the UI
            to place normalised bboxes at the right pixel positions.
        raw_llm_output: Verbatim LLM JSON (for debugging / replay).
        extractor_model: Specific model ID used (``"gpt-4o"``, ``"gemini-…"``).
        backend_used:   Backend family (``"mock"``, ``"gemini"``, …).
        notes:          Free-form notes / summary from the extractor.
    """

    document_type: str = "receipt"
    language: str = "en"
    currency: str = "USD"
    fields: list[FieldSchema] = Field(default_factory=list)
    line_items: list[LineItem] = Field(default_factory=list)
    confidence: float = 0.0
    source_count: int = 0
    source_image_index: int = 0
    source_image_width: int | None = None
    source_image_height: int | None = None
    raw_llm_output: str = ""
    extractor_model: str = ""
    backend_used: str = ""
    notes: str = ""

    @field_validator("confidence")
    @classmethod
    def _clamp_confidence(cls, v: float) -> float:
        return max(0.0, min(1.0, v))

    def get_field(self, field_name: str) -> FieldSchema | None:
        """Return the :class:`FieldSchema` whose name matches, or ``None``."""
        target = field_name.strip().lower().replace(" ", "_").replace("-", "_")
        for f in self.fields:
            if f.field_name == target:
                return f
        return None

    def to_zone_faker_map(self) -> dict[str, str]:
        """Return ``{field_name: faker_provider}`` for all fields."""
        return {f.field_name: f.faker_provider for f in self.fields}

    def to_synthesis_zones(self) -> list[dict[str, Any]]:
        """Convert fields to a list of partial ``ZoneConfig`` dicts.

        Omits ``box`` and ``zone_id`` (which require layout info) but
        includes everything needed to drive data generation.
        """
        zones: list[dict[str, Any]] = []
        for f in self.fields:
            zones.append(
                {
                    "label": f.display_label or f.field_name,
                    "faker_provider": f.faker_provider,
                    "custom_values": f.example_values[:5],
                    "language": f.language or self.language,
                    "currency": f.currency or self.currency,
                }
            )
        return zones


# BCP-47 / ISO 639-1 language code → preferred Faker locale.
# Only the most common mappings; unknown codes fall back to ``en_US``.
_FAKER_LOCALE_MAP: dict[str, str] = {
    "en": "en_US",
    "en-us": "en_US",
    "en-gb": "en_GB",
    "en-ca": "en_CA",
    "fr": "fr_FR",
    "fr-fr": "fr_FR",
    "fr-ca": "fr_CA",
    "es": "es_ES",
    "es-es": "es_ES",
    "es-mx": "es_MX",
    "de": "de_DE",
    "it": "it_IT",
    "pt": "pt_BR",
    "pt-br": "pt_BR",
    "pt-pt": "pt_PT",
    "nl": "nl_NL",
    "ja": "ja_JP",
    "zh": "zh_CN",
    "zh-cn": "zh_CN",
    "zh-tw": "zh_TW",
    "ko": "ko_KR",
    "ru": "ru_RU",
    "ar": "ar_AA",
    "tr": "tr_TR",
    "pl": "pl_PL",
    "sv": "sv_SE",
    "no": "no_NO",
    "da": "da_DK",
    "fi": "fi_FI",
    "th": "th_TH",
    "vi": "vi_VN",
    "id": "id_ID",
    "ms": "ms_MY",
    "hi": "hi_IN",
}


def to_faker_locale(language: str | None) -> str:
    """Map a BCP-47 / ISO 639-1 language code to a Faker locale string.

    Returns ``"en_US"`` for ``None`` or unknown codes.
    """
    if not language:
        return "en_US"
    key = language.strip().lower().replace("_", "-")
    if key in _FAKER_LOCALE_MAP:
        return _FAKER_LOCALE_MAP[key]
    # Also try the primary subtag (e.g. "fr-XYZ" → "fr")
    primary = key.split("-", 1)[0]
    return _FAKER_LOCALE_MAP.get(primary, "en_US")


# ISO 4217 currency code → (symbol, decimal places).
_CURRENCY_INFO: dict[str, tuple[str, int]] = {
    "USD": ("$", 2), "CAD": ("CA$", 2), "AUD": ("A$", 2), "NZD": ("NZ$", 2),
    "EUR": ("€", 2), "GBP": ("£", 2), "JPY": ("¥", 0), "CNY": ("¥", 2),
    "KRW": ("₩", 0), "INR": ("₹", 2), "RUB": ("₽", 2), "BRL": ("R$", 2),
    "MXN": ("MX$", 2), "CHF": ("CHF ", 2), "SEK": ("kr", 2), "NOK": ("kr", 2),
    "DKK": ("kr", 2), "PLN": ("zł", 2), "TRY": ("₺", 2), "THB": ("฿", 2),
    "SGD": ("S$", 2), "MYR": ("RM", 2), "IDR": ("Rp", 0), "PHP": ("₱", 2),
    "VND": ("₫", 0), "HKD": ("HK$", 2), "TWD": ("NT$", 2), "AED": ("AED ", 2),
    "SAR": ("SAR ", 2), "ZAR": ("R", 2),
}


def format_currency(amount: float, currency: str | None) -> str:
    """Format ``amount`` for the given ISO 4217 code — best effort."""
    code = (currency or "USD").upper()
    symbol, places = _CURRENCY_INFO.get(code, (f"{code} ", 2))
    if places == 0:
        return f"{symbol}{int(round(amount)):,}"
    return f"{symbol}{amount:,.{places}f}"


__all__ = [
    "BoundingBox",
    "DocumentSchema",
    "FieldDataType",
    "FieldSchema",
    "LineItem",
    "to_faker_locale",
    "format_currency",
]
