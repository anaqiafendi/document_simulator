"""Unit tests for the Faker-driven `make_receipt` content factory.

Covers FDD #28 AC-1: Faker determinism, arithmetic consistency, locale-aware
tax rates, and template-driven content variation.
"""

from __future__ import annotations

import pytest

from document_simulator.synthesis.receipts.content import make_receipt
from document_simulator.synthesis.receipts.schema import Receipt

# Templates exercised in tests. The taxi template is intentionally short and
# may carry zero tax in some locales (rideshare fares are often inclusive),
# so it is excluded from the locale tax assertion below.
_ALL_TEMPLATES = (
    "thermal_minimal",
    "restaurant_tip",
    "retail_multicol",
    "a4_invoice",
    "taxi_stub",
)


def test_make_receipt_seeded_determinism() -> None:
    """AC-1: same (seed, template) -> identical Receipt model."""
    seed = 42
    template = "thermal_minimal"
    a = make_receipt(seed=seed, template=template)
    b = make_receipt(seed=seed, template=template)

    assert isinstance(a, Receipt)
    # model_dump() captures every field including computed totals.
    assert a.model_dump() == b.model_dump(), "Same seed must yield identical Receipts"


def test_make_receipt_arithmetic_consistent() -> None:
    """AC-1: subtotal == sum(items.total); tax == round(subtotal * tax_rate, 2);
    total == subtotal + tax. True for every template.
    """
    for template in _ALL_TEMPLATES:
        receipt = make_receipt(seed=7, template=template)

        expected_subtotal = round(sum(item.total for item in receipt.items), 2)
        assert (
            receipt.subtotal == expected_subtotal
        ), f"{template}: subtotal mismatch ({receipt.subtotal} vs {expected_subtotal})"

        expected_tax = round(receipt.subtotal * receipt.tax_rate, 2)
        assert (
            receipt.tax == expected_tax
        ), f"{template}: tax mismatch ({receipt.tax} vs {expected_tax})"

        expected_total = round(receipt.subtotal + receipt.tax, 2)
        assert (
            receipt.total == expected_total
        ), f"{template}: total mismatch ({receipt.total} vs {expected_total})"

        # Sanity: every receipt has at least one line item.
        assert len(receipt.items) >= 1, f"{template}: no line items"


def test_make_receipt_different_templates_differ() -> None:
    """AC-1: same seed across different templates yields visibly different content.

    We assert that at least two templates produce different (merchant, items)
    tuples — because each template draws from its own SKU corpus / persona.
    """
    seed = 99
    receipts = {tpl: make_receipt(seed=seed, template=tpl) for tpl in _ALL_TEMPLATES}

    signatures = {
        tpl: (r.merchant, tuple((it.sku, it.qty) for it in r.items)) for tpl, r in receipts.items()
    }
    distinct = set(signatures.values())
    assert len(distinct) >= 2, (
        f"Expected templates to produce varied content, got {len(distinct)} unique "
        f"signatures across {len(_ALL_TEMPLATES)} templates"
    )


def test_make_receipt_locale_aware_tax_rate() -> None:
    """AC-1: tax_rate falls in a sensible range for retail-class templates.

    Retail/restaurant/invoice tax rates in the US sit roughly between 0% and
    25%; UK VAT is 20%. We assert 0.0 <= tax_rate <= 0.25 for templates with
    explicit tax lines.

    The taxi stub is exempt — fares may be inclusive of tax (tax_rate=0.0 OK).
    """
    taxed_templates = ("thermal_minimal", "restaurant_tip", "retail_multicol", "a4_invoice")
    for template in taxed_templates:
        receipt = make_receipt(seed=11, template=template)
        assert (
            0.0 <= receipt.tax_rate <= 0.25
        ), f"{template}: tax_rate={receipt.tax_rate} out of [0, 0.25] range"


def test_make_receipt_unknown_template_raises() -> None:
    """Defensive: an unknown template name should raise ValueError, not silently
    fall back. Keeps the API contract honest.
    """
    with pytest.raises(ValueError):
        make_receipt(seed=1, template="this_template_does_not_exist")
