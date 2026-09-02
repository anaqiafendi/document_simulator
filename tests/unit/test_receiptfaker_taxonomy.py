"""Tests for ReceiptFaker template extraction and visual-feature taxonomy."""

from __future__ import annotations

import json

import pytest

from document_simulator.data.receiptfaker.schema import ReceiptTemplate
from document_simulator.data.receiptfaker.scrape import extract_template_json, reassemble_flight
from document_simulator.data.receiptfaker.taxonomy import (
    _classify_role,
    build_taxonomy,
    label_template,
)


def _template_payload(**overrides) -> dict:
    """A minimal but realistic template payload."""
    payload = {
        "id": "abc123",
        "slug": "Demo-Receipt",
        "name": "Demo Receipt",
        "published": True,
        "fontType": "MERCHANT_COPY",
        "numberFormat": "LEFT",
        "backgroundType": "CRUMPLED_1",
        "textColor": "#101828",
        "sections": [
            {
                "id": "s1",
                "type": "HEADER",
                "alignment": "CENTER",
                "logo": "https://example.test/logo.jpg",
                "businessDetails": "DEMO CO\n1 High Street",
                "bottomDivider": True,
                "bottomDividerType": "DASHES",
                "date": "$undefined",
            },
            {
                "id": "s2",
                "type": "PAYMENT",
                "isCash": False,
                "cashFields": [],
                "cardFields": [
                    {"title": "BURGER", "value": "7.25"},
                    {"title": "Subtotal", "value": "18.42"},
                    {"title": "Tax", "value": "3.68"},
                    {"title": "Dine In Total", "value": "22.10"},
                    {"title": "Cred Cards #XXXX8497", "value": "22.10"},
                ],
                "bottomDivider": True,
                "bottomDividerType": "DASHES",
            },
            {
                "id": "s3",
                "type": "CUSTOM",
                "alignment": "CENTER",
                "custom": "Thank you!",
                "bottomDivider": False,
                "bottomDividerType": "SOLID",
            },
        ],
    }
    payload.update(overrides)
    return payload


# --------------------------------------------------------------------------- #
# Flight-payload extraction
# --------------------------------------------------------------------------- #
def test_reassemble_flight_concatenates_chunks() -> None:
    html = (
        '<script>self.__next_f.push([1,"hel"])</script>'
        '<script>self.__next_f.push([1,"lo \\"world\\""])</script>'
    )
    assert reassemble_flight(html) == 'hello "world"'


def test_extract_template_json_recovers_embedded_template() -> None:
    payload = _template_payload()
    chunk = json.dumps(f'6:["$","div",null,{{"template":{json.dumps(payload)},"x":1}}]')
    html = f"<script>self.__next_f.push([1,{chunk}])</script>"

    extracted = extract_template_json(html)

    assert extracted is not None
    assert extracted["slug"] == "Demo-Receipt"
    assert len(extracted["sections"]) == 3


def test_extract_template_json_returns_none_without_payload() -> None:
    assert extract_template_json("<html><body>nothing here</body></html>") is None


# --------------------------------------------------------------------------- #
# Schema
# --------------------------------------------------------------------------- #
def test_schema_normalises_rsc_sentinels() -> None:
    template = ReceiptTemplate.model_validate(_template_payload(createdAt="$D2026-08-23T15:44:30Z"))

    assert template.sections[0].date is None  # "$undefined" -> None
    assert template.created_at == "2026-08-23T15:44:30Z"  # "$D<iso>" -> iso


def test_section_types_expose_layout_signature() -> None:
    template = ReceiptTemplate.model_validate(_template_payload())
    assert template.section_types == ["HEADER", "PAYMENT", "CUSTOM"]


def test_payment_fields_follow_cash_flag() -> None:
    payload = _template_payload()
    payload["sections"][1]["isCash"] = True
    payload["sections"][1]["cashFields"] = [{"title": "Cash", "value": "25.00"}]
    template = ReceiptTemplate.model_validate(payload)

    assert [f.title for f in template.sections[1].payment_fields] == ["Cash"]


# --------------------------------------------------------------------------- #
# Role classification
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("Subtotal", "SUBTOTAL"),
        ("Sub-Total", "SUBTOTAL"),
        ("Tax", "TAX"),
        ("VAT 20%", "TAX"),
        ("Dine In Total", "TOTAL"),
        ("Cred Cards #XXXX8497", "TENDER"),
        ("Auth:161294", "AUTH"),
        ("Change", "CHANGE"),
        ("Table: 14", "META"),
        ("SGL STILTON STACK", "ITEM"),
        ("", "BLANK"),
    ],
)
def test_classify_role(title: str, expected: str) -> None:
    assert _classify_role(title) == expected


def test_subtotal_beats_total_pattern() -> None:
    """'Subtotal' must not be swallowed by the broader TOTAL pattern."""
    assert _classify_role("Subtotal") == "SUBTOTAL"


# --------------------------------------------------------------------------- #
# Labelling
# --------------------------------------------------------------------------- #
def test_label_template_assigns_every_dimension() -> None:
    template = ReceiptTemplate.model_validate(_template_payload())
    labels = label_template(template)

    assert labels.font_type == "MERCHANT_COPY"
    assert labels.merchant_block_position == "TOP"
    assert labels.logo_placement == "TOP"
    assert labels.divider_style == "DASHES"
    assert labels.layout_signature == "HEADER|PAYMENT|CUSTOM"
    assert labels.money_row_order == "ITEM>SUBTOTAL>TAX>TOTAL>TENDER"
    assert labels.header_alignment == "CENTER"
    assert labels.section_count == 3


def test_divider_style_ignores_undrawn_dividers() -> None:
    """A bottomDividerType on a section with bottomDivider=False is not drawn."""
    payload = _template_payload()
    for section in payload["sections"]:
        section["bottomDivider"] = False
    template = ReceiptTemplate.model_validate(payload)

    assert label_template(template).divider_style == "NONE"


def test_logo_placement_is_none_without_logo() -> None:
    payload = _template_payload()
    payload["sections"][0]["logo"] = ""
    template = ReceiptTemplate.model_validate(payload)

    assert label_template(template).logo_placement == "NONE"


def test_bottom_placement_detected() -> None:
    """A merchant block in the last section is labelled BOTTOM, not TOP."""
    payload = _template_payload()
    payload["sections"][0].pop("businessDetails")
    payload["sections"][0]["type"] = "CUSTOM"
    payload["sections"][2]["businessDetails"] = "DEMO CO\n1 High Street"
    template = ReceiptTemplate.model_validate(payload)

    assert label_template(template).merchant_block_position == "BOTTOM"


def test_group_key_matches_for_identical_templates() -> None:
    a = label_template(ReceiptTemplate.model_validate(_template_payload(slug="a", name="A")))
    b = label_template(ReceiptTemplate.model_validate(_template_payload(slug="b", name="B")))

    assert a.group_key() == b.group_key()


def test_money_row_order_spans_items_and_payment_blocks() -> None:
    """ITEMS totalLines and PAYMENT rows contribute to one ordered sequence."""
    payload = _template_payload()
    payload["sections"].insert(
        1,
        {
            "id": "s1b",
            "type": "ITEMS",
            "items": [{"quantity": "2", "description": "FRIES", "total": "3.50"}],
            "totalLines": [{"title": "Subtotal", "value": "3.50"}],
            "total": "3.50",
            "totalText": "Total",
            "totalDivider": True,
            "totalDividerType": "EMPTY",
            "bottomDivider": False,
            "bottomDividerType": "DASHES",
        },
    )
    labels = label_template(ReceiptTemplate.model_validate(payload))

    assert labels.money_row_order.startswith("ITEM>SUBTOTAL>TOTAL>")
    assert labels.quantity_column == "PRESENT"
    assert labels.total_divider_style == "EMPTY"


def test_quantity_column_absent_when_items_have_no_quantity() -> None:
    payload = _template_payload()
    payload["sections"].insert(
        1,
        {
            "id": "s1b",
            "type": "ITEMS",
            "items": [{"quantity": "", "description": "FRIES", "total": "3.50"}],
            "totalLines": [],
            "bottomDivider": False,
        },
    )
    labels = label_template(ReceiptTemplate.model_validate(payload))

    assert labels.quantity_column == "ABSENT"


def test_barcode_placement_tracks_block_position() -> None:
    payload = _template_payload()
    payload["sections"].append(
        {"id": "s4", "type": "BARCODE", "length": 12, "bottomDivider": False}
    )
    labels = label_template(ReceiptTemplate.model_validate(payload))

    assert labels.barcode_placement == "BOTTOM"
    assert (
        label_template(ReceiptTemplate.model_validate(_template_payload())).barcode_placement
        == "NONE"
    )


def test_build_taxonomy_counts_values_per_dimension() -> None:
    a = ReceiptTemplate.model_validate(_template_payload(slug="a"))
    b = ReceiptTemplate.model_validate(_template_payload(slug="b", fontType="COURIER"))
    taxonomy = build_taxonomy([label_template(a), label_template(b)])

    assert taxonomy["font_type"] == {"MERCHANT_COPY": 1, "COURIER": 1}
    assert taxonomy["layout_signature"] == {"HEADER|PAYMENT|CUSTOM": 2}


# --------------------------------------------------------------------------- #
# Filename collision safety
# --------------------------------------------------------------------------- #
def test_build_filenames_passes_through_unique_slugs() -> None:
    from document_simulator.data.receiptfaker.scrape import build_filenames

    assert build_filenames(["ALDI-Receipt", "Costco-Receipt"]) == {
        "ALDI-Receipt": "ALDI-Receipt",
        "Costco-Receipt": "Costco-Receipt",
    }


def test_build_filenames_disambiguates_case_only_collisions() -> None:
    """Case-insensitive filesystems would otherwise silently drop one member."""
    from document_simulator.data.receiptfaker.scrape import build_filenames

    names = build_filenames(["Hotel-Receipt", "Hotel-receipt", "Costco-Receipt"])

    assert names["Costco-Receipt"] == "Costco-Receipt"
    assert names["Hotel-Receipt"] != names["Hotel-receipt"]
    assert len({name.casefold() for name in names.values()}) == 3
