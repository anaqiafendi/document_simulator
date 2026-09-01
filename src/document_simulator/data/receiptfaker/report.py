"""Render a per-dimension report of the receipt template taxonomy.

For every dimension: its group count, the full list of groups, what the
dimension means and where it is visible on a receipt, the distribution across
the catalogue (absolute and percentage), and one example template per group.

Usage::

    python -m document_simulator.data.receiptfaker.report --data data/receiptfaker
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, NamedTuple

from loguru import logger

from document_simulator.data.receiptfaker.analyze import load_templates
from document_simulator.data.receiptfaker.taxonomy import DIMENSIONS, label_template


class DimensionDoc(NamedTuple):
    """Human-facing explanation of one dimension."""

    summary: str
    where: str


# Hand-authored: what each dimension captures and where a reader can see it.
DIMENSION_DOCS: dict[str, DimensionDoc] = {
    "font_type": DimensionDoc(
        "Typeface family the entire receipt body is rendered in.",
        "Everywhere. Easiest to judge on digits and capitals in the total row -- "
        "MERCHANT_COPY is the narrow dot-matrix thermal face, FAKE_RECEIPT and "
        "RECEIPTIONAL_RECEIPT are wider and rounder.",
    ),
    "merchant_block_position": DimensionDoc(
        "Vertical position of the block holding the merchant name and address.",
        "The store name, street, city and phone number. Nearly always the first "
        "block under the logo; MIDDLE means it appears after some other block.",
    ),
    "logo_placement": DimensionDoc(
        "Vertical position of the brand logo image, or its absence.",
        "The graphic at the very top of most receipts. BOTTOM puts it below the "
        "totals, near the thank-you message.",
    ),
    "divider_style": DimensionDoc(
        "Dominant separator character drawn between stacked blocks.",
        "The horizontal rules splitting header from items from totals. EMPTY is a "
        "blank line rather than a drawn rule; NONE means blocks abut directly.",
    ),
    "total_divider_style": DimensionDoc(
        "Separator drawn immediately above the grand-total row.",
        "The rule between the last line item (or tax row) and the TOTAL line.",
    ),
    "total_emphasis": DimensionDoc(
        "Font-size increase applied to the grand-total row relative to body text.",
        "The TOTAL line. PERCENT_50 renders it half again as large; NONE keeps it "
        "the same size as the line items above it.",
    ),
    "layout_signature": DimensionDoc(
        "The ordered sequence of block types -- the layout itself.",
        "Read top to bottom down the receipt. HEADER|ITEMS|CUSTOM is logo and "
        "address, then the purchase table, then a footer message.",
    ),
    "money_row_order": DimensionDoc(
        "Order in which semantic money rows appear across the whole receipt.",
        "The arithmetic column. ITEM>SUBTOTAL>TAX>TOTAL>TENDER>CHANGE is the "
        "classic supermarket order; NONE means the receipt shows no priced rows.",
    ),
    "quantity_column": DimensionDoc(
        "Whether line items render a leading quantity column.",
        "The left edge of the item table -- a '2' before the product name. "
        "NO_ITEMS covers receipts with no itemised purchase table at all.",
    ),
    "barcode_placement": DimensionDoc(
        "Vertical position of the barcode block, or its absence.",
        "The scannable stripe, usually near the foot of the receipt below the "
        "totals and above or below the thank-you message.",
    ),
    "number_format": DimensionDoc(
        "Horizontal alignment of the amount column.",
        "The price column on the right. LEFT ragged-aligns the amounts; RIGHT and "
        "RIGHT_SPACE align them flush so decimal points line up.",
    ),
    "background_type": DimensionDoc(
        "Paper texture composited behind the rendered text.",
        "The substrate itself -- crumple pattern, shadowing and creases. Purely a "
        "photorealism treatment; it does not move any content.",
    ),
    "header_alignment": DimensionDoc(
        "Text alignment inside the header block.",
        "The merchant name and address lines. CENTER is the thermal-printer norm; "
        "LEFT reads more like an invoice.",
    ),
    "section_count": DimensionDoc(
        "Number of stacked blocks making up the receipt.",
        "A proxy for overall complexity and length -- count the visually distinct "
        "bands from logo to footer.",
    ),
}


TEMPLATE_URL = "https://www.receiptfaker.com/generate/{slug}"


def _md_cell(value: object) -> str:
    """Escape a value for use inside a Markdown table cell.

    Pipes end a cell even inside backticks, and ``layout_signature`` values are
    pipe-joined block sequences.
    """
    return str(value).replace("|", "\\|")


def _example_link(slug: str) -> str:
    """Markdown link to the live template page."""
    return f"[{slug}]({TEMPLATE_URL.format(slug=slug)})"


def _example_for(slugs: list[str]) -> str:
    """Pick a readable representative slug for a group (shortest, then alphabetical)."""
    return sorted(slugs, key=lambda slug: (len(slug), slug))[0]


def build_report(data_dir: Path) -> dict[str, Any]:
    """Assemble the per-dimension report structure."""
    templates = load_templates(data_dir)
    labels = [label_template(template) for template in templates]
    total = len(labels)

    report: dict[str, Any] = {"template_count": total, "dimension_count": len(DIMENSIONS), "dimensions": {}}

    for dimension in DIMENSIONS:
        members: dict[str, list[str]] = defaultdict(list)
        for label in labels:
            members[str(getattr(label, dimension))].append(label.slug)

        counts = Counter({value: len(slugs) for value, slugs in members.items()})
        doc = DIMENSION_DOCS[dimension]
        report["dimensions"][dimension] = {
            "summary": doc.summary,
            "where_to_see_it": doc.where,
            "group_count": len(members),
            "groups": [
                {
                    "value": value,
                    "count": count,
                    "share": count / total,
                    "example": _example_for(members[value]),
                }
                for value, count in counts.most_common()
            ],
        }
    return report


def render_markdown(report: dict[str, Any]) -> str:
    """Render the report as a standalone Markdown document."""
    total = report["template_count"]
    lines: list[str] = [
        "# ReceiptFaker template taxonomy — per-dimension report",
        "",
        f"**{total} templates** classified across **{report['dimension_count']} dimensions**.",
        "",
        "Every dimension below is a discrete axis: each template takes exactly one "
        "value from that dimension's group list. Labels are read directly from the "
        "site's own template definitions, so they are ground truth rather than "
        "inferred from images.",
        "",
        "## Dimensions at a glance",
        "",
        "| # | Dimension | Groups | Largest group | Share |",
        "| --- | --- | ---: | --- | ---: |",
    ]
    ordered = sorted(
        report["dimensions"].items(), key=lambda kv: -kv[1]["group_count"]
    )
    for index, (dimension, info) in enumerate(ordered, start=1):
        top = info["groups"][0]
        lines.append(
            f"| {index} | `{dimension}` | {info['group_count']} | "
            f"`{_md_cell(top['value'])}` | {top['share']:.1%} |"
        )

    lines += ["", "---", ""]

    for dimension, info in ordered:
        lines += [
            f"## `{dimension}`",
            "",
            f"**{info['group_count']} groups.** {info['summary']}",
            "",
            f"*Where to see it:* {info['where_to_see_it']}",
            "",
            "| Group | Count | Share | Example template |",
            "| --- | ---: | ---: | --- |",
        ]
        for group in info["groups"]:
            lines.append(
                f"| `{_md_cell(group['value'])}` | {group['count']} | "
                f"{group['share']:.1%} | {_example_link(group['example'])} |"
            )
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    """CLI entry point for the taxonomy report."""
    parser = argparse.ArgumentParser(description="Report the ReceiptFaker taxonomy")
    parser.add_argument("--data", type=Path, default=Path("data/receiptfaker"))
    parser.add_argument("--markdown", type=Path, default=Path("docs/receiptfaker_taxonomy_report.md"))
    args = parser.parse_args()

    report = build_report(args.data)

    json_path = args.data / "taxonomy_report.json"
    json_path.write_text(json.dumps(report, indent=2))

    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.write_text(render_markdown(report))

    logger.info(f"Wrote {args.markdown} and {json_path}")


if __name__ == "__main__":
    main()
