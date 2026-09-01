"""Load the distilled taxonomy prior and sample layout specs from it.

Sampling is *hybrid*: replay a whole layout/style combination observed in the
corpus, then re-roll a small number of style axes from their marginals. Replay
alone caps variety at the 831 observed combinations and over-represents the head
of the distribution; independent per-dimension sampling reaches far more
combinations but destroys the correlations that make a receipt plausible (it
would put restaurant tip rows on a taxi stub). Perturbing only the style axes
of a real skeleton keeps the structure honest while reaching combinations the
corpus never contained.
"""

from __future__ import annotations

import json
import random
from functools import cache
from pathlib import Path
from typing import Any, NamedTuple

from document_simulator.synthesis.receipts.layout.spec import (
    STYLE_FIELDS,
    BlockType,
    LayoutSpec,
    MoneyRole,
    ReceiptStyle,
)

PRIOR_PATH = Path(__file__).parent / "taxonomy_prior.json"


class Prior(NamedTuple):
    """The distilled corpus statistics used for sampling."""

    joint: list[dict[str, Any]]
    marginals: dict[str, dict[str, int]]
    text_banks: dict[str, Any]
    structural_dimensions: tuple[str, ...]
    style_dimensions: tuple[str, ...]
    template_count: int

    def labels_for(self, role: MoneyRole | str) -> list[str]:
        """Observed row labels for a money role, empty when none were mined."""
        key = role.value if isinstance(role, MoneyRole) else role
        banks: dict[str, list[str]] = self.text_banks.get("role_labels", {})
        return banks.get(key, [])


@cache
def load_prior(path: Path | None = None) -> Prior:
    """Load and cache the prior shipped with the package."""
    payload = json.loads((path or PRIOR_PATH).read_text())
    source = payload["source"]
    return Prior(
        joint=payload["joint"],
        marginals=payload["marginals"],
        text_banks=payload["text_banks"],
        structural_dimensions=tuple(source["structural_dimensions"]),
        style_dimensions=tuple(source["style_dimensions"]),
        template_count=source["template_count"],
    )


def _parse_blocks(layout_signature: str) -> tuple[BlockType, ...]:
    """Turn a pipe-joined layout signature into block types.

    ``RESTAURANT`` maps to ``META``; unrecognised names are dropped rather than
    raising, so a corpus refresh that introduces a new block type degrades to a
    slightly shorter receipt instead of crashing a batch mid-run.
    """
    blocks: list[BlockType] = []
    for name in layout_signature.split("|"):
        candidate = "META" if name == "RESTAURANT" else name
        try:
            blocks.append(BlockType(candidate))
        except ValueError:
            continue
    return tuple(blocks)


def _parse_money_rows(money_row_order: str) -> tuple[MoneyRole, ...]:
    """Turn a ``>``-joined role sequence into money roles."""
    if money_row_order in ("NONE", ""):
        return ()
    rows: list[MoneyRole] = []
    for name in money_row_order.split(">"):
        try:
            rows.append(MoneyRole(name))
        except ValueError:
            continue
    return tuple(rows)


def _weighted_choice(rng: random.Random, weights: dict[str, int]) -> str:
    """Pick a key with probability proportional to its weight."""
    keys = sorted(weights)  # sorted for determinism across runs
    return rng.choices(keys, weights=[weights[k] for k in keys], k=1)[0]


def sample_spec(rng: random.Random, *, perturb: int = 2, prior: Prior | None = None) -> LayoutSpec:
    """Draw one layout spec: replay an observed combination, then perturb style.

    Args:
        rng: Seeded RNG. Same seed sequence -> same specs.
        perturb: How many style axes to re-roll. 0 replays the observed
            combination verbatim.
        prior: Override the shipped prior (used by tests).

    Returns:
        A LayoutSpec whose structure is real and whose styling may be novel.
    """
    prior = prior or load_prior()

    entry = rng.choices(prior.joint, weights=[e["weight"] for e in prior.joint], k=1)[0]
    structure = dict(zip(prior.structural_dimensions, entry["structure"], strict=True))
    style_values = dict(zip(prior.style_dimensions, entry["style"], strict=True))

    perturbable = [field for field in STYLE_FIELDS if field in prior.marginals]
    chosen = rng.sample(perturbable, k=min(perturb, len(perturbable))) if perturb else []
    for field in chosen:
        style_values[field] = _weighted_choice(rng, prior.marginals[field])

    return LayoutSpec(
        blocks=_parse_blocks(str(structure["layout_signature"])),
        money_rows=_parse_money_rows(str(structure["money_row_order"])),
        style=ReceiptStyle(**{k: v for k, v in style_values.items() if k in STYLE_FIELDS}),
        merchant_block_position=str(structure["merchant_block_position"]),
        logo_placement=str(structure["logo_placement"]),
        barcode_placement=str(structure["barcode_placement"]),
        perturbed=tuple(sorted(chosen)),
    )
