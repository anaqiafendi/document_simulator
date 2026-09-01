"""Tests for layout specs, the hybrid prior sampler, and stratified batches."""

from __future__ import annotations

import random
from collections import Counter

import pytest

from document_simulator.synthesis.receipts.layout import (
    STYLE_FIELDS,
    BlockType,
    LayoutSpec,
    MoneyRole,
    ReceiptStyle,
    load_prior,
    sample_spec,
    stratified_specs,
)
from document_simulator.synthesis.receipts.layout.prior import _parse_blocks, _parse_money_rows


# --------------------------------------------------------------------------- #
# Spec model
# --------------------------------------------------------------------------- #
def test_spec_id_is_content_derived_and_stable() -> None:
    """AC: same layout -> same id, in any process (used to key filenames)."""
    a = LayoutSpec(blocks=(BlockType.HEADER,), money_rows=(MoneyRole.TOTAL,))
    b = LayoutSpec(blocks=(BlockType.HEADER,), money_rows=(MoneyRole.TOTAL,))
    assert a.spec_id == b.spec_id
    assert len(a.spec_id) == 12


def test_spec_id_changes_with_style() -> None:
    base = LayoutSpec(blocks=(BlockType.HEADER,), money_rows=())
    restyled = base.model_copy(update={"style": ReceiptStyle(divider_style="STARS")})
    assert base.spec_id != restyled.spec_id


def test_perturbed_is_excluded_from_spec_id() -> None:
    """Two specs that look identical must share an id regardless of provenance."""
    base = LayoutSpec(blocks=(BlockType.HEADER,), money_rows=())
    tagged = base.model_copy(update={"perturbed": ("font_type",)})
    assert base.spec_id == tagged.spec_id


# --------------------------------------------------------------------------- #
# Signature parsing
# --------------------------------------------------------------------------- #
def test_parse_blocks_maps_restaurant_to_meta() -> None:
    assert _parse_blocks("HEADER|RESTAURANT|ITEMS") == (
        BlockType.HEADER,
        BlockType.META,
        BlockType.ITEMS,
    )


def test_parse_blocks_drops_unknown_types() -> None:
    """A corpus refresh introducing a new block must not crash a running batch."""
    assert _parse_blocks("HEADER|WIDGET|ITEMS") == (BlockType.HEADER, BlockType.ITEMS)


def test_parse_money_rows_handles_none() -> None:
    assert _parse_money_rows("NONE") == ()
    assert _parse_money_rows("ITEM>TAX>TOTAL") == (
        MoneyRole.ITEM,
        MoneyRole.TAX,
        MoneyRole.TOTAL,
    )


# --------------------------------------------------------------------------- #
# Hybrid sampling
# --------------------------------------------------------------------------- #
def test_sample_spec_is_deterministic() -> None:
    """AC: same seed -> identical spec."""
    assert sample_spec(random.Random(42)).spec_id == sample_spec(random.Random(42)).spec_id


def test_sample_spec_differs_across_seeds() -> None:
    ids = {sample_spec(random.Random(s)).spec_id for s in range(20)}
    assert len(ids) > 1


@pytest.mark.parametrize("perturb", [0, 1, 2, 3])
def test_perturb_count_is_honoured(perturb: int) -> None:
    """Exactly N style axes are re-rolled -- no more, no fewer."""
    spec = sample_spec(random.Random(7), perturb=perturb)
    assert len(spec.perturbed) == perturb
    assert set(spec.perturbed) <= set(STYLE_FIELDS)


def test_zero_perturb_replays_an_observed_combination() -> None:
    """With perturb=0 the style must exist verbatim in the corpus."""
    prior = load_prior()
    spec = sample_spec(random.Random(3), perturb=0)
    observed = {
        tuple(entry["style"]) for entry in prior.joint
    }
    drawn = tuple(getattr(spec.style, field) for field in prior.style_dimensions)
    assert drawn in observed


def test_structure_is_never_perturbed() -> None:
    """Block order is replay-only; perturbing it yields impossible receipts."""
    prior = load_prior()
    index = {d: i for i, d in enumerate(prior.structural_dimensions)}

    def normalised(signature: str) -> str:
        """Apply the same block mapping the parser does, so this compares like for like."""
        return "|".join(
            "META" if name == "RESTAURANT" else name
            for name in signature.split("|")
            if name in {b.value for b in BlockType} or name == "RESTAURANT"
        )

    observed = {
        (
            entry["structure"][index["merchant_block_position"]],
            entry["structure"][index["logo_placement"]],
            normalised(str(entry["structure"][index["layout_signature"]])),
            str(entry["structure"][index["money_row_order"]]),
            entry["structure"][index["barcode_placement"]],
        )
        for entry in prior.joint
    }

    for seed in range(30):
        spec = sample_spec(random.Random(seed), perturb=3)
        key = (
            spec.merchant_block_position,
            spec.logo_placement,
            "|".join(b.value for b in spec.blocks),
            ">".join(r.value for r in spec.money_rows) or "NONE",
            spec.barcode_placement,
        )
        assert key in observed, f"seed {seed} invented structure: {key}"


# --------------------------------------------------------------------------- #
# Stratified batches
# --------------------------------------------------------------------------- #
def test_stratified_returns_exactly_n() -> None:
    assert len(stratified_specs(37, seed=1)) == 37
    assert stratified_specs(0, seed=1) == []


def test_stratified_covers_common_values_that_weighting_would_miss() -> None:
    """The point of stratifying: rare-but-real values must appear.

    Weighted sampling gives MERCHANT_COPY 92% of draws, so a plain batch of 200
    would almost never contain the other three fonts.
    """
    prior = load_prior()
    batch = stratified_specs(200, seed=42)
    for field in STYLE_FIELDS:
        expected = {
            value
            for value, count in prior.marginals[field].items()
            if count / prior.template_count >= 0.01
        }
        seen = {getattr(spec.style, field) for spec in batch}
        assert expected <= seen, f"{field}: missing {expected - seen}"


def test_stratified_is_deterministic() -> None:
    a = [s.spec_id for s in stratified_specs(50, seed=9)]
    b = [s.spec_id for s in stratified_specs(50, seed=9)]
    assert a == b


def test_stratified_batch_is_mostly_distinct() -> None:
    """Diversity is the whole objective -- a batch of near-clones is useless."""
    batch = stratified_specs(200, seed=42)
    assert len({s.spec_id for s in batch}) >= 150


def test_stratified_bulk_still_looks_like_real_receipts() -> None:
    """Coverage must not invert the distribution -- the head stays the head."""
    batch = stratified_specs(200, seed=42)
    fonts = Counter(s.style.font_type for s in batch)
    assert fonts.most_common(1)[0][0] == "MERCHANT_COPY"
