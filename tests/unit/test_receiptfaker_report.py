"""Tests for the per-dimension taxonomy report."""

from __future__ import annotations

from document_simulator.data.receiptfaker.report import (
    DIMENSION_DOCS,
    _example_for,
    _md_cell,
    render_markdown,
)
from document_simulator.data.receiptfaker.taxonomy import DIMENSIONS


def test_every_dimension_is_documented() -> None:
    """A new dimension must not silently ship without a description."""
    assert set(DIMENSION_DOCS) == set(DIMENSIONS)


def test_docs_are_non_empty() -> None:
    for dimension, doc in DIMENSION_DOCS.items():
        assert doc.summary.strip(), dimension
        assert doc.where.strip(), dimension


def test_md_cell_escapes_pipes() -> None:
    """layout_signature values are pipe-joined and would otherwise split cells."""
    assert _md_cell("HEADER|ITEMS|CUSTOM") == r"HEADER\|ITEMS\|CUSTOM"


def test_example_prefers_shortest_slug() -> None:
    slugs = ["Aldi-Receipt-example-with-many-items", "ALDI-Receipt", "Costco-Receipt"]
    assert _example_for(slugs) == "ALDI-Receipt"


def test_example_is_deterministic_for_equal_lengths() -> None:
    assert _example_for(["B-Receipt", "A-Receipt"]) == "A-Receipt"


def test_render_markdown_covers_all_groups() -> None:
    report = {
        "template_count": 3,
        "dimension_count": 1,
        "dimensions": {
            "font_type": {
                "summary": "Typeface family.",
                "where_to_see_it": "Everywhere.",
                "group_count": 2,
                "groups": [
                    {"value": "MERCHANT_COPY", "count": 2, "share": 2 / 3, "example": "A-Receipt"},
                    {"value": "FAKE_RECEIPT", "count": 1, "share": 1 / 3, "example": "B-Receipt"},
                ],
            }
        },
    }

    markdown = render_markdown(report)

    assert "**3 templates**" in markdown
    assert "**2 groups.** Typeface family." in markdown
    assert "MERCHANT_COPY" in markdown and "FAKE_RECEIPT" in markdown
    assert "66.7%" in markdown and "33.3%" in markdown
    assert "https://www.receiptfaker.com/generate/A-Receipt" in markdown
