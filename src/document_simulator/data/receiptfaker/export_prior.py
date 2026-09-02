"""Distil the labelled corpus into a compact prior for the receipt synthesiser.

The synthesiser must not depend on the 35MB scraped corpus at runtime. This
module reduces it to a single JSON file (a few hundred KB) carrying everything
sampling needs:

``joint``
    Every layout/style combination actually observed, with its weight. Replaying
    these preserves real correlations -- restaurant layouts keep their tip rows,
    grocery layouts keep their barcodes.
``marginals``
    Per-dimension value weights, used to perturb individual style axes away from
    a replayed combination.
``text_banks``
    Real receipt copy mined from the corpus: footer lines, metadata labels, and
    money-row labels bucketed by semantic role. These replace the hardcoded
    filler strings (``SERVER: ALEX``, ``TABLE 12``) that currently appear on
    every single render.

Usage::

    python -m document_simulator.data.receiptfaker.export_prior
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from loguru import logger

from document_simulator.data.receiptfaker.analyze import load_templates
from document_simulator.data.receiptfaker.schema import ReceiptTemplate
from document_simulator.data.receiptfaker.taxonomy import (
    DIMENSIONS,
    _classify_role,
    label_template,
)

# Dimensions safe to perturb independently. Re-rolling one of these changes how
# a receipt looks without making it structurally impossible.
STYLE_DIMENSIONS: tuple[str, ...] = (
    "font_type",
    "divider_style",
    "total_divider_style",
    "total_emphasis",
    "number_format",
    "header_alignment",
    "background_type",
    "quantity_column",
)

# Dimensions that describe structure. Perturbing these independently produces
# nonsense (three barcodes, a total with no items), so they are replay-only.
STRUCTURAL_DIMENSIONS: tuple[str, ...] = tuple(
    dimension for dimension in DIMENSIONS if dimension not in STYLE_DIMENSIONS
)

_DIGIT_RUN = re.compile(r"\d{4,}")
_HAS_LETTERS = re.compile(r"[A-Za-z]{2,}")
_SEPARATOR_ONLY = re.compile(r"^[\W_]+$")
_CURRENCY_OR_NUMBER = re.compile(r"[£$€¥]|\d")
# A serial/code token: letters and digits interleaved, e.g. "TH66B3C1ZZ".
_SERIAL_TOKEN = re.compile(r"\b(?=\w*[A-Za-z])(?=\w*\d)\w{6,}\b")


def _is_reusable_copy(line: str) -> bool:
    """True when a line is generic receipt copy worth replaying.

    Rejects separator runs, digit runs and serial-shaped tokens. Those are
    transaction ids, store numbers and card numbers that must be *generated*
    per receipt -- replaying them would stamp the same fake serial onto every
    receipt in the dataset, which is exactly the defect this bank exists to fix.
    """
    if not (3 <= len(line) <= 60):
        return False
    if _SEPARATOR_ONLY.match(line):
        return False
    if _DIGIT_RUN.search(line) or _SERIAL_TOKEN.search(line):
        return False
    return bool(_HAS_LETTERS.search(line))


def _is_row_label(title: str) -> bool:
    """True when a payment/total row title is a reusable *label*.

    A label names a row ("Subtotal", "Change Due"); it never carries the amount.
    Titles with digits or currency symbols are value text that leaked into the
    title column, so they are rejected.
    """
    return _is_reusable_copy(title) and not _CURRENCY_OR_NUMBER.search(title)


def mine_text_banks(templates: list[ReceiptTemplate]) -> dict[str, Any]:
    """Extract reusable receipt copy, bucketed for the renderer."""
    footer: Counter[str] = Counter()
    meta_labels: Counter[str] = Counter()
    role_labels: defaultdict[str, Counter[str]] = defaultdict(Counter)

    for template in templates:
        for section in template.sections:
            if section.type == "CUSTOM" and section.custom:
                for raw in section.custom.split("\n"):
                    line = raw.strip()
                    if _is_reusable_copy(line):
                        footer[line] += 1

            for field in (*section.left_fields, *section.right_fields):
                title = field.title.strip()
                # Titles that are prices or bare numbers are mislabelled values.
                if title and not _CURRENCY_OR_NUMBER.search(title):
                    meta_labels[title] += 1

            for field in (*section.payment_fields, *section.total_lines):
                title = field.title.strip()
                if title and _is_row_label(title):
                    role = _classify_role(title)
                    # ITEM is the classifier's fallback bucket, not a row label
                    # class -- item text comes from the SKU corpora instead.
                    if role != "ITEM":
                        role_labels[role][title] += 1

    return {
        "footer": [text for text, _ in footer.most_common(1500)],
        "meta_labels": [text for text, _ in meta_labels.most_common()],
        "role_labels": {
            role: [text for text, _ in counts.most_common(40)]
            for role, counts in sorted(role_labels.items())
        },
    }


def build_prior(data_dir: Path) -> dict[str, Any]:
    """Reduce the labelled corpus to the sampling prior."""
    templates = load_templates(data_dir)
    labels = [label_template(template) for template in templates]

    # Joint: every observed combination, with the style block split out so the
    # sampler can perturb style while holding structure fixed.
    joint: Counter[tuple[Any, ...]] = Counter(
        tuple(getattr(label, dimension) for dimension in DIMENSIONS) for label in labels
    )
    # Stored positionally against source.structural_dimensions /
    # source.style_dimensions. 831 entries x 14 repeated key names is ~300KB of
    # pure overhead; parallel arrays cut the file by 4x.
    structural_index = [DIMENSIONS.index(d) for d in STRUCTURAL_DIMENSIONS]
    style_index = [DIMENSIONS.index(d) for d in STYLE_DIMENSIONS]
    joint_entries = [
        {
            "weight": weight,
            "structure": [values[i] for i in structural_index],
            "style": [values[i] for i in style_index],
        }
        for values, weight in joint.most_common()
    ]

    marginals = {
        dimension: dict(
            Counter(str(getattr(label, dimension)) for label in labels).most_common()
        )
        for dimension in DIMENSIONS
    }

    return {
        "source": {
            "corpus": "receiptfaker",
            "template_count": len(labels),
            "dimensions": list(DIMENSIONS),
            "style_dimensions": list(STYLE_DIMENSIONS),
            "structural_dimensions": list(STRUCTURAL_DIMENSIONS),
        },
        "joint": joint_entries,
        "marginals": marginals,
        "text_banks": mine_text_banks(templates),
    }


def main() -> None:
    """CLI entry point for prior export."""
    default_out = (
        Path(__file__).resolve().parents[2]
        / "synthesis"
        / "receipts"
        / "layout"
        / "taxonomy_prior.json"
    )
    parser = argparse.ArgumentParser(description="Export the receipt layout prior")
    parser.add_argument("--data", type=Path, default=Path("data/receiptfaker"))
    parser.add_argument("--out", type=Path, default=default_out)
    args = parser.parse_args()

    prior = build_prior(args.data)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    # Compact separators: this ships inside the package, so size matters more
    # than diff readability.
    args.out.write_text(json.dumps(prior, ensure_ascii=False, separators=(",", ":")))

    banks = prior["text_banks"]
    logger.info(
        f"Prior: {len(prior['joint'])} joint combos, "
        f"{len(banks['footer'])} footer lines, "
        f"{len(banks['meta_labels'])} meta labels, "
        f"{sum(len(v) for v in banks['role_labels'].values())} role labels "
        f"-> {args.out} ({args.out.stat().st_size / 1024:.0f} KB)"
    )


if __name__ == "__main__":
    main()
