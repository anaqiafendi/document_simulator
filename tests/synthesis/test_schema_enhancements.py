"""Tests for the PR #27 enhancement follow-up.

Covers the feedback points from the 2026-04-19 review comment:

1. Per-image schemas — ``extract_per_image`` returns one schema per input
2. Bounding boxes on fields and line items (normalised to [0, 1])
3. ``/api/synthesis/faker-providers`` catalogue endpoint + integration
4. Line-item extraction (mock backend emits them with currency / language)
5. Multi-language / multi-currency per-field metadata
6. Schema carries language and currency per field and per document
7. Faker uses the per-zone locale + currency when sampling
"""

from __future__ import annotations

import pytest
from PIL import Image

from document_simulator.synthesis.field_schema import (
    BoundingBox,
    DocumentSchema,
    FieldDataType,
    FieldSchema,
    LineItem,
    format_currency,
    to_faker_locale,
)
from document_simulator.synthesis.sampler import (
    ZoneDataSampler,
    list_currency_codes,
    list_faker_providers,
)
from document_simulator.synthesis.schema_extractor import (
    SchemaExtractor,
    SchemaExtractorConfig,
)
from document_simulator.synthesis.zones import ZoneConfig


@pytest.fixture()
def mock_extractor() -> SchemaExtractor:
    return SchemaExtractor(SchemaExtractorConfig(backend="mock"))


@pytest.fixture()
def blank_image() -> Image.Image:
    return Image.new("RGB", (400, 600), color=(255, 255, 255))


# ---------------------------------------------------------------------------
# Per-image extraction
# ---------------------------------------------------------------------------


class TestPerImageExtraction:
    def test_extract_per_image_returns_one_schema_each(self, mock_extractor, blank_image):
        schemas = mock_extractor.extract_per_image([blank_image, blank_image, blank_image])
        assert len(schemas) == 3
        for i, s in enumerate(schemas):
            assert isinstance(s, DocumentSchema)
            assert s.source_image_index == i

    def test_schemas_include_image_dimensions(self, mock_extractor, blank_image):
        schemas = mock_extractor.extract_per_image([blank_image])
        assert schemas[0].source_image_width == 400
        assert schemas[0].source_image_height == 600

    def test_document_type_hint_applied_when_empty(self, blank_image):
        # Mock already returns "receipt" by default; hint biases it the other way
        ex = SchemaExtractor(SchemaExtractorConfig(backend="mock"))
        schemas = ex.extract_per_image([blank_image], document_type_hint="invoice")
        assert schemas[0].document_type == "invoice"


# ---------------------------------------------------------------------------
# Bounding boxes
# ---------------------------------------------------------------------------


class TestBoundingBoxes:
    def test_mock_schema_attaches_bboxes(self, mock_extractor, blank_image):
        schema = mock_extractor.extract([blank_image])
        # Mock schema has 4 fields with bboxes
        bboxes = [f.bbox for f in schema.fields if f.bbox is not None]
        assert len(bboxes) == 4
        for bb in bboxes:
            assert 0.0 <= bb.x1 <= 1.0
            assert 0.0 <= bb.y1 <= 1.0
            assert bb.x2 >= bb.x1
            assert bb.y2 >= bb.y1

    def test_bounding_box_rejects_out_of_range(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            BoundingBox(x1=0.0, y1=0.0, x2=1.2, y2=0.5)

    def test_bounding_box_x2_clamped_to_at_least_x1(self):
        bb = BoundingBox(x1=0.5, y1=0.5, x2=0.2, y2=0.9)
        assert bb.x2 == 0.5


# ---------------------------------------------------------------------------
# Language + currency per field
# ---------------------------------------------------------------------------


class TestFieldLocaleMetadata:
    def test_field_carries_language_and_currency(self):
        f = FieldSchema(
            field_name="total",
            data_type=FieldDataType.CURRENCY,
            language="fr",
            currency="CAD",
        )
        assert f.language == "fr"
        assert f.currency == "CAD"

    def test_mock_total_amount_field_has_currency(self, mock_extractor, blank_image):
        schema = mock_extractor.extract([blank_image])
        total = schema.get_field("total_amount")
        assert total is not None
        assert total.currency == "USD"
        assert total.language == "en"

    def test_to_synthesis_zones_propagates_language_and_currency(self):
        s = DocumentSchema(
            language="fr",
            currency="EUR",
            fields=[
                FieldSchema(field_name="montant", data_type=FieldDataType.CURRENCY),
                FieldSchema(
                    field_name="date_naissance",
                    data_type=FieldDataType.DATE,
                    language="fr",
                    currency=None,
                ),
            ],
        )
        zones = s.to_synthesis_zones()
        assert zones[0]["language"] == "fr"
        assert zones[0]["currency"] == "EUR"
        assert zones[1]["language"] == "fr"


class TestLocaleMapping:
    def test_english_default(self):
        assert to_faker_locale("en") == "en_US"
        assert to_faker_locale(None) == "en_US"
        assert to_faker_locale("") == "en_US"

    def test_french_variants(self):
        assert to_faker_locale("fr") == "fr_FR"
        assert to_faker_locale("fr-CA") == "fr_CA"

    def test_unknown_language_falls_back(self):
        assert to_faker_locale("xyz") == "en_US"

    def test_japanese(self):
        assert to_faker_locale("ja") == "ja_JP"


class TestCurrencyFormatting:
    def test_usd(self):
        assert "$" in format_currency(1234.5, "USD")

    def test_jpy_no_decimals(self):
        out = format_currency(1234.56, "JPY")
        assert out == "¥1,235"

    def test_eur(self):
        out = format_currency(42.0, "EUR")
        assert "€" in out and "42" in out

    def test_unknown_code(self):
        out = format_currency(100, "XYZ")
        assert "XYZ" in out


# ---------------------------------------------------------------------------
# Line items
# ---------------------------------------------------------------------------


class TestLineItems:
    def test_mock_schema_has_line_items(self, mock_extractor, blank_image):
        schema = mock_extractor.extract([blank_image])
        assert len(schema.line_items) == 2
        for li in schema.line_items:
            assert isinstance(li, LineItem)
            assert li.currency == "USD"
            assert li.language == "en"

    def test_line_item_has_bbox(self, mock_extractor, blank_image):
        schema = mock_extractor.extract([blank_image])
        for li in schema.line_items:
            assert li.bbox is not None

    def test_line_item_optional_fields(self):
        li = LineItem(description="Coffee")
        assert li.quantity is None
        assert li.currency is None
        assert li.bbox is None


# ---------------------------------------------------------------------------
# Faker provider catalogue
# ---------------------------------------------------------------------------


class TestFakerProvidersCatalogue:
    def test_catalogue_has_expected_categories(self):
        cat = list_faker_providers()
        for required in ["identity", "static", "custom", "person", "address", "date_time", "finance"]:
            assert required in cat, f"missing category: {required}"

    def test_custom_prices_present(self):
        cat = list_faker_providers()
        custom_names = [p["name"] for p in cat["custom"]]
        for n in ["price_short", "price_medium", "price_large", "pricetag"]:
            assert n in custom_names

    def test_person_provider_shapes(self):
        cat = list_faker_providers()
        entry = next(p for p in cat["person"] if p["name"] == "name")
        assert "label" in entry and "description" in entry

    def test_currency_codes_non_empty(self):
        codes = list_currency_codes()
        assert len(codes) > 20
        usd = next(c for c in codes if c["code"] == "USD")
        assert usd["symbol"] == "$"


# ---------------------------------------------------------------------------
# Sampler — locale + currency aware
# ---------------------------------------------------------------------------


class TestSamplerLocale:
    def _zone(self, **kwargs) -> ZoneConfig:
        return ZoneConfig(
            zone_id="z1",
            label="L",
            box=[[0, 0], [100, 0], [100, 50], [0, 50]],
            faker_provider=kwargs.pop("faker_provider", "name"),
            **kwargs,
        )

    def test_default_locale_and_currency_unchanged(self):
        zone = self._zone(faker_provider="name")
        out = ZoneDataSampler.sample(zone, identity={}, seed=42)
        assert isinstance(out, str) and len(out) > 0

    def test_pricetag_respects_currency(self):
        zone = self._zone(faker_provider="pricetag", currency="EUR")
        out = ZoneDataSampler.sample(zone, identity={}, seed=7)
        assert "€" in out

    def test_pricetag_respects_currency_via_argument(self):
        zone = self._zone(faker_provider="pricetag")
        out = ZoneDataSampler.sample(zone, identity={}, seed=7, currency="JPY")
        assert "¥" in out
        # JPY has 0 decimals — no decimal point expected
        assert "." not in out

    def test_french_locale_street_address(self):
        # "street_address" is a standard Faker method (not an identity provider),
        # so it exercises the locale branch end-to-end.
        zone = self._zone(faker_provider="street_address", language="fr")
        out = ZoneDataSampler.sample(zone, identity={}, seed=7)
        assert isinstance(out, str) and len(out) > 0

    def test_bothify_fallback_still_works(self):
        zone = self._zone(faker_provider="bothify:AA-####")
        out = ZoneDataSampler.sample(zone, identity={}, seed=7)
        assert len(out) == 7 and out[2] == "-"
