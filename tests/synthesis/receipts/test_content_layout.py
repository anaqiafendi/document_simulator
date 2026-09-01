"""Tests for spec-driven content generation (FDD #28 AC-4: layout stage).

Covers the widened ``make_receipt(seed, template=None, *, spec=None)``:
determinism under a spec, well-formedness of every block type, the item
partition, the money-modifier invariants across a stratified spec batch, and
back-compatibility of the ``spec=None`` path.
"""

from __future__ import annotations

import random
from datetime import datetime

import pytest
from pydantic import ValidationError

from document_simulator.synthesis.receipts.content import (
    _DATE_FORMATS,
    _DATE_WINDOW,
    TEMPLATE_IDS,
    TEMPLATE_REGISTRY,
    _footer_bank,
    _label_for,
    _meta_label_bank,
    _partition_indices,
    make_receipt,
    template_file_for,
    template_spec_for,
)
from document_simulator.synthesis.receipts.layout import (
    BlockType,
    LayoutSpec,
    MoneyRole,
    load_prior,
    sample_spec,
    stratified_specs,
)

_ALL_TEMPLATES = (
    "thermal_minimal",
    "restaurant_tip",
    "retail_multicol",
    "a4_invoice",
    "taxi_stub",
)

#: A spec that exercises every block type and every money role at once.
_EXHAUSTIVE_SPEC = LayoutSpec(
    blocks=tuple(BlockType),
    money_rows=tuple(MoneyRole),
    logo_placement="TOP",
)

_PAYMENT_ROLES = {MoneyRole.TENDER, MoneyRole.CHANGE, MoneyRole.AUTH}


def _parse_timestamp(text: str) -> datetime:
    """Parse a generated DATE block value against the formats the factory uses."""
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    raise AssertionError(f"{text!r} matches none of the generated date formats")


# --------------------------------------------------------------------------- #
# Determinism
# --------------------------------------------------------------------------- #
def test_spec_driven_receipt_is_deterministic() -> None:
    """AC-4: same (seed, spec) -> identical Receipt, sections and all."""
    spec = sample_spec(random.Random(42))
    a = make_receipt(seed=42, spec=spec)
    b = make_receipt(seed=42, spec=spec)
    assert a.model_dump() == b.model_dump(), "Same seed + spec must yield identical Receipts"


@pytest.mark.parametrize("template", _ALL_TEMPLATES)
def test_spec_driven_receipt_is_deterministic_per_template(template: str) -> None:
    """AC-4: determinism holds for every template, not just the default."""
    spec = sample_spec(random.Random(42))
    a = make_receipt(seed=42, template=template, spec=spec)
    b = make_receipt(seed=42, template=template, spec=spec)
    assert a.model_dump() == b.model_dump()


def test_generated_dates_do_not_depend_on_the_wall_clock() -> None:
    """A receipt whose date is `now` is not reproducible tomorrow."""
    spec = LayoutSpec(blocks=(BlockType.DATE,), money_rows=())
    receipt = make_receipt(seed=42, template="thermal_minimal", spec=spec)
    text = receipt.sections[0].text
    assert text is not None
    moment = _parse_timestamp(text)
    lo, hi = _DATE_WINDOW
    # %y / %m-%d-only formats lose no information we assert on beyond the year.
    assert lo.year <= moment.year <= hi.year


# --------------------------------------------------------------------------- #
# Block well-formedness
# --------------------------------------------------------------------------- #
def test_every_block_type_produces_a_well_formed_block() -> None:
    """AC-4: each of the seven BlockTypes resolves to a renderable block."""
    receipt = make_receipt(seed=42, template="thermal_minimal", spec=_EXHAUSTIVE_SPEC)
    prior = load_prior()

    assert len(receipt.sections) == len(_EXHAUSTIVE_SPEC.blocks)
    assert tuple(b.type for b in receipt.sections) == _EXHAUSTIVE_SPEC.blocks
    assert receipt.style == _EXHAUSTIVE_SPEC.style

    by_type = {block.type: block for block in receipt.sections}

    header = by_type[BlockType.HEADER]
    assert header.business_details is not None
    assert receipt.merchant in header.business_details
    assert receipt.address in header.business_details
    assert header.alignment == _EXHAUSTIVE_SPEC.style.header_alignment

    items = by_type[BlockType.ITEMS]
    assert items.item_indices == tuple(range(len(receipt.items)))
    assert items.show_quantity is (_EXHAUSTIVE_SPEC.style.quantity_column == "PRESENT")
    assert items.money_rows, "the ledger rows must land somewhere"

    payment = by_type[BlockType.PAYMENT]
    assert payment.money_rows
    assert {row.role for row in payment.money_rows} <= _PAYMENT_ROLES

    custom = by_type[BlockType.CUSTOM]
    assert custom.text in _footer_bank(prior)

    date = by_type[BlockType.DATE]
    assert date.text is not None
    _parse_timestamp(date.text)

    barcode = by_type[BlockType.BARCODE]
    assert barcode.barcode_value is not None
    assert barcode.barcode_value.isdigit() and len(barcode.barcode_value) == 12

    meta = by_type[BlockType.META]
    fields = meta.left_fields + meta.right_fields
    assert fields, "a META block with no fields renders as a blank band"
    assert {f.title for f in fields} <= set(_meta_label_bank(prior))
    assert len({f.title for f in fields}) == len(fields), "meta labels must not repeat"


def test_bottom_divider_comes_from_the_spec_style() -> None:
    spec = _EXHAUSTIVE_SPEC.model_copy(
        update={"style": _EXHAUSTIVE_SPEC.style.model_copy(update={"divider_style": "STARS"})}
    )
    receipt = make_receipt(seed=7, template="thermal_minimal", spec=spec)
    assert {block.bottom_divider for block in receipt.sections} == {"STARS"}


@pytest.mark.parametrize(
    ("placement", "expected_index"),
    [("NONE", None), ("TOP", 0), ("MIDDLE", 1), ("BOTTOM", 2)],
)
def test_logo_lands_on_the_header_the_placement_names(
    placement: str, expected_index: int | None
) -> None:
    """AC-4: logo_path is set on exactly the HEADER the placement points at."""
    spec = LayoutSpec(
        blocks=(BlockType.HEADER, BlockType.HEADER, BlockType.HEADER),
        money_rows=(),
        logo_placement=placement,
    )
    receipt = make_receipt(seed=3, template="thermal_minimal", spec=spec)
    carrying = [i for i, block in enumerate(receipt.sections) if block.logo_path is not None]

    if expected_index is None or not carrying:
        # No pool on disk is a legitimate state; the placement must still not
        # scatter logos across every header.
        assert carrying == []
    else:
        assert carrying == [expected_index]


def test_no_logo_without_a_header_block() -> None:
    spec = LayoutSpec(blocks=(BlockType.ITEMS,), money_rows=(), logo_placement="TOP")
    receipt = make_receipt(seed=3, template="thermal_minimal", spec=spec)
    assert all(block.logo_path is None for block in receipt.sections)


# --------------------------------------------------------------------------- #
# Item partitioning
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(("n_items", "n_blocks"), [(8, 1), (8, 3), (3, 5), (0, 2), (10, 10)])
def test_partition_indices_is_a_partition(n_items: int, n_blocks: int) -> None:
    chunks = _partition_indices(n_items, n_blocks)
    assert len(chunks) == n_blocks
    flat = [index for chunk in chunks for index in chunk]
    assert flat == list(range(n_items)), "indices must be covered exactly once, in order"


def test_items_are_partitioned_across_every_items_block() -> None:
    """AC-4: multi-ITEMS layouts split the items -- they never duplicate them."""
    spec = LayoutSpec(
        blocks=(BlockType.HEADER, BlockType.ITEMS, BlockType.ITEMS, BlockType.ITEMS),
        money_rows=(MoneyRole.ITEM, MoneyRole.TOTAL),
    )
    receipt = make_receipt(seed=42, template="retail_multicol", spec=spec)
    chunks = [b.item_indices for b in receipt.sections if b.type is BlockType.ITEMS]

    flat = [index for chunk in chunks for index in chunk]
    assert len(flat) == len(set(flat)), "an item was printed twice"
    assert sorted(flat) == list(range(len(receipt.items))), "an item was dropped"


def test_items_partition_holds_across_a_sampled_batch() -> None:
    for index, spec in enumerate(stratified_specs(100, seed=42)):
        receipt = make_receipt(seed=index, spec=spec)
        chunks = [b.item_indices for b in receipt.sections if b.type is BlockType.ITEMS]
        flat = [i for chunk in chunks for i in chunk]
        if not chunks:
            continue
        assert sorted(flat) == list(range(len(receipt.items))), f"spec {spec.spec_id} lost items"


# --------------------------------------------------------------------------- #
# Money modifiers -- the factory must never build a Receipt that raises
# --------------------------------------------------------------------------- #
def test_money_modifiers_hold_across_a_stratified_spec_batch() -> None:
    """AC-4: 100 sampled layouts x seeds produce zero invalid receipts.

    The Receipt validator rejects tender < total and discount > subtotal. The
    factory computes modifiers in dependency order specifically so those states
    are unreachable, not merely improbable.
    """
    for index, spec in enumerate(stratified_specs(100, seed=42)):
        try:
            receipt = make_receipt(seed=index, spec=spec)
        except ValidationError as exc:  # pragma: no cover - the assertion is the point
            pytest.fail(f"spec {spec.spec_id} (seed {index}) built an invalid Receipt: {exc}")

        requested = set(spec.money_rows)

        # Reconciliation: every computed field derives from the printed parts.
        assert receipt.taxable_base == round(receipt.subtotal - (receipt.discount or 0.0), 2)
        assert receipt.tax == round(receipt.taxable_base * receipt.tax_rate, 2)
        assert receipt.total == round(receipt.taxable_base + receipt.tax + (receipt.tip or 0.0), 2)

        if MoneyRole.DISCOUNT in requested:
            assert receipt.discount is not None
            assert 0.0 <= receipt.discount < receipt.subtotal
        else:
            assert receipt.discount is None

        if MoneyRole.TIP in requested:
            assert receipt.tip is not None and receipt.tip >= 0.0
        else:
            assert receipt.tip is None

        if requested & {MoneyRole.TENDER, MoneyRole.CHANGE}:
            assert receipt.tender is not None, "CHANGE without a TENDER cannot be computed"
            assert receipt.tender >= receipt.total
            assert receipt.change == round(receipt.tender - receipt.total, 2)
            assert receipt.change is not None and receipt.change >= 0.0
        else:
            assert receipt.tender is None
            assert receipt.change is None


def test_printed_money_rows_agree_with_the_receipt_totals() -> None:
    """A row that disagrees with the model teaches wrong arithmetic."""
    expected = {
        MoneyRole.SUBTOTAL: lambda r: r.subtotal,
        MoneyRole.DISCOUNT: lambda r: r.discount,
        MoneyRole.TAX: lambda r: r.tax,
        MoneyRole.TIP: lambda r: r.tip,
        MoneyRole.TOTAL: lambda r: r.total,
        MoneyRole.TENDER: lambda r: r.tender,
        MoneyRole.CHANGE: lambda r: r.change,
    }
    for index, spec in enumerate(stratified_specs(50, seed=7)):
        receipt = make_receipt(seed=index, spec=spec)
        for block in receipt.sections:
            for row in block.money_rows:
                if row.role in expected:
                    assert row.amount == expected[row.role](receipt), f"{row.role} row mismatch"


def test_every_money_row_is_printed_exactly_once() -> None:
    """Rows must not be duplicated across the ledger and payment blocks."""
    receipt = make_receipt(seed=42, template="thermal_minimal", spec=_EXHAUSTIVE_SPEC)
    printed = [row for block in receipt.sections for row in block.money_rows]
    roles = [row.role for row in printed]
    # ITEM is carried by item_indices, not by a money row.
    assert MoneyRole.ITEM not in roles
    assert len(roles) == len(set(roles))
    assert set(roles) == set(_EXHAUSTIVE_SPEC.money_rows) - {MoneyRole.ITEM}


def test_change_implies_tender_even_when_tender_is_not_requested() -> None:
    spec = LayoutSpec(
        blocks=(BlockType.ITEMS, BlockType.PAYMENT),
        money_rows=(MoneyRole.ITEM, MoneyRole.TOTAL, MoneyRole.CHANGE),
    )
    receipt = make_receipt(seed=5, template="thermal_minimal", spec=spec)
    assert receipt.tender is not None
    assert receipt.change is not None and receipt.change >= 0.0


# --------------------------------------------------------------------------- #
# Text banks, not hardcoded constants
# --------------------------------------------------------------------------- #
def test_money_row_labels_come_from_the_mined_banks() -> None:
    """AC-4: labels are corpus-derived, so they vary the way real receipts do."""
    prior = load_prior()
    seen: dict[MoneyRole, set[str]] = {}
    for index, spec in enumerate(stratified_specs(60, seed=11)):
        receipt = make_receipt(seed=index, spec=spec)
        for block in receipt.sections:
            for row in block.money_rows:
                seen.setdefault(row.role, set()).add(row.label)

    total_labels = seen.get(MoneyRole.TOTAL, set())
    assert len(total_labels) > 1, "a constant label would defeat the point of the bank"
    assert total_labels <= set(prior.labels_for(MoneyRole.TOTAL))


def test_discount_label_falls_back_when_its_bank_is_unusable() -> None:
    """DISCOUNT's one mined label is a wrapped two-line fragment, so it is dropped."""
    prior = load_prior()
    assert prior.labels_for(MoneyRole.DISCOUNT), "the raw bank is non-empty..."
    assert _label_for(random.Random(0), prior, MoneyRole.DISCOUNT) == "DISCOUNT"


def test_custom_text_comes_from_the_footer_bank() -> None:
    prior = load_prior()
    footer = set(_footer_bank(prior))
    texts: set[str] = set()
    for index, spec in enumerate(stratified_specs(40, seed=13)):
        receipt = make_receipt(seed=index, spec=spec)
        texts |= {
            block.text
            for block in receipt.sections
            if block.type is BlockType.CUSTOM and block.text
        }
    assert len(texts) > 1
    assert texts <= footer


# --------------------------------------------------------------------------- #
# Back-compatibility -- the spec=None path is untouched
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("template", _ALL_TEMPLATES)
def test_spec_none_path_is_unchanged(template: str) -> None:
    """AC-4: adding the spec argument must not perturb the v0.2 output."""
    receipt = make_receipt(seed=42, template=template)
    assert receipt.sections == ()
    assert receipt.style is None
    assert receipt.discount is None
    assert receipt.tip is None
    assert receipt.tender is None
    assert receipt.model_dump() == make_receipt(seed=42, template=template).model_dump()


@pytest.mark.parametrize("template", _ALL_TEMPLATES)
def test_a_spec_only_adds_to_the_content_it_does_not_change_it(template: str) -> None:
    """The same seed keeps its merchant, items and card digits under any spec."""
    plain = make_receipt(seed=42, template=template)
    laid_out = make_receipt(seed=42, template=template, spec=sample_spec(random.Random(1)))

    assert laid_out.merchant == plain.merchant
    assert laid_out.address == plain.address
    assert [i.model_dump() for i in laid_out.items] == [i.model_dump() for i in plain.items]
    assert laid_out.tax_rate == plain.tax_rate
    assert laid_out.payment_last4 == plain.payment_last4


def test_neither_template_nor_spec_raises() -> None:
    with pytest.raises(ValueError, match="requires a template, a spec, or both"):
        make_receipt(seed=1)


def test_unknown_template_still_raises_with_a_spec() -> None:
    with pytest.raises(ValueError, match="Unknown template"):
        make_receipt(seed=1, template="nope", spec=sample_spec(random.Random(0)))


def test_spec_only_call_varies_its_template() -> None:
    """A spec-only batch must not be all one persona."""
    spec = sample_spec(random.Random(2))
    merchants = {make_receipt(seed=s, spec=spec).merchant for s in range(30)}
    assert len(merchants) > 1


# --------------------------------------------------------------------------- #
# The unified template registry
# --------------------------------------------------------------------------- #
def test_registry_exposes_every_template_with_a_jinja_file() -> None:
    """The registry is the single source of truth the router reads from."""
    assert set(TEMPLATE_IDS) == set(_ALL_TEMPLATES)
    for template_id in TEMPLATE_IDS:
        entry = template_spec_for(template_id)
        assert entry.template_id == template_id
        assert template_file_for(template_id) == entry.jinja_file
        assert entry.jinja_file.endswith(".html.j2")
        assert entry.display_name and entry.description
        assert TEMPLATE_REGISTRY[template_id] is entry


def test_registry_jinja_files_exist_on_disk() -> None:
    """The drift this registry exists to prevent would show up exactly here."""
    from document_simulator.synthesis.receipts import render

    for entry in TEMPLATE_REGISTRY.values():
        assert (render._TEMPLATES_DIR / entry.jinja_file).is_file()


def test_template_file_for_rejects_unknown_ids() -> None:
    with pytest.raises(ValueError, match="Unknown template"):
        template_file_for("this_template_does_not_exist")
