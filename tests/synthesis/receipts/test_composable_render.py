"""Unit tests for the composable renderer (v0.4 Stage 5).

The composable template is data-driven: one template renders every layout the
sampler can emit, so the coverage that used to live per-template now lives per
*block type* and per *style axis*.

Acceptance criteria exercised here:
  AC-1  every BlockType renders and contributes >= 1 tagged token
  AC-2  every emitted token carries a non-null semantic_role
  AC-3  every token polygon is non-degenerate and inside the image
  AC-4  each divider_style value produces materially different markup
  AC-5  each total_emphasis value produces materially different CSS, and the
        strongest emphasis measurably enlarges the TOTAL row
  AC-6  a receipt with many blocks still paginates to exactly one page and
        loses no tokens (FDD decision #8 -- render.py reads pages[0] only)
  AC-7  image_id is keyed on seed + spec identity, so a spec sweep at one seed
        cannot overwrite itself; a receipt with no spec keeps the legacy %08d

Receipts are constructed inline rather than via ``content.py`` so these tests
pin the renderer alone.
"""

from __future__ import annotations

import re

import pytest
from PIL import Image
from weasyprint import HTML

from document_simulator.synthesis.receipts.layout.spec import (
    BlockType,
    MoneyRole,
    ReceiptStyle,
)
from document_simulator.synthesis.receipts.render import (
    COMPOSABLE_TEMPLATE,
    build_html,
    render_receipt,
)
from document_simulator.synthesis.receipts.schema import (
    ImageGroundTruth,
    LineItem,
    MetaField,
    MoneyRow,
    Receipt,
    ReceiptBlock,
)

SEED = 42

DIVIDER_STYLES = ("DASHES", "STARS", "EQUALS", "COLONS", "DOTS", "EMPTY", "NONE")
TOTAL_EMPHASES = (
    "NONE",
    "PERCENT_10",
    "PERCENT_20",
    "PERCENT_50",
    "PERCENT_75",
    "PERCENT_100",
)

_ITEMS = [
    LineItem(sku="ESPRESSO", qty=2, unit_price=3.50),
    LineItem(sku="BAGEL", qty=1, unit_price=2.25),
    LineItem(sku="ORANGE JUICE", qty=3, unit_price=1.75),
]


def _receipt(*blocks: ReceiptBlock, style: ReceiptStyle | None = None) -> Receipt:
    """Build a Receipt whose sections are exactly ``blocks``."""
    return Receipt(
        merchant="ACME PROVISIONS",
        address="1 Main Street, Springfield",
        items=list(_ITEMS),
        tax_rate=0.08,
        payment_last4="4242",
        tender=40.00,
        style=style if style is not None else ReceiptStyle(),
        sections=blocks,
    )


def _block_for(block_type: BlockType) -> ReceiptBlock:
    """A minimally-populated block of the requested type, with content to tag."""
    if block_type is BlockType.HEADER:
        return ReceiptBlock(type=block_type, business_details="1 Main Street, Springfield")
    if block_type is BlockType.ITEMS:
        return ReceiptBlock(
            type=block_type,
            item_indices=(0, 1, 2),
            money_rows=(
                MoneyRow(role=MoneyRole.SUBTOTAL, label="SUBTOTAL", amount=14.50),
                MoneyRow(role=MoneyRole.TAX, label="TAX", amount=1.16),
                MoneyRow(role=MoneyRole.TOTAL, label="TOTAL", amount=15.66),
            ),
        )
    if block_type is BlockType.PAYMENT:
        return ReceiptBlock(
            type=block_type,
            money_rows=(
                MoneyRow(role=MoneyRole.TENDER, label="CASH", amount=40.00),
                MoneyRow(role=MoneyRole.CHANGE, label="CHANGE", amount=24.34),
                MoneyRow(role=MoneyRole.AUTH, label="AUTH", text="A1B2C3D4"),
            ),
        )
    if block_type is BlockType.CUSTOM:
        return ReceiptBlock(type=block_type, text="THANK YOU FOR SHOPPING")
    if block_type is BlockType.DATE:
        return ReceiptBlock(type=block_type, text="31/08/2026 14:07")
    if block_type is BlockType.BARCODE:
        return ReceiptBlock(type=block_type, barcode_value="0123456789128")
    if block_type is BlockType.META:
        return ReceiptBlock(
            type=block_type,
            left_fields=(MetaField(title="Table", value="14"),),
            right_fields=(MetaField(title="Server", value="ANN"),),
        )
    raise AssertionError(f"no fixture for BlockType {block_type}")


def _token_ids_in_html(html: str) -> set[str]:
    """Every data-token-id the template emitted, regardless of what rendered."""
    return set(re.findall(r'data-token-id="([^"]+)"', html))


def _divider_markup(html: str) -> list[str]:
    """The rendered divider elements, isolated from the rest of the document."""
    return re.findall(r'<div class="divider[^"]*">[^<]*</div>', html)


def _total_rule(html: str) -> str:
    """The `.money-row.role-total { ... }` CSS rule body."""
    match = re.search(r"\.money-row\.role-total \{(.*?)\}", html, re.DOTALL)
    assert match is not None, "composable template emitted no .role-total rule"
    return match.group(1).strip()


# --------------------------------------------------------------------------
# AC-1 / AC-2 / AC-3
# --------------------------------------------------------------------------

_BLOCK_CASES = (
    (BlockType.HEADER, 2, {"merchant", "address"}),
    (BlockType.ITEMS, 9, {"item_qty", "item_sku", "item_price", "subtotal", "tax", "total"}),
    (BlockType.PAYMENT, 6, {"tender", "change", "auth"}),
    (BlockType.CUSTOM, 1, {"footer"}),
    (BlockType.DATE, 1, {"date"}),
    (BlockType.BARCODE, 1, {"barcode"}),
    (BlockType.META, 4, {"meta"}),
)


@pytest.mark.parametrize("block_type,min_tokens,expected_roles", _BLOCK_CASES)
def test_every_block_type_renders_and_emits_tokens(
    block_type: BlockType, min_tokens: int, expected_roles: set[str]
) -> None:
    """AC-1: each BlockType renders standalone and contributes tagged tokens."""
    receipt = _receipt(_block_for(block_type))
    image, gt = render_receipt(receipt, seed=SEED, template_name=COMPOSABLE_TEMPLATE)

    assert isinstance(image, Image.Image), f"{block_type}: image is not PIL.Image"
    assert isinstance(gt, ImageGroundTruth), f"{block_type}: gt is not ImageGroundTruth"
    assert len(gt.tokens) >= min_tokens, (
        f"{block_type}: only {len(gt.tokens)} tokens (need >= {min_tokens})"
    )

    roles = {token.semantic_role for token in gt.tokens}
    missing = expected_roles - roles
    assert not missing, f"{block_type}: expected semantic roles {sorted(missing)} not emitted"


@pytest.mark.parametrize("block_type,_min_tokens,_roles", _BLOCK_CASES)
def test_every_token_has_a_semantic_role(
    block_type: BlockType, _min_tokens: int, _roles: set[str]
) -> None:
    """AC-2: no token comes back with semantic_role still None."""
    receipt = _receipt(_block_for(block_type))
    _, gt = render_receipt(receipt, seed=SEED, template_name=COMPOSABLE_TEMPLATE)

    untagged = [token.token_id for token in gt.tokens if token.semantic_role is None]
    assert not untagged, f"{block_type}: tokens without semantic_role: {untagged}"


def test_token_ids_are_unique_across_a_full_receipt() -> None:
    """AC-1: stacking every block type twice still yields unique token ids."""
    blocks = [_block_for(bt) for bt in BlockType] * 2
    receipt = _receipt(*blocks)
    _, gt = render_receipt(receipt, seed=SEED, template_name=COMPOSABLE_TEMPLATE)

    ids = [token.token_id for token in gt.tokens]
    assert len(ids) == len(set(ids)), (
        f"duplicate token ids: {sorted({i for i in ids if ids.count(i) > 1})}"
    )


def test_token_polygons_are_well_formed_within_image() -> None:
    """AC-3: every polygon is non-degenerate and inside the rendered image."""
    blocks = [_block_for(bt) for bt in BlockType]
    receipt = _receipt(*blocks, style=ReceiptStyle(divider_style="DASHES"))
    image, gt = render_receipt(receipt, seed=SEED, template_name=COMPOSABLE_TEMPLATE)
    width, height = image.size

    assert gt.tokens, "composable render produced no tokens at all"
    for token in gt.tokens:
        polygon = token.coords[0].polygon
        assert len(polygon) >= 3, f"{token.token_id}: polygon has <3 vertices"

        xs = [p[0] for p in polygon]
        ys = [p[1] for p in polygon]
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)

        assert x_max - x_min > 0, f"{token.token_id}: zero width polygon"
        assert y_max - y_min > 0, f"{token.token_id}: zero height polygon"
        assert -2 <= x_min and x_max <= width + 2, (
            f"{token.token_id}: x out of bounds [{x_min}, {x_max}] vs width {width}"
        )
        assert -2 <= y_min and y_max <= height + 2, (
            f"{token.token_id}: y out of bounds [{y_min}, {y_max}] vs height {height}"
        )


# --------------------------------------------------------------------------
# AC-4  divider_style
# --------------------------------------------------------------------------


def test_each_divider_style_renders_distinct_markup() -> None:
    """AC-4: the 7 divider_style values yield 7 distinct divider renderings."""
    rendered: dict[str, str] = {}
    for value in DIVIDER_STYLES:
        receipt = _receipt(
            ReceiptBlock(type=BlockType.CUSTOM, text="THANK YOU", bottom_divider=value),
            ReceiptBlock(type=BlockType.DATE, text="31/08/2026"),
            style=ReceiptStyle(divider_style=value),
        )
        rendered[value] = "\n".join(_divider_markup(build_html(receipt, COMPOSABLE_TEMPLATE)))

    for value, markup in rendered.items():
        clashes = [other for other, m in rendered.items() if other != value and m == markup]
        assert not clashes, f"divider_style={value} renders identically to {clashes}"


@pytest.mark.parametrize(
    "value,glyph",
    (("DASHES", "-"), ("STARS", "*"), ("EQUALS", "="), ("COLONS", ":"), ("DOTS", ".")),
)
def test_glyph_dividers_print_their_taxonomy_character(value: str, glyph: str) -> None:
    """AC-4: DASHES/STARS/EQUALS/COLONS/DOTS print a run of their own glyph."""
    receipt = _receipt(
        ReceiptBlock(type=BlockType.CUSTOM, text="THANK YOU", bottom_divider=value),
        style=ReceiptStyle(divider_style=value),
    )
    dividers = _divider_markup(build_html(receipt, COMPOSABLE_TEMPLATE))

    assert dividers, f"divider_style={value} rendered no divider element"
    assert f"divider-{value.lower()}" in dividers[0], (
        f"{value}: missing divider-{value.lower()} class"
    )
    assert glyph * 8 in dividers[0], f"{value}: divider does not contain a run of {glyph!r}"


def test_empty_divider_is_a_blank_line_and_none_renders_nothing() -> None:
    """AC-4: EMPTY reserves a blank line; NONE emits no element at all."""
    empty = _receipt(
        ReceiptBlock(type=BlockType.CUSTOM, text="THANK YOU", bottom_divider="EMPTY"),
        style=ReceiptStyle(divider_style="EMPTY"),
    )
    none = _receipt(
        ReceiptBlock(type=BlockType.CUSTOM, text="THANK YOU", bottom_divider="NONE"),
        style=ReceiptStyle(divider_style="NONE"),
    )

    empty_dividers = _divider_markup(build_html(empty, COMPOSABLE_TEMPLATE))
    assert len(empty_dividers) == 1, f"EMPTY: expected 1 divider element, got {empty_dividers}"
    assert "divider-empty" in empty_dividers[0], "EMPTY: missing divider-empty class"
    inner = re.sub(r"^<div[^>]*>|</div>$", "", empty_dividers[0])
    assert inner == "", f"EMPTY: divider should carry no glyphs, got {inner!r}"

    assert not _divider_markup(build_html(none, COMPOSABLE_TEMPLATE)), (
        "NONE: expected no divider element to be emitted"
    )


# --------------------------------------------------------------------------
# AC-5  total_emphasis
# --------------------------------------------------------------------------


def test_each_total_emphasis_produces_distinct_css() -> None:
    """AC-5: the 6 total_emphasis values yield 6 distinct .role-total rules."""
    rules: dict[str, str] = {}
    for value in TOTAL_EMPHASES:
        receipt = _receipt(_block_for(BlockType.ITEMS), style=ReceiptStyle(total_emphasis=value))
        rules[value] = _total_rule(build_html(receipt, COMPOSABLE_TEMPLATE))

    for value, rule in rules.items():
        clashes = [other for other, r in rules.items() if other != value and r == rule]
        assert not clashes, f"total_emphasis={value} yields the same CSS as {clashes}: {rule!r}"


@pytest.mark.parametrize(
    "value,scale", (("NONE", "1"), ("PERCENT_10", "1.1"), ("PERCENT_100", "2"))
)
def test_total_emphasis_sets_the_expected_font_scale(value: str, scale: str) -> None:
    """AC-5: the emphasis percentage lands as an em multiplier on the total row."""
    receipt = _receipt(_block_for(BlockType.ITEMS), style=ReceiptStyle(total_emphasis=value))
    rule = _total_rule(build_html(receipt, COMPOSABLE_TEMPLATE))
    assert f"font-size: {scale}em" in rule, (
        f"total_emphasis={value}: expected {scale}em, got {rule!r}"
    )


def test_strongest_total_emphasis_enlarges_the_rendered_total() -> None:
    """AC-5: emphasis is not merely declared -- it changes rendered glyph size."""
    heights: dict[str, float] = {}
    for value in ("NONE", "PERCENT_100"):
        receipt = _receipt(_block_for(BlockType.ITEMS), style=ReceiptStyle(total_emphasis=value))
        _, gt = render_receipt(receipt, seed=SEED, template_name=COMPOSABLE_TEMPLATE)
        totals = [t for t in gt.tokens if t.semantic_role == "total" and t.text == "15.66"]
        assert len(totals) == 1, f"total_emphasis={value}: expected 1 total amount, got {totals}"
        ys = [p[1] for p in totals[0].coords[0].polygon]
        heights[value] = max(ys) - min(ys)

    assert heights["PERCENT_100"] > heights["NONE"] * 1.5, (
        f"PERCENT_100 total height {heights['PERCENT_100']} is not materially larger "
        f"than NONE {heights['NONE']}"
    )


# --------------------------------------------------------------------------
# AC-6  pagination (FDD decision #8)
# --------------------------------------------------------------------------


def _many_block_receipt() -> Receipt:
    """A layout far longer than anything the corpus prior can sample."""
    blocks: list[ReceiptBlock] = [_block_for(BlockType.HEADER)]
    for index in range(18):
        blocks.append(
            ReceiptBlock(
                type=BlockType.CUSTOM,
                text=f"PROMOTIONAL LINE {index:02d}",
                bottom_divider="DASHES",
            )
        )
    blocks.append(_block_for(BlockType.META))
    blocks.append(_block_for(BlockType.DATE))
    blocks.append(_block_for(BlockType.ITEMS))
    blocks.append(_block_for(BlockType.ITEMS))
    blocks.append(_block_for(BlockType.PAYMENT))
    blocks.append(_block_for(BlockType.BARCODE))
    return _receipt(*blocks, style=ReceiptStyle(divider_style="DASHES"))


def test_many_block_receipt_fits_on_exactly_one_page() -> None:
    """AC-6: the default page height absorbs a 24-block layout without spilling.

    render.py rasterizes and walks ``document.pages[0]`` only, so a second page
    would silently delete tokens from both the image and the ground truth.
    """
    receipt = _many_block_receipt()
    html = build_html(receipt, COMPOSABLE_TEMPLATE)
    document = HTML(string=html).render()

    assert len(document.pages) == 1, (
        f"{len(receipt.sections)}-block receipt paginated to {len(document.pages)} pages; "
        "tokens past page 1 would be silently dropped"
    )


def test_many_block_receipt_loses_no_tokens() -> None:
    """AC-6: every data-token-id in the markup survives into the ground truth."""
    receipt = _many_block_receipt()
    html = build_html(receipt, COMPOSABLE_TEMPLATE)
    _, gt = render_receipt(receipt, seed=SEED, template_name=COMPOSABLE_TEMPLATE)

    declared = _token_ids_in_html(html)
    harvested = {token.token_id for token in gt.tokens}
    assert declared, "template declared no tokens for the many-block receipt"
    assert not declared - harvested, (
        f"{len(declared - harvested)} of {len(declared)} tokens were lost during render: "
        f"{sorted(declared - harvested)[:10]}"
    )


def test_page_height_is_configurable_for_longer_layouts() -> None:
    """AC-6: page_height is a knob, so an even longer layout stays recoverable."""
    receipt = _many_block_receipt()
    short = HTML(string=build_html(receipt, COMPOSABLE_TEMPLATE, page_height="60mm")).render()
    tall = HTML(string=build_html(receipt, COMPOSABLE_TEMPLATE, page_height="900mm")).render()

    assert len(short.pages) > 1, "60mm page was expected to overflow; the fixture is too short"
    assert len(tall.pages) == 1, f"900mm page still paginated to {len(tall.pages)} pages"


# --------------------------------------------------------------------------
# AC-7  image_id collision
# --------------------------------------------------------------------------


def test_different_styles_at_one_seed_get_different_image_ids() -> None:
    """AC-7 regression: a spec sweep at seed 42 must not all write 00000042.png."""
    style_a = ReceiptStyle(divider_style="DASHES", total_emphasis="NONE")
    style_b = ReceiptStyle(divider_style="STARS", total_emphasis="PERCENT_50")

    _, gt_a = render_receipt(
        _receipt(_block_for(BlockType.ITEMS), style=style_a),
        seed=SEED,
        template_name=COMPOSABLE_TEMPLATE,
    )
    _, gt_b = render_receipt(
        _receipt(_block_for(BlockType.ITEMS), style=style_b),
        seed=SEED,
        template_name=COMPOSABLE_TEMPLATE,
    )

    assert gt_a.image_id != gt_b.image_id, (
        f"two styles at seed {SEED} collided on image_id={gt_a.image_id!r}; "
        "the second render would overwrite the first"
    )
    assert gt_a.image_path != gt_b.image_path, f"image_path collided: {gt_a.image_path}"
    assert gt_a.image_id.startswith(f"{SEED:08d}_"), f"unexpected id shape {gt_a.image_id!r}"


def test_different_block_skeletons_at_one_seed_get_different_image_ids() -> None:
    """AC-7: spec identity covers the block skeleton, not just the style axes."""
    style = ReceiptStyle()
    _, gt_a = render_receipt(
        _receipt(_block_for(BlockType.HEADER), _block_for(BlockType.ITEMS), style=style),
        seed=SEED,
        template_name=COMPOSABLE_TEMPLATE,
    )
    _, gt_b = render_receipt(
        _receipt(
            _block_for(BlockType.HEADER),
            _block_for(BlockType.ITEMS),
            _block_for(BlockType.BARCODE),
            style=style,
        ),
        seed=SEED,
        template_name=COMPOSABLE_TEMPLATE,
    )
    assert gt_a.image_id != gt_b.image_id, f"block skeletons collided on {gt_a.image_id!r}"


def test_image_id_is_stable_across_repeated_renders() -> None:
    """AC-7: the id is content-derived, so re-rendering reproduces it exactly."""
    receipt = _receipt(_block_for(BlockType.ITEMS), style=ReceiptStyle(divider_style="DOTS"))
    _, first = render_receipt(receipt, seed=SEED, template_name=COMPOSABLE_TEMPLATE)
    _, second = render_receipt(receipt, seed=SEED, template_name=COMPOSABLE_TEMPLATE)
    assert first.image_id == second.image_id, (
        f"image_id is not deterministic: {first.image_id!r} then {second.image_id!r}"
    )


def test_image_id_is_filesystem_safe() -> None:
    """AC-7: ids stay restricted to characters legal in a filename everywhere."""
    _, gt = render_receipt(
        _receipt(_block_for(BlockType.ITEMS), style=ReceiptStyle()),
        seed=SEED,
        template_name=COMPOSABLE_TEMPLATE,
        spec_id="spec/with:illegal chars*",
    )
    assert re.fullmatch(r"[A-Za-z0-9._-]+", gt.image_id), f"unsafe image_id {gt.image_id!r}"
    assert gt.image_id.startswith(f"{SEED:08d}_"), f"unexpected id shape {gt.image_id!r}"


def test_receipt_without_a_spec_keeps_the_legacy_id_format() -> None:
    """AC-7: v0.1/v0.2 receipts keep bare %08d so on-disk datasets stay valid."""
    legacy = Receipt(
        merchant="ACME PROVISIONS",
        address="1 Main Street, Springfield",
        items=list(_ITEMS),
        tax_rate=0.08,
        payment_last4="4242",
    )
    assert legacy.style is None and not legacy.sections, "fixture is not spec-free"

    _, gt = render_receipt(legacy, seed=SEED)
    assert gt.image_id == f"{SEED:08d}", f"legacy id changed to {gt.image_id!r}"
    assert str(gt.image_path) == f"images/{SEED:08d}.png", f"legacy path changed to {gt.image_path}"
