"""Tests for the distilled layout prior exported to the synthesiser."""

from __future__ import annotations

import json
from pathlib import Path

from document_simulator.data.receiptfaker.export_prior import (
    STRUCTURAL_DIMENSIONS,
    STYLE_DIMENSIONS,
    _is_reusable_copy,
    _is_row_label,
    mine_text_banks,
)
from document_simulator.data.receiptfaker.schema import ReceiptTemplate
from document_simulator.data.receiptfaker.taxonomy import DIMENSIONS

PRIOR_PATH = (
    Path(__file__).resolve().parents[2]
    / "src/document_simulator/synthesis/receipts/layout/taxonomy_prior.json"
)


def test_style_and_structural_dimensions_partition_all_dimensions() -> None:
    """Every dimension is either perturbable or replay-only, never both."""
    assert set(STYLE_DIMENSIONS) | set(STRUCTURAL_DIMENSIONS) == set(DIMENSIONS)
    assert not set(STYLE_DIMENSIONS) & set(STRUCTURAL_DIMENSIONS)


def test_reusable_copy_rejects_volatile_text() -> None:
    """Ids and serials must be generated per receipt, never replayed."""
    assert _is_reusable_copy("THANK YOU")
    assert _is_reusable_copy("Have a nice day")
    assert not _is_reusable_copy("------------------------")
    assert not _is_reusable_copy("TC# 4891 4435 7070 5637")  # digit run
    assert not _is_reusable_copy("PRODUCT SERIAL # TH66B3C1ZZ")  # serial token
    assert not _is_reusable_copy("ab")  # too short


def test_row_label_rejects_embedded_amounts() -> None:
    """A row label names the row; it never carries the amount."""
    assert _is_row_label("Subtotal")
    assert _is_row_label("Change Due")
    assert not _is_row_label("E-$5 Off $20")
    assert not _is_row_label("20% off Coupon Code")


def test_mine_text_banks_buckets_by_role_and_drops_item_fallback() -> None:
    template = ReceiptTemplate.model_validate(
        {
            "id": "x",
            "slug": "Demo",
            "name": "Demo",
            "published": True,
            "sections": [
                {"id": "s1", "type": "CUSTOM", "custom": "THANK YOU\n----\nORDER 99812345"},
                {
                    "id": "s2",
                    "type": "ITEMS",
                    "items": [{"quantity": "1", "description": "FRIES", "total": "3.50"}],
                    "totalLines": [
                        {"title": "Subtotal", "value": "3.50"},
                        {"title": "Change Due", "value": "1.50"},
                        {"title": "WIDGET DELUXE", "value": "3.50"},
                    ],
                },
                {"id": "s3", "type": "RESTAURANT", "leftFields": [{"title": "Table", "value": "4"}]},
            ],
        }
    )

    banks = mine_text_banks([template])

    assert banks["footer"] == ["THANK YOU"]  # separator and order id dropped
    assert banks["meta_labels"] == ["Table"]
    assert banks["role_labels"]["SUBTOTAL"] == ["Subtotal"]
    assert banks["role_labels"]["CHANGE"] == ["Change Due"]
    assert "ITEM" not in banks["role_labels"]  # classifier fallback is not a label class


def test_exported_prior_is_well_formed() -> None:
    """The shipped prior must load and match the declared dimension order."""
    prior = json.loads(PRIOR_PATH.read_text())

    assert prior["source"]["template_count"] > 0
    assert prior["source"]["style_dimensions"] == list(STYLE_DIMENSIONS)
    assert prior["source"]["structural_dimensions"] == list(STRUCTURAL_DIMENSIONS)

    # Joint entries are positional -- arity must match the declared order or the
    # sampler will silently read the wrong dimension.
    for entry in prior["joint"]:
        assert len(entry["structure"]) == len(STRUCTURAL_DIMENSIONS)
        assert len(entry["style"]) == len(STYLE_DIMENSIONS)

    assert sum(e["weight"] for e in prior["joint"]) == prior["source"]["template_count"]
    assert set(prior["marginals"]) == set(DIMENSIONS)


def test_prior_role_labels_carry_no_amounts() -> None:
    """Regression: labels with embedded prices leaked into the bank once."""
    prior = json.loads(PRIOR_PATH.read_text())
    for role, labels in prior["text_banks"]["role_labels"].items():
        for label in labels:
            assert not any(c.isdigit() for c in label), f"{role}: {label!r}"
