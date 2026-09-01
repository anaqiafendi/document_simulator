"""Derive a categorical visual-feature taxonomy over receipt templates.

Every template is reduced to a fixed set of *dimensions*, each taking a value
from a small discrete set. Two templates sharing a dimension value are
interchangeable along that axis, so the label matrix doubles as a grouping key
for synthetic generation and as stratification metadata for train/test splits.

Dimensions
----------
``font_type``               Typeface family the site renders the receipt in.
``merchant_block_position`` Where the merchant name/address block sits.
``logo_placement``          Where the logo image sits (or ``NONE``).
``divider_style``           Dominant separator drawn between blocks.
``total_divider_style``     Separator drawn above the total row.
``total_emphasis``          Size emphasis applied to the total row.
``layout_signature``        Ordered sequence of block types (the layout itself).
``money_row_order``         Order of semantic money rows across the whole receipt.
``quantity_column``         Whether line items render a leading quantity column.
``barcode_placement``       Where the barcode block sits (or ``NONE``).
``number_format``           Alignment of numeric columns.
``background_type``         Paper/background treatment.
``header_alignment``        Text alignment of the header block.
``section_count``           Number of stacked blocks.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from document_simulator.data.receiptfaker.schema import ReceiptSection, ReceiptTemplate

Placement = Literal["TOP", "MIDDLE", "BOTTOM", "NONE"]

# Semantic roles for payment rows, matched against the row title in order.
# The first pattern that matches wins, so more specific patterns come first.
_ROLE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("CHANGE", re.compile(r"\bchange\b", re.I)),
    (
        "TENDER",
        re.compile(
            r"\b(cash|cards?|cred|credit|debit|visa|mastercard|amex|tender|paid|payment)\b", re.I
        ),
    ),
    (
        "AUTH",
        re.compile(
            r"\b(auth|approval|ref|reference|trace|batch|aid|arqc|terminal|merchant\s*id|mid|tid)\b",
            re.I,
        ),
    ),
    # SUBTOTAL must precede TOTAL: "Sub-Total" also matches the broader \btotal\b.
    ("SUBTOTAL", re.compile(r"\bsub[\s-]*total\b", re.I)),
    ("TOTAL", re.compile(r"\btotal\b", re.I)),
    ("TAX", re.compile(r"\b(tax|vat|gst|hst|pst)\b", re.I)),
    ("DISCOUNT", re.compile(r"\b(discount|coupon|savings?|promo|off)\b", re.I)),
    ("TIP", re.compile(r"\b(tip|gratuity|service\s*charge)\b", re.I)),
    (
        "META",
        re.compile(
            r"\b(host|server|cashier|table|order\s*no|order\s*#|register|store|lane|date|time|invoice|receipt\s*no|check|guests?)\b",
            re.I,
        ),
    ),
]


def _classify_role(title: str) -> str:
    """Map a payment row title to a semantic role."""
    cleaned = title.strip()
    if not cleaned:
        return "BLANK"
    for role, pattern in _ROLE_PATTERNS:
        if pattern.search(cleaned):
            return role
    return "ITEM"


def _placement(index: int | None, total: int) -> Placement:
    """Bucket a section index into a coarse vertical placement."""
    if index is None or total == 0:
        return "NONE"
    if index == 0:
        return "TOP"
    if index == total - 1:
        return "BOTTOM"
    return "MIDDLE"


def _merchant_index(sections: list[ReceiptSection]) -> int | None:
    """Index of the block carrying the merchant name/address, if any."""
    for index, section in enumerate(sections):
        if section.business_details:
            return index
    for index, section in enumerate(sections):
        if section.type == "HEADER":
            return index
    return None


def _logo_index(sections: list[ReceiptSection]) -> int | None:
    """Index of the block carrying a logo image, if any."""
    for index, section in enumerate(sections):
        if section.has_logo:
            return index
    return None


def _divider_style(sections: list[ReceiptSection]) -> str:
    """Dominant separator style actually drawn between blocks."""
    drawn = [
        section.bottom_divider_type or "UNSET" for section in sections if section.bottom_divider
    ]
    if not drawn:
        return "NONE"
    return Counter(drawn).most_common(1)[0][0]


def _money_row_order(sections: list[ReceiptSection]) -> tuple[str, ...]:
    """Order of distinct semantic money rows across the whole receipt.

    Walks every block in document order. Purchased goods live in ITEMS blocks
    (``items``), their summary rows in ``totalLines``/``total``; card and cash
    tender rows live in PAYMENT blocks; RESTAURANT blocks hold two-column
    metadata. All three contribute to one ordered role sequence.
    """
    order: list[str] = []

    def push(role: str) -> None:
        if role != "BLANK" and (not order or order[-1] != role):
            order.append(role)

    for section in sections:
        if section.items:
            push("ITEM")
        for field in section.total_lines:
            push(_classify_role(field.title))
        if section.total or section.total_text:
            push(_classify_role(section.total_text or "Total"))
        for field in section.payment_fields:
            push(_classify_role(field.title))
        for field in (*section.left_fields, *section.right_fields):
            push(_classify_role(field.title))

    # Collapse to first-appearance order so ITEM,TAX,ITEM,TAX -> ITEM,TAX.
    seen: list[str] = []
    for role in order:
        if role not in seen:
            seen.append(role)
    return tuple(seen)


def _quantity_column(sections: list[ReceiptSection]) -> str:
    """Whether any line item renders the leading quantity column."""
    has_items = any(section.items for section in sections)
    if not has_items:
        return "NO_ITEMS"
    for section in sections:
        for item in section.items:
            if item.quantity.strip():
                return "PRESENT"
    return "ABSENT"


def _total_divider_style(sections: list[ReceiptSection]) -> str:
    """Dominant separator drawn above the total row."""
    drawn = [section.total_divider_type or "UNSET" for section in sections if section.total_divider]
    if not drawn:
        return "NONE"
    return Counter(drawn).most_common(1)[0][0]


def _total_emphasis(sections: list[ReceiptSection]) -> str:
    """How strongly the total row is size-emphasised relative to body text."""
    values = [section.total_size_increased for section in sections if section.total_size_increased]
    if not values:
        return "NONE"
    return Counter(values).most_common(1)[0][0]


def _barcode_index(sections: list[ReceiptSection]) -> int | None:
    """Index of the barcode block, if any."""
    for index, section in enumerate(sections):
        if section.type == "BARCODE":
            return index
    return None


class TemplateLabels(BaseModel):
    """One template reduced to its categorical feature values."""

    model_config = ConfigDict(frozen=True)

    slug: str
    name: str

    font_type: str
    merchant_block_position: Placement
    logo_placement: Placement
    divider_style: str
    total_divider_style: str
    total_emphasis: str
    layout_signature: str
    money_row_order: str
    quantity_column: str
    barcode_placement: Placement
    number_format: str
    background_type: str
    header_alignment: str
    section_count: int

    def group_key(self, dimensions: list[str] | None = None) -> tuple[Any, ...]:
        """Hashable key for grouping templates over a subset of dimensions."""
        fields = dimensions or [
            name for name in type(self).model_fields if name not in ("slug", "name")
        ]
        return tuple(getattr(self, field) for field in fields)


def label_template(template: ReceiptTemplate) -> TemplateLabels:
    """Reduce a template to its categorical feature values."""
    sections = template.sections
    total = len(sections)
    header = next((s for s in sections if s.type == "HEADER"), None)

    return TemplateLabels(
        slug=template.slug,
        name=template.name,
        font_type=template.font_type or "UNSET",
        merchant_block_position=_placement(_merchant_index(sections), total),
        logo_placement=_placement(_logo_index(sections), total),
        divider_style=_divider_style(sections),
        total_divider_style=_total_divider_style(sections),
        total_emphasis=_total_emphasis(sections),
        layout_signature="|".join(template.section_types) or "EMPTY",
        money_row_order=">".join(_money_row_order(sections)) or "NONE",
        quantity_column=_quantity_column(sections),
        barcode_placement=_placement(_barcode_index(sections), total),
        number_format=template.number_format or "UNSET",
        background_type=template.background_type or "UNSET",
        header_alignment=(header.alignment if header and header.alignment else "UNSET"),
        section_count=total,
    )


DIMENSIONS: list[str] = [
    name for name in TemplateLabels.model_fields if name not in ("slug", "name")
]


def build_taxonomy(labels: list[TemplateLabels]) -> dict[str, dict[str, int]]:
    """Discrete value set and template count for every dimension.

    Returns a mapping of ``dimension -> {value: count}``, sorted by descending
    count so the dominant categories in each axis read off the top.
    """
    taxonomy: dict[str, dict[str, int]] = {}
    for dimension in DIMENSIONS:
        counts = Counter(str(getattr(label, dimension)) for label in labels)
        taxonomy[dimension] = dict(counts.most_common())
    return taxonomy
