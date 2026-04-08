"""Thermal receipt template — 58mm-wide format typical of fast-food / transit receipts.

Layout (top to bottom):
    header      — merchant name, address, date/time, order number
    line_items  — variable 2–12 rows: item name + unit price + qty + line total
    subtotals   — subtotal, tax, total
    footer      — thank-you message, loyalty ID

Canvas width: 220px (≈58mm at 96dpi).
"""

from __future__ import annotations

from document_simulator.synthesis.document_template import DocumentTemplate
from document_simulator.synthesis.sections import RepeatingSection, StaticSection
from document_simulator.synthesis.zones import (
    FieldTypeConfig,
    GeneratorConfig,
    RespondentConfig,
    ZoneConfig,
)

# ---------------------------------------------------------------------------
# Respondent
# ---------------------------------------------------------------------------

_respondent = RespondentConfig(
    respondent_id="default",
    display_name="Receipt Data",
    field_types=[
        FieldTypeConfig(
            field_type_id="standard",
            display_name="Standard text",
            font_family="monospace",
            font_size_range=(9, 11),
            font_color="#000000",
        ),
        FieldTypeConfig(
            field_type_id="header",
            display_name="Header text",
            font_family="monospace",
            font_size_range=(11, 13),
            font_color="#000000",
            bold=True,
        ),
    ],
)

# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------

# --- Header section (top_y=0, height=110) ---
_HEADER_ZONES: list[ZoneConfig] = [
    ZoneConfig(
        zone_id="merchant_name",
        label="merchant_name",
        box=[[5, 5], [215, 5], [215, 20], [5, 20]],
        faker_provider="company",
        respondent_id="default",
        field_type_id="header",
        alignment="center",
    ),
    ZoneConfig(
        zone_id="merchant_address",
        label="merchant_address",
        box=[[5, 22], [215, 22], [215, 34], [5, 34]],
        faker_provider="address_single_line",
        respondent_id="default",
        field_type_id="standard",
        alignment="center",
    ),
    ZoneConfig(
        zone_id="receipt_date",
        label="date",
        box=[[5, 38], [110, 38], [110, 50], [5, 50]],
        faker_provider="date_numeric",
        respondent_id="default",
        field_type_id="standard",
    ),
    ZoneConfig(
        zone_id="receipt_time",
        label="time",
        box=[[115, 38], [215, 38], [215, 50], [115, 50]],
        faker_provider="time",
        respondent_id="default",
        field_type_id="standard",
        alignment="right",
    ),
    ZoneConfig(
        zone_id="order_number",
        label="order_number",
        box=[[5, 54], [215, 54], [215, 66], [5, 66]],
        faker_provider="number_short",
        respondent_id="default",
        field_type_id="standard",
    ),
    ZoneConfig(
        zone_id="header_divider",
        label="divider",
        box=[[5, 70], [215, 70], [215, 72], [5, 72]],
        faker_provider="custom_values",
        custom_values=["------------------------"],
        respondent_id="default",
        field_type_id="standard",
        alignment="center",
    ),
    ZoneConfig(
        zone_id="col_header_item",
        label="col_item",
        box=[[5, 74], [130, 74], [130, 86], [5, 86]],
        faker_provider="custom_values",
        custom_values=["ITEM"],
        respondent_id="default",
        field_type_id="standard",
    ),
    ZoneConfig(
        zone_id="col_header_price",
        label="col_price",
        box=[[135, 74], [215, 74], [215, 86], [135, 86]],
        faker_provider="custom_values",
        custom_values=["PRICE"],
        respondent_id="default",
        field_type_id="standard",
        alignment="right",
    ),
    ZoneConfig(
        zone_id="col_divider",
        label="col_divider",
        box=[[5, 88], [215, 88], [215, 90], [5, 90]],
        faker_provider="custom_values",
        custom_values=["------------------------"],
        respondent_id="default",
        field_type_id="standard",
        alignment="center",
    ),
]

_header_section = StaticSection(
    section_id="header",
    zones=_HEADER_ZONES,
    top_y=0,
)

# --- Line items section (variable, 2–12 rows) ---
_LINE_ITEM_ROW_TEMPLATE: list[ZoneConfig] = [
    ZoneConfig(
        zone_id="line_item_name",
        label="item_name",
        box=[[5, 0], [130, 0], [130, 18], [5, 18]],
        faker_provider="word",
        respondent_id="default",
        field_type_id="standard",
    ),
    ZoneConfig(
        zone_id="line_item_price",
        label="item_price",
        box=[[135, 0], [215, 0], [215, 18], [135, 18]],
        faker_provider="price_short",
        respondent_id="default",
        field_type_id="standard",
        alignment="right",
    ),
]

_items_section = RepeatingSection(
    section_id="line_items",
    row_template=_LINE_ITEM_ROW_TEMPLATE,
    row_height=20,
    num_rows_range=(2, 12),
    top_y=0,  # stacked by DocumentTemplate
)

# --- Subtotals section ---
_SUBTOTAL_ZONES: list[ZoneConfig] = [
    ZoneConfig(
        zone_id="subtotal_divider",
        label="divider",
        box=[[5, 0], [215, 0], [215, 2], [5, 2]],
        faker_provider="custom_values",
        custom_values=["------------------------"],
        respondent_id="default",
        field_type_id="standard",
        alignment="center",
    ),
    ZoneConfig(
        zone_id="subtotal_label",
        label="subtotal_label",
        box=[[5, 5], [130, 5], [130, 17], [5, 17]],
        faker_provider="custom_values",
        custom_values=["Subtotal"],
        respondent_id="default",
        field_type_id="standard",
    ),
    ZoneConfig(
        zone_id="subtotal_amount",
        label="subtotal_amount",
        box=[[135, 5], [215, 5], [215, 17], [135, 17]],
        faker_provider="price_medium",
        respondent_id="default",
        field_type_id="standard",
        alignment="right",
    ),
    ZoneConfig(
        zone_id="tax_label",
        label="tax_label",
        box=[[5, 20], [130, 20], [130, 32], [5, 32]],
        faker_provider="custom_values",
        custom_values=["Tax (HST 13%)"],
        respondent_id="default",
        field_type_id="standard",
    ),
    ZoneConfig(
        zone_id="tax_amount",
        label="tax_amount",
        box=[[135, 20], [215, 20], [215, 32], [135, 32]],
        faker_provider="price_short",
        respondent_id="default",
        field_type_id="standard",
        alignment="right",
    ),
    ZoneConfig(
        zone_id="total_divider",
        label="total_divider",
        box=[[5, 35], [215, 35], [215, 37], [5, 37]],
        faker_provider="custom_values",
        custom_values=["========================"],
        respondent_id="default",
        field_type_id="standard",
        alignment="center",
    ),
    ZoneConfig(
        zone_id="total_label",
        label="total_label",
        box=[[5, 40], [130, 40], [130, 54], [5, 54]],
        faker_provider="custom_values",
        custom_values=["TOTAL"],
        respondent_id="default",
        field_type_id="header",
    ),
    ZoneConfig(
        zone_id="total_amount",
        label="total_amount",
        box=[[135, 40], [215, 40], [215, 54], [135, 54]],
        faker_provider="price_medium",
        respondent_id="default",
        field_type_id="header",
        alignment="right",
    ),
]

_subtotals_section = StaticSection(
    section_id="subtotals",
    zones=_SUBTOTAL_ZONES,
    top_y=0,
)

# --- Footer section ---
_FOOTER_ZONES: list[ZoneConfig] = [
    ZoneConfig(
        zone_id="footer_divider",
        label="footer_divider",
        box=[[5, 0], [215, 0], [215, 2], [5, 2]],
        faker_provider="custom_values",
        custom_values=["------------------------"],
        respondent_id="default",
        field_type_id="standard",
        alignment="center",
    ),
    ZoneConfig(
        zone_id="footer_message",
        label="footer_message",
        box=[[5, 5], [215, 5], [215, 17], [5, 17]],
        faker_provider="custom_values",
        custom_values=["Thank you for your purchase!"],
        respondent_id="default",
        field_type_id="standard",
        alignment="center",
    ),
    ZoneConfig(
        zone_id="loyalty_id",
        label="loyalty_id",
        box=[[5, 20], [215, 20], [215, 32], [5, 32]],
        faker_provider="number_long",
        respondent_id="default",
        field_type_id="standard",
        alignment="center",
    ),
]

_footer_section = StaticSection(
    section_id="footer",
    zones=_FOOTER_ZONES,
    top_y=0,
)

# ---------------------------------------------------------------------------
# Assembled template
# ---------------------------------------------------------------------------

receipt_thermal_template = DocumentTemplate(
    document_type="receipt",
    style_name="thermal",
    sections=[
        _header_section,
        _items_section,
        _subtotals_section,
        _footer_section,
    ],
    respondents=[_respondent],
    image_width=220,
)
