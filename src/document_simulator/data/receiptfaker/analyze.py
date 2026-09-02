"""Label the scraped catalogue and report its visual-feature taxonomy.

Usage::

    python -m document_simulator.data.receiptfaker.analyze --data data/receiptfaker
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import pandas as pd
from loguru import logger
from pydantic import ValidationError
from rich.console import Console
from rich.table import Table

from document_simulator.data.receiptfaker.schema import ReceiptTemplate
from document_simulator.data.receiptfaker.taxonomy import (
    DIMENSIONS,
    TemplateLabels,
    build_taxonomy,
    label_template,
)


def load_templates(data_dir: Path) -> list[ReceiptTemplate]:
    """Parse every scraped template JSON under ``data_dir/templates``."""
    templates: list[ReceiptTemplate] = []
    paths = sorted((data_dir / "templates").glob("*.json"))
    for path in paths:
        try:
            templates.append(ReceiptTemplate.model_validate_json(path.read_text()))
        except ValidationError as exc:
            logger.warning(f"Skipping {path.name}: {exc.error_count()} validation errors")
    logger.info(f"Loaded {len(templates)}/{len(paths)} templates from {data_dir}")
    return templates


def render_taxonomy(taxonomy: dict[str, dict[str, int]], total: int, top_n: int = 12) -> None:
    """Print the discrete category set of each dimension."""
    console = Console()
    for dimension, counts in taxonomy.items():
        table = Table(
            title=f"{dimension}  ({len(counts)} distinct values)",
            title_justify="left",
            header_style="bold",
        )
        table.add_column("value", overflow="fold", max_width=60)
        table.add_column("count", justify="right")
        table.add_column("share", justify="right")
        for value, count in list(counts.items())[:top_n]:
            table.add_row(value, str(count), f"{count / total:.1%}")
        if len(counts) > top_n:
            tail = sum(list(counts.values())[top_n:])
            table.add_row(f"… {len(counts) - top_n} more", str(tail), f"{tail / total:.1%}")
        console.print(table)
        console.print()


def build_cluster_index(labels: list[TemplateLabels]) -> dict[str, list[str]]:
    """Group template slugs by their full label tuple (identical on every axis)."""
    groups: dict[tuple, list[str]] = defaultdict(list)
    for label in labels:
        groups[label.group_key()].append(label.slug)
    return {
        "::".join(str(part) for part in key): sorted(slugs)
        for key, slugs in sorted(groups.items(), key=lambda kv: -len(kv[1]))
    }


def main() -> None:
    """CLI entry point for taxonomy analysis."""
    parser = argparse.ArgumentParser(description="Analyse ReceiptFaker template features")
    parser.add_argument("--data", type=Path, default=Path("data/receiptfaker"))
    parser.add_argument("--top-n", type=int, default=12)
    args = parser.parse_args()

    templates = load_templates(args.data)
    if not templates:
        raise SystemExit(f"No templates found under {args.data / 'templates'}")

    labels = [label_template(template) for template in templates]
    taxonomy = build_taxonomy(labels)

    frame = pd.DataFrame([label.model_dump() for label in labels])
    labels_path = args.data / "labels.csv"
    frame.to_csv(labels_path, index=False)

    taxonomy_path = args.data / "taxonomy.json"
    taxonomy_path.write_text(json.dumps(taxonomy, indent=2))

    clusters = build_cluster_index(labels)
    clusters_path = args.data / "clusters.json"
    clusters_path.write_text(json.dumps(clusters, indent=2))

    render_taxonomy(taxonomy, total=len(labels), top_n=args.top_n)

    console = Console()
    console.print(
        f"[bold]{len(labels)}[/bold] templates labelled across {len(DIMENSIONS)} dimensions"
    )
    console.print(f"[bold]{len(clusters)}[/bold] exact-match groups (identical on every dimension)")
    console.print(f"wrote {labels_path}, {taxonomy_path}, {clusters_path}")


if __name__ == "__main__":
    main()
