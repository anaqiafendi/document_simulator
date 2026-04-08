"""A4 invoice-style receipt template — portrait A4 format typical of hotel / airline invoices.

Layout (top to bottom):
    header        — company letterhead, invoice number, dates, billing info
    line_items    — variable 2–20 rows: description, qty, unit price, total
    subtotals     — subtotal, discount (optional field), taxes, grand total
    footer        — payment terms, contact info

Canvas width: 794px (A4 at 96dpi).
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
    display_name="Invoice Data",
    field_types=[
        FieldTypeConfig(
            field_type_id="standard",
            display_name="Standard text",
            font_family="serif",
            font_size_range=(10, 12),
            font_color="#111111",
        ),
        FieldTypeConfig(
            field_type_id="heading",
            display_name="Heading",
            font_family="serif",
            font_size_range=(14, 18),
            font_color="#000000",
            bold=True,
        ),
        FieldTypeConfig(
            field_type_id="label",
            display_name="Field label",
            font_family="sans-serif",
            font_size_range=(9, 11),
            font_color="#555555",
        ),
    ],
)

# ---------------------------------------------------------------------------
# Header section (height ~180px)
# ---------------------------------------------------------------------------

_HEADER_ZONES: list[ZoneConfig] = [
    # Company name top-left
    ZoneConfig(
        zone_id="company_name",
        label="company_name",
        box=[[40, 30], [400, 30], [400, 55], [40, 55]],
        faker_provider="company",
        respondent_id="default",
        field_type_id="heading",
    ),
    # "INVOICE" label top-right
    ZoneConfig(
        zone_id="invoice_title",
        label="invoice_title",
        box=[[550, 30], [754, 30], [754, 55], [550, 55]],
        faker_provider="custom_values",
        custom_values=["INVOICE"],
        respondent_id="default",
        field_type_id="heading",
        alignment="right",
    ),
    # Company address
    ZoneConfig(
        zone_id="company_address",
        label="company_address",
        box=[[40, 60], [350, 60], [350, 72], [40, 72]],
        faker_provider="address_single_line",
        respondent_id="default",
        field_type_id="standard",
    ),
    # Invoice number
    ZoneConfig(
        zone_id="invoice_number_label",
        label="invoice_number_label",
        box=[[550, 60], [680, 60], [680, 72], [550, 72]],
        faker_provider="custom_values",
        custom_values=["Invoice #:"],
        respondent_id="default",
        field_type_id="label",
    ),
    ZoneConfig(
        zone_id="invoice_number",
        label="invoice_number",
        box=[[685, 60], [754, 60], [754, 72], [685, 72]],
        faker_provider="number_medium",
        respondent_id="default",
        field_type_id="standard",
        alignment="right",
    ),
    # Invoice date
    ZoneConfig(
        zone_id="invoice_date_label",
        label="invoice_date_label",
        box=[[550, 76], [680, 76], [680, 88], [550, 88]],
        faker_provider="custom_values",
        custom_values=["Date:"],
        respondent_id="default",
        field_type_id="label",
    ),
    ZoneConfig(
        zone_id="invoice_date",
        label="invoice_date",
        box=[[685, 76], [754, 76], [754, 88], [685, 88]],
        faker_provider="date_written",
        respondent_id="default",
        field_type_id="standard",
        alignment="right",
    ),
    # Bill-to section
    ZoneConfig(
        zone_id="bill_to_label",
        label="bill_to_label",
        box=[[40, 100], [200, 100], [200, 112], [40, 112]],
        faker_provider="custom_values",
        custom_values=["Bill To:"],
        respondent_id="default",
        field_type_id="label",
    ),
    ZoneConfig(
        zone_id="client_name",
        label="client_name",
        box=[[40, 115], [350, 115], [350, 128], [40, 128]],
        faker_provider="full_name",
        respondent_id="default",
        field_type_id="standard",
    ),
    ZoneConfig(
        zone_id="client_address",
        label="client_address",
        box=[[40, 131], [350, 131], [350, 143], [40, 143]],
        faker_provider="address_single_line",
        respondent_id="default",
        field_type_id="standard",
    ),
    # Table header row
    ZoneConfig(
        zone_id="col_desc_header",
        label="col_desc",
        box=[[40, 160], [450, 160], [450, 173], [40, 173]],
        faker_provider="custom_values",
        custom_values=["DESCRIPTION"],
        respondent_id="default",
        field_type_id="label",
    ),
    ZoneConfig(
        zone_id="col_qty_header",
        label="col_qty",
        box=[[455, 160], [555, 160], [555, 173], [455, 173]],
        faker_provider="custom_values",
        custom_values=["QTY"],
        respondent_id="default",
        field_type_id="label",
        alignment="center",
    ),
    ZoneConfig(
        zone_id="col_unit_header",
        label="col_unit",
        box=[[560, 160], [660, 160], [660, 173], [560, 173]],
        faker_provider="custom_values",
        custom_values=["UNIT PRICE"],
        respondent_id="default",
        field_type_id="label",
        alignment="right",
    ),
    ZoneConfig(
        zone_id="col_total_header",
        label="col_total",
        box=[[665, 160], [754, 160], [754, 173], [665, 173]],
        faker_provider="custom_values",
        custom_values=["TOTAL"],
        respondent_id="default",
        field_type_id="label",
        alignment="right",
    ),
]

_header_section = StaticSection(
    section_id="header",
    zones=_HEADER_ZONES,
    top_y=0,
)

# ---------------------------------------------------------------------------
# Line items section (variable 2–20 rows)
# ---------------------------------------------------------------------------

_LINE_ITEM_ROW: list[ZoneConfig] = [
    ZoneConfig(
        zone_id="line_item_desc",
        label="item_description",
        box=[[40, 0], [450, 0], [450, 22], [40, 22]],
        faker_provider="catch_phrase",
        respondent_id="default",
        field_type_id="standard",
    ),
    ZoneConfig(
        zone_id="line_item_qty",
        label="item_qty",
        box=[[455, 0], [555, 0], [555, 22], [455, 22]],
        faker_provider="number_short",
        respondent_id="default",
        field_type_id="standard",
        alignment="center",
    ),
    ZoneConfig(
        zone_id="line_item_unit",
        label="item_unit_price",
        box=[[560, 0], [660, 0], [660, 22], [560, 22]],
        faker_provider="price_medium",
        respondent_id="default",
        field_type_id="standard",
        alignment="right",
    ),
    ZoneConfig(
        zone_id="line_item_total",
        label="item_line_total",
        box=[[665, 0], [754, 0], [754, 22], [665, 22]],
        faker_provider="price_medium",
        respondent_id="default",
        field_type_id="standard",
        alignment="right",
    ),
]

_items_section = RepeatingSection(
    section_id="line_items",
    row_template=_LINE_ITEM_ROW,
    row_height=24,
    num_rows_range=(2, 20),
    top_y=0,
)

# ---------------------------------------------------------------------------
# Subtotals section (~100px)
# ---------------------------------------------------------------------------

_SUBTOTAL_ZONES: list[ZoneConfig] = [
    ZoneConfig(
        zone_id="subtotal_label",
        label="subtotal_label",
        box=[[560, 10], [660, 10], [660, 22], [560, 22]],
        faker_provider="custom_values",
        custom_values=["Subtotal:"],
        respondent_id="default",
        field_type_id="label",
        alignment="right",
    ),
    ZoneConfig(
        zone_id="subtotal_value",
        label="subtotal",
        box=[[665, 10], [754, 10], [754, 22], [665, 22]],
        faker_provider="price_large",
        respondent_id="default",
        field_type_id="standard",
        alignment="right",
    ),
    ZoneConfig(
        zone_id="tax_label",
        label="tax_label",
        box=[[560, 28], [660, 28], [660, 40], [560, 40]],
        faker_provider="custom_values",
        custom_values=["Tax (13%):"],
        respondent_id="default",
        field_type_id="label",
        alignment="right",
    ),
    ZoneConfig(
        zone_id="tax_value",
        label="tax",
        box=[[665, 28], [754, 28], [754, 40], [665, 40]],
        faker_provider="price_medium",
        respondent_id="default",
        field_type_id="standard",
        alignment="right",
    ),
    ZoneConfig(
        zone_id="total_label",
        label="total_label",
        box=[[560, 50], [660, 50], [660, 66], [560, 66]],
        faker_provider="custom_values",
        custom_values=["TOTAL DUE:"],
        respondent_id="default",
        field_type_id="heading",
        alignment="right",
    ),
    ZoneConfig(
        zone_id="total_value",
        label="total",
        box=[[665, 50], [754, 50], [754, 66], [665, 66]],
        faker_provider="price_large",
        respondent_id="default",
        field_type_id="heading",
        alignment="right",
    ),
]

_subtotals_section = StaticSection(
    section_id="subtotals",
    zones=_SUBTOTAL_ZONES,
    top_y=0,
)

# ---------------------------------------------------------------------------
# Footer section (~60px)
# ---------------------------------------------------------------------------

_FOOTER_ZONES: list[ZoneConfig] = [
    ZoneConfig(
        zone_id="payment_terms",
        label="payment_terms",
        box=[[40, 20], [500, 20], [500, 32], [40, 32]],
        faker_provider="custom_values",
        custom_values=["Payment due within 30 days. Thank you for your business."],
        respondent_id="default",
        field_type_id="label",
    ),
    ZoneConfig(
        zone_id="contact_email",
        label="contact_email",
        box=[[40, 38], [350, 38], [350, 50], [40, 50]],
        faker_provider="email",
        respondent_id="default",
        field_type_id="label",
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

receipt_a4_template = DocumentTemplate(
    document_type="receipt",
    style_name="a4",
    sections=[
        _header_section,
        _items_section,
        _subtotals_section,
        _footer_section,
    ],
    respondents=[_respondent],
    image_width=794,
)
