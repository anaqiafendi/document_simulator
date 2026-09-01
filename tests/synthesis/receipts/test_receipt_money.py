"""Tests for the extended receipt money model and its invariants."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from document_simulator.synthesis.receipts.content import make_receipt
from document_simulator.synthesis.receipts.schema import LineItem, Receipt

ITEMS = [LineItem(sku="A", qty=2, unit_price=5.00), LineItem(sku="B", qty=1, unit_price=10.00)]


def _receipt(**overrides) -> Receipt:
    base = dict(
        merchant="DEMO", address="1 High St", items=ITEMS, tax_rate=0.10, payment_last4="1234"
    )
    return Receipt(**{**base, **overrides})


# --------------------------------------------------------------------------- #
# Backwards compatibility
# --------------------------------------------------------------------------- #
def test_v02_receipt_arithmetic_is_unchanged() -> None:
    """A receipt with no modifiers must behave exactly as it did in v0.2."""
    r = _receipt()
    assert r.subtotal == 20.00
    assert r.tax == 2.00  # 20.00 * 0.10
    assert r.total == 22.00  # subtotal + tax
    assert r.change is None


def test_existing_templates_see_empty_layout_fields() -> None:
    """The five hand-written templates read none of the new fields."""
    r = _receipt()
    assert r.sections == ()
    assert r.style is None


@pytest.mark.parametrize(
    "template", ["thermal_minimal", "restaurant_tip", "retail_multicol", "a4_invoice", "taxi_stub"]
)
def test_generated_receipts_still_balance(template: str) -> None:
    """AC: every template's generated content is arithmetically consistent."""
    r = make_receipt(seed=42, template=template)
    assert r.subtotal == round(sum(i.total for i in r.items), 2)
    assert r.total == round(r.taxable_base + r.tax, 2)


# --------------------------------------------------------------------------- #
# New modifiers
# --------------------------------------------------------------------------- #
def test_discount_reduces_the_taxable_base() -> None:
    """Tax is charged after discount, not before -- the common real-world rule."""
    r = _receipt(discount=5.00)
    assert r.taxable_base == 15.00
    assert r.tax == 1.50
    assert r.total == 16.50


def test_tip_is_added_after_tax() -> None:
    r = _receipt(tip=3.00)
    assert r.tax == 2.00  # tip is not taxed
    assert r.total == 25.00


def test_change_is_tender_minus_total() -> None:
    r = _receipt(tender=30.00)
    assert r.total == 22.00
    assert r.change == 8.00


def test_all_modifiers_compose() -> None:
    r = _receipt(discount=4.00, tip=2.00, tender=25.00)
    assert r.taxable_base == 16.00
    assert r.tax == 1.60
    assert r.total == 19.60
    assert r.change == 5.40


# --------------------------------------------------------------------------- #
# Invariants -- inconsistent arithmetic must not reach a dataset
# --------------------------------------------------------------------------- #
def test_tender_below_total_is_rejected() -> None:
    with pytest.raises(ValidationError, match="less than total"):
        _receipt(tender=1.00)


def test_discount_above_subtotal_is_rejected() -> None:
    with pytest.raises(ValidationError, match="exceeds subtotal"):
        _receipt(discount=999.00)


@pytest.mark.parametrize("field", ["discount", "tip"])
def test_negative_modifiers_are_rejected(field: str) -> None:
    with pytest.raises(ValidationError, match="must not be negative"):
        _receipt(**{field: -1.00})


def test_tender_exactly_equal_to_total_is_allowed() -> None:
    """Exact payment is normal, not an edge case to reject."""
    assert _receipt(tender=22.00).change == 0.00
