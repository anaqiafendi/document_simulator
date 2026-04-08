"""TemplateRegistry — catalog of built-in document templates with default zones.

Each entry describes a document style (e.g. thermal receipt, A4 receipt) and
provides a set of default ZoneConfig objects that the React UI can pre-populate
when a template is selected.  Templates that contain repeating line-item sections
advertise a ``supports_line_items`` flag and sensible ``default_line_items_range``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TemplateStyle:
    """Metadata for one built-in template style."""

    id: str
    name: str
    description: str
    supports_line_items: bool = False
    default_line_items_range: tuple[int, int] = (3, 8)
    # Default zones returned for GET /api/synthesis/templates/{id}/zones
    default_zones: list[dict[str, Any]] = field(default_factory=list)


def _receipt_thermal_zones() -> list[dict[str, Any]]:
    """Default zones for a narrow thermal receipt (384 × 800 px at 96 dpi)."""
    return [
        {
            "zone_id": "thermal_header",
            "label": "Store name",
            "box": [[20, 20], [364, 20], [364, 55], [20, 55]],
            "respondent_id": "default",
            "field_type_id": "standard",
            "faker_provider": "company",
            "custom_values": [],
            "alignment": "center",
            "page": 0,
        },
        {
            "zone_id": "thermal_date",
            "label": "Date / time",
            "box": [[20, 65], [364, 65], [364, 90], [20, 90]],
            "respondent_id": "default",
            "field_type_id": "standard",
            "faker_provider": "date_time",
            "custom_values": [],
            "alignment": "center",
            "page": 0,
        },
        {
            "zone_id": "thermal_cashier",
            "label": "Cashier name",
            "box": [[20, 95], [364, 95], [364, 118], [20, 118]],
            "respondent_id": "default",
            "field_type_id": "standard",
            "faker_provider": "first_name",
            "custom_values": [],
            "alignment": "left",
            "page": 0,
        },
        {
            "zone_id": "thermal_total",
            "label": "Total amount",
            "box": [[20, 680], [364, 680], [364, 710], [20, 710]],
            "respondent_id": "default",
            "field_type_id": "standard",
            "faker_provider": "pricetag",
            "custom_values": [],
            "alignment": "right",
            "page": 0,
        },
        {
            "zone_id": "thermal_footer",
            "label": "Thank-you message",
            "box": [[20, 730], [364, 730], [364, 760], [20, 760]],
            "respondent_id": "default",
            "field_type_id": "standard",
            "faker_provider": "catch_phrase",
            "custom_values": [],
            "alignment": "center",
            "page": 0,
        },
    ]


def _receipt_a4_zones() -> list[dict[str, Any]]:
    """Default zones for an A4 receipt / invoice (794 × 1123 px at 96 dpi)."""
    return [
        {
            "zone_id": "a4_company",
            "label": "Company name",
            "box": [[40, 40], [400, 40], [400, 80], [40, 80]],
            "respondent_id": "default",
            "field_type_id": "standard",
            "faker_provider": "company",
            "custom_values": [],
            "alignment": "left",
            "page": 0,
        },
        {
            "zone_id": "a4_address",
            "label": "Company address",
            "box": [[40, 85], [400, 85], [400, 130], [40, 130]],
            "respondent_id": "default",
            "field_type_id": "standard",
            "faker_provider": "address",
            "custom_values": [],
            "alignment": "left",
            "page": 0,
        },
        {
            "zone_id": "a4_invoice_no",
            "label": "Invoice number",
            "box": [[500, 40], [754, 40], [754, 65], [500, 65]],
            "respondent_id": "default",
            "field_type_id": "standard",
            "faker_provider": "bothify",
            "custom_values": ["INV-####"],
            "alignment": "right",
            "page": 0,
        },
        {
            "zone_id": "a4_date",
            "label": "Invoice date",
            "box": [[500, 70], [754, 70], [754, 95], [500, 95]],
            "respondent_id": "default",
            "field_type_id": "standard",
            "faker_provider": "date",
            "custom_values": [],
            "alignment": "right",
            "page": 0,
        },
        {
            "zone_id": "a4_bill_to_name",
            "label": "Bill-to name",
            "box": [[40, 200], [380, 200], [380, 225], [40, 225]],
            "respondent_id": "default",
            "field_type_id": "standard",
            "faker_provider": "name",
            "custom_values": [],
            "alignment": "left",
            "page": 0,
        },
        {
            "zone_id": "a4_bill_to_address",
            "label": "Bill-to address",
            "box": [[40, 228], [380, 228], [380, 290], [40, 290]],
            "respondent_id": "default",
            "field_type_id": "standard",
            "faker_provider": "address",
            "custom_values": [],
            "alignment": "left",
            "page": 0,
        },
        {
            "zone_id": "a4_total",
            "label": "Total due",
            "box": [[550, 950], [754, 950], [754, 980], [550, 980]],
            "respondent_id": "default",
            "field_type_id": "standard",
            "faker_provider": "pricetag",
            "custom_values": [],
            "alignment": "right",
            "page": 0,
        },
    ]


# ── Registry ──────────────────────────────────────────────────────────────────

_REGISTRY: dict[str, TemplateStyle] = {
    "receipt_thermal": TemplateStyle(
        id="receipt_thermal",
        name="Thermal Receipt",
        description="Narrow thermal paper receipt (80 mm / 384 px wide) with header, line items, and total.",
        supports_line_items=True,
        default_line_items_range=(3, 10),
        default_zones=_receipt_thermal_zones(),
    ),
    "receipt_a4": TemplateStyle(
        id="receipt_a4",
        name="A4 Invoice / Receipt",
        description="Full-page A4 invoice with company header, bill-to section, line-item table, and totals.",
        supports_line_items=True,
        default_line_items_range=(3, 8),
        default_zones=_receipt_a4_zones(),
    ),
}


class TemplateRegistry:
    """Read-only catalog of built-in document template styles."""

    @classmethod
    def list_all(cls) -> list[TemplateStyle]:
        """Return all registered template styles."""
        return list(_REGISTRY.values())

    @classmethod
    def get(cls, template_id: str) -> TemplateStyle | None:
        """Return the TemplateStyle for *template_id*, or None if not found."""
        return _REGISTRY.get(template_id)

    @classmethod
    def get_zones(cls, template_id: str) -> list[dict]:
        """Return the default zones for *template_id*.

        Returns an empty list if the template is not found.
        """
        style = _REGISTRY.get(template_id)
        return style.default_zones if style else []
