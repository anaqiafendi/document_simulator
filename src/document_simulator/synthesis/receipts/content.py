"""Faker-driven `Receipt` content factory (FDD #28, v0.2 content / v0.4 layout).

Public API:
    make_receipt(seed, template=None, *, spec=None) -> Receipt
        Faker-backed, locale-aware, arithmetic-consistent receipt. Passing a
        :class:`LayoutSpec` additionally resolves the spec's blocks and money
        rows into ``Receipt.sections`` / ``Receipt.style``.
    make_minimal_receipt(seed) -> Receipt
        Back-compat wrapper -> make_receipt(seed, "thermal_minimal").
    TEMPLATE_REGISTRY / TEMPLATES / TEMPLATE_IDS
        The single source of truth for the shipped templates: SKU corpus,
        locale, item-count distribution *and* Jinja2 filename + UI copy.
    template_spec_for(id) / template_file_for(id)
        Registry lookups. The API router uses ``template_file_for`` so the
        router and this module cannot drift apart again.

Each template binds to a specific SKU corpus (small JSON files bundled in
``sku_corpora/``) and a content distribution (number of line items, presence of
tip lines, etc.). Output is fully deterministic for a fixed (seed, template,
spec) triple: Faker is seeded per call via ``Faker.seed_instance(seed)`` and a
private ``random.Random(seed)`` is used for any non-Faker numeric draws. The
module-level ``random`` is never touched.
"""

from __future__ import annotations

import json
import math
import random
from collections.abc import Callable, Iterable, Sequence
from datetime import datetime
from functools import cache
from importlib.resources import files
from pathlib import Path
from typing import Any, Final, NamedTuple

from faker import Faker

from document_simulator.synthesis.receipts.layout.prior import Prior, load_prior
from document_simulator.synthesis.receipts.layout.spec import (
    BlockType,
    LayoutSpec,
    MoneyRole,
)
from document_simulator.synthesis.receipts.schema import (
    LineItem,
    MetaField,
    MoneyRow,
    Receipt,
    ReceiptBlock,
)

# ---------------------------------------------------------------------------
# Template registry -- ONE definition, used by both the content factory and the
# API router. Each entry binds a SKU corpus, locale and item-count distribution
# to the Jinja2 file that renders it plus the copy the UI shows for it. Adding a
# new template == adding an entry here + a Jinja2 file; nothing else.
# ---------------------------------------------------------------------------


class TemplateSpec(NamedTuple):
    """Everything the pipeline knows about one shipped receipt template."""

    template_id: str
    jinja_file: str
    display_name: str
    description: str
    corpus: str
    locale: str
    min_items: int
    max_items: int
    merchant_style: str


TEMPLATES: Final[tuple[TemplateSpec, ...]] = (
    TemplateSpec(
        template_id="thermal_minimal",
        jinja_file="thermal_minimal.html.j2",
        display_name="Thermal Single-Column",
        description=(
            "Classic 80mm thermal printer receipt with merchant header, line items, and totals."
        ),
        corpus="grocery",
        locale="en_US",
        min_items=3,
        max_items=8,
        merchant_style="grocery",
    ),
    TemplateSpec(
        template_id="restaurant_tip",
        jinja_file="restaurant_tip.html.j2",
        display_name="Restaurant w/ Tip Lines",
        description=(
            "Sit-down restaurant receipt: server name, table, tip suggestions (15/18/20%)."
        ),
        corpus="restaurant",
        locale="en_US",
        min_items=2,
        max_items=6,
        merchant_style="restaurant",
    ),
    TemplateSpec(
        template_id="retail_multicol",
        jinja_file="retail_multicol.html.j2",
        display_name="Retail Multi-Column",
        description="Big-box retail receipt with a 3-column SKU / description / price grid.",
        corpus="grocery",
        locale="en_US",
        min_items=5,
        max_items=10,
        merchant_style="retail",
    ),
    TemplateSpec(
        template_id="a4_invoice",
        jinja_file="a4_invoice.html.j2",
        display_name="A4 Invoice",
        description=(
            "Full-page A4 invoice layout with billing block, item table, and grand total."
        ),
        corpus="restaurant",
        locale="en_US",
        min_items=3,
        max_items=7,
        merchant_style="company",
    ),
    TemplateSpec(
        template_id="taxi_stub",
        jinja_file="taxi_stub.html.j2",
        display_name="Taxi / Parking Stub",
        description="Narrow rideshare or parking stub: driver, route, fare breakdown, tip line.",
        corpus="services",
        locale="en_US",
        min_items=3,
        max_items=5,
        merchant_style="taxi",
    ),
)

#: Registry keyed by template id, in declaration order.
TEMPLATE_REGISTRY: Final[dict[str, TemplateSpec]] = {t.template_id: t for t in TEMPLATES}

#: Valid template ids, in declaration order (the order the UI lists them in).
TEMPLATE_IDS: Final[tuple[str, ...]] = tuple(TEMPLATE_REGISTRY)


def template_spec_for(template_id: str) -> TemplateSpec:
    """Look up one template's full binding.

    Args:
        template_id: A registered template id.

    Returns:
        The :class:`TemplateSpec` for ``template_id``.

    Raises:
        ValueError: If ``template_id`` is not registered.
    """
    try:
        return TEMPLATE_REGISTRY[template_id]
    except KeyError:
        valid = ", ".join(sorted(TEMPLATE_REGISTRY))
        raise ValueError(f"Unknown template {template_id!r}. Valid templates: {valid}") from None


def template_file_for(template_id: str) -> str:
    """Jinja2 filename that renders ``template_id``.

    Raises:
        ValueError: If ``template_id`` is not registered.
    """
    return template_spec_for(template_id).jinja_file


# ---------------------------------------------------------------------------
# SKU corpus loader -- cached at module level so repeated `make_receipt` calls
# don't re-read the JSON file every time.
# ---------------------------------------------------------------------------


@cache
def _load_sku_corpus(category: str) -> dict[str, Any]:
    """Load a SKU corpus JSON file from the package's `sku_corpora/` directory.

    Args:
        category: Filename stem (e.g. "grocery", "restaurant", "services").

    Returns:
        The parsed corpus dict with keys ``currency``, ``tax_rate_range``, ``items``.

    Raises:
        FileNotFoundError: If no JSON file exists for the given category.
    """
    pkg = files("document_simulator.synthesis.receipts.sku_corpora")
    path = pkg / f"{category}.json"
    parsed: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return parsed


# ---------------------------------------------------------------------------
# Per-style merchant generators -- wrap Faker with style-specific suffixes so a
# "restaurant" reads differently from a "grocery" without needing locale changes.
# ---------------------------------------------------------------------------


def _make_merchant(faker: Faker, style: str) -> str:
    """Build a stylised merchant name appropriate for the receipt class."""
    if style == "grocery":
        return f"{faker.last_name().upper()} GROCERY MARKET"
    if style == "restaurant":
        # E.g. "BLUE BAY GRILL" or "AVERY DINER"
        adjective = faker.word(
            ext_word_list=[
                "BLUE",
                "RED",
                "GOLDEN",
                "SILVER",
                "RIVER",
                "OAK",
                "PINE",
                "STONE",
                "URBAN",
                "RUSTIC",
                "WILD",
                "ROYAL",
            ]
        )
        venue = faker.word(
            ext_word_list=[
                "GRILL",
                "DINER",
                "KITCHEN",
                "BISTRO",
                "TAVERN",
                "EATERY",
                "CAFE",
                "HOUSE",
            ]
        )
        return f"{adjective} {venue}"
    if style == "retail":
        return f"{faker.last_name().upper()}MART"
    if style == "company":
        return faker.company().upper()
    if style == "taxi":
        return f"{faker.city().upper()} TAXI & PARKING"
    return faker.company().upper()


def _make_address(faker: Faker) -> str:
    """One-line postal address for the receipt header (newlines stripped)."""
    raw = faker.address()
    # Faker puts a literal newline between street and city/state — flatten it.
    return raw.replace("\n", ", ")


# ---------------------------------------------------------------------------
# Layout support (v0.4)
# ---------------------------------------------------------------------------

#: Money roles printed by a PAYMENT block rather than under the item ledger.
_PAYMENT_ROLES: Final[frozenset[MoneyRole]] = frozenset(
    {MoneyRole.TENDER, MoneyRole.CHANGE, MoneyRole.AUTH}
)

#: Blocks whose rows read as left-flowing columns rather than centred banners.
#: HEADER takes its alignment from the spec; the rest are structural.
_LEFT_ALIGNED_BLOCKS: Final[frozenset[BlockType]] = frozenset(
    {BlockType.ITEMS, BlockType.PAYMENT, BlockType.META}
)

#: Used only when the mined label bank for a role is unusable (DISCOUNT's single
#: mined label is a wrapped two-line fragment, so it is filtered out entirely).
_DEFAULT_ROLE_LABELS: Final[dict[MoneyRole, str]] = {
    MoneyRole.ITEM: "ITEM",
    MoneyRole.SUBTOTAL: "SUBTOTAL",
    MoneyRole.DISCOUNT: "DISCOUNT",
    MoneyRole.TAX: "TAX",
    MoneyRole.TIP: "TIP",
    MoneyRole.TOTAL: "TOTAL",
    MoneyRole.TENDER: "TENDER",
    MoneyRole.CHANGE: "CHANGE",
    MoneyRole.META: "NOTE",
    MoneyRole.AUTH: "AUTH CODE",
}

#: How each numeric role reads its amount off the finished receipt. Keeping the
#: arithmetic on the model means a money row can never disagree with the totals.
_AMOUNT_BY_ROLE: Final[dict[MoneyRole, Callable[[Receipt], float | None]]] = {
    MoneyRole.SUBTOTAL: lambda r: r.subtotal,
    MoneyRole.DISCOUNT: lambda r: r.discount,
    MoneyRole.TAX: lambda r: r.tax,
    MoneyRole.TIP: lambda r: r.tip,
    MoneyRole.TOTAL: lambda r: r.total,
    MoneyRole.TENDER: lambda r: r.tender,
    MoneyRole.CHANGE: lambda r: r.change,
}

#: Discount as a share of subtotal. Capped well below 1.0 so the sampled value
#: cannot approach the subtotal, which the Receipt validator would reject.
_DISCOUNT_SHARE: Final[tuple[float, float]] = (0.05, 0.25)

#: Tip rates seen on real card terminals' suggested-tip rows.
_TIP_RATES: Final[tuple[float, ...]] = (0.10, 0.125, 0.15, 0.18, 0.20, 0.25)

#: Note denominations a customer plausibly hands over. ``0`` means exact payment
#: (card, or counted cash), which is by far the most common single case.
_TENDER_STEPS: Final[tuple[int, ...]] = (0, 1, 1, 5, 5, 10, 20, 50)

#: Fixed window for generated timestamps. Deliberately *not* "now" -- a receipt
#: whose date depends on the wall clock is not reproducible tomorrow.
_DATE_WINDOW: Final[tuple[datetime, datetime]] = (
    datetime(2023, 1, 1),
    datetime(2025, 12, 31),
)

_DATE_FORMATS: Final[tuple[str, ...]] = (
    "%m/%d/%Y %I:%M %p",
    "%m/%d/%y %H:%M",
    "%d/%m/%Y %H:%M",
    "%Y-%m-%d %H:%M:%S",
    "%b %d, %Y %I:%M%p",
)

#: Logo pool shipped with the repo (Git LFS). Absolute paths are emitted because
#: WeasyPrint resolves a relative ``src`` against the *template* directory, not
#: the repo root, so a relative value would silently fail to load. Reassign this
#: to point the factory at a different pool.
LOGO_DIR: Path = Path(__file__).resolve().parents[4] / "data" / "receiptfaker" / "logos"

_LOGO_SUFFIXES: Final[frozenset[str]] = frozenset({".png", ".jpg", ".jpeg", ".webp", ".gif"})


@cache
def _logo_pool(directory: Path) -> tuple[str, ...]:
    """Sorted absolute paths of usable logo images, empty when none are present.

    Sorted rather than in directory order so the pool -- and therefore the
    logo a given seed picks -- is stable across processes and filesystems.
    """
    if not directory.is_dir():
        return ()
    return tuple(sorted(str(p) for p in directory.iterdir() if p.suffix.lower() in _LOGO_SUFFIXES))


def _pick_logo(rng: random.Random) -> str | None:
    """Choose one logo from the pool, or None when the pool is unavailable."""
    pool = _logo_pool(LOGO_DIR)
    return rng.choice(pool) if pool else None


def _clean_labels(bank: Sequence[str]) -> list[str]:
    """Drop mined labels that are blank or were wrapped across two printed lines.

    A two-line fragment such as ``"Balance before \\nSaving"`` is an artefact of
    the OCR that produced the bank, not a label any receipt actually prints.
    """
    return [label.strip() for label in bank if label.strip() and "\n" not in label]


def _label_for(rng: random.Random, prior: Prior, role: MoneyRole) -> str:
    """Resolve a money row's printed label from the mined bank for its role."""
    bank = _clean_labels(prior.labels_for(role))
    if not bank:
        return _DEFAULT_ROLE_LABELS[role]
    return rng.choice(bank)


def _meta_label_bank(prior: Prior) -> list[str]:
    """Two-column metadata titles, de-duplicated and stripped of mined values.

    Some mined entries carry their example value (``"Customer: J Manchester"``);
    only the part before the colon is the label.
    """
    seen: dict[str, None] = {}
    for raw in prior.text_banks.get("meta_labels", []):
        label = str(raw).split(":")[0].strip()
        if label and "\n" not in label:
            seen.setdefault(label, None)
    return list(seen)


def _footer_bank(prior: Prior) -> list[str]:
    """Free-text footer lines mined from the corpus."""
    return _clean_labels([str(line) for line in prior.text_banks.get("footer", [])])


def _make_timestamp(rng: random.Random, faker: Faker) -> str:
    """A generated -- never replayed -- receipt timestamp."""
    moment = faker.date_time_between(*_DATE_WINDOW)
    return str(moment.strftime(rng.choice(_DATE_FORMATS)))


def _make_barcode(rng: random.Random) -> str:
    """A 12-digit numeric barcode payload (UPC-A length, check digit not encoded)."""
    return f"{rng.randrange(10**12):012d}"


def _meta_value(rng: random.Random, faker: Faker, label: str) -> str:
    """Invent a plausible value for a two-column metadata label."""
    key = label.lower()
    if "date" in key or "time" in key:
        return _make_timestamp(rng, faker)
    if any(word in key for word in ("server", "cashier", "clerk", "attendant", "name", "driver")):
        return str(faker.first_name())
    if any(word in key for word in ("price", "amount", "total", "fare", "balance")):
        return f"{rng.uniform(1.0, 250.0):.2f}"
    if "year" in key:
        return str(rng.randrange(2010, 2026))
    if any(word in key for word in ("phone", "tel")):
        return f"({rng.randrange(200, 1000)}) {rng.randrange(200, 1000)}-{rng.randrange(10000):04d}"
    return str(rng.randrange(1, 999))


# --- money modifiers -------------------------------------------------------


def _sample_discount(rng: random.Random, subtotal: float) -> float:
    """A discount that is non-negative and strictly below the subtotal.

    The Receipt validator rejects ``discount > subtotal``; clamping here rather
    than trusting the draw means the factory can never construct a receipt that
    raises.
    """
    ceiling = round(max(subtotal - 0.01, 0.0), 2)
    drawn = round(subtotal * rng.uniform(*_DISCOUNT_SHARE), 2)
    return min(max(drawn, 0.0), ceiling)


def _sample_tip(rng: random.Random, taxable_base: float) -> float:
    """A tip as a share of the discounted subtotal (tips are not taxed)."""
    return round(max(taxable_base, 0.0) * rng.choice(_TIP_RATES), 2)


def _sample_tender(rng: random.Random, total: float) -> float:
    """Cash handed over: the total rounded up to a plausible note, or exact.

    Guaranteed ``>= total`` so the ``tender >= total`` invariant holds by
    construction rather than by luck.
    """
    step = rng.choice(_TENDER_STEPS)
    if step == 0:
        return round(total, 2)
    tender = float(math.ceil(total / step) * step)
    return round(max(tender, total), 2)


# --- block assembly --------------------------------------------------------


def _partition_indices(n_items: int, n_blocks: int) -> list[tuple[int, ...]]:
    """Split ``range(n_items)`` into ``n_blocks`` contiguous, disjoint chunks.

    Every index lands in exactly one chunk. When there are more blocks than
    items some chunks are empty -- an ITEMS block with nothing under it is a
    real (if unusual) layout, and dropping the block would desync the spec's
    block list from the receipt's sections.
    """
    if n_blocks <= 0:
        return []
    bounds = [i * n_items // n_blocks for i in range(n_blocks + 1)]
    return [tuple(range(bounds[i], bounds[i + 1])) for i in range(n_blocks)]


def _block_positions(blocks: Sequence[BlockType]) -> dict[BlockType, list[int]]:
    """Index every block type's positions in the stack, in order."""
    positions: dict[BlockType, list[int]] = {block_type: [] for block_type in BlockType}
    for index, block_type in enumerate(blocks):
        positions[block_type].append(index)
    return positions


def _carrier(positions: dict[BlockType, list[int]], preference: Iterable[BlockType]) -> int | None:
    """Index of the block that should carry a group of money rows.

    Money rows print under the *last* block of their preferred type (totals
    follow the final item group). The fallback chain keeps rows printable on
    layouts that lack the obvious host -- 129 of the 831 corpus layouts have no
    ITEMS block at all.
    """
    for block_type in preference:
        if positions[block_type]:
            return positions[block_type][-1]
    return None


def _logo_position(spec: LayoutSpec, header_positions: Sequence[int]) -> int | None:
    """Which HEADER block (if any) carries the logo, per ``spec.logo_placement``."""
    if not header_positions or spec.logo_placement == "NONE":
        return None
    if spec.logo_placement == "BOTTOM":
        return header_positions[-1]
    if spec.logo_placement == "MIDDLE":
        return header_positions[len(header_positions) // 2]
    return header_positions[0]


def _resolve_money_rows(
    rng: random.Random,
    faker: Faker,
    prior: Prior,
    spec: LayoutSpec,
    receipt: Receipt,
) -> list[MoneyRow]:
    """Turn ``spec.money_rows`` into labelled rows bound to the receipt's totals.

    ``ITEM`` is skipped: the item lines are carried by ``ReceiptBlock.item_indices``
    so they stay single-sourced on ``Receipt.items``.
    """
    rows: list[MoneyRow] = []
    for role in spec.money_rows:
        if role is MoneyRole.ITEM:
            continue
        label = _label_for(rng, prior, role)
        if role is MoneyRole.META:
            rows.append(MoneyRow(role=role, label=label, text=_meta_value(rng, faker, label)))
            continue
        if role is MoneyRole.AUTH:
            rows.append(MoneyRow(role=role, label=label, text=f"{rng.randrange(10**6):06d}"))
            continue
        amount = _AMOUNT_BY_ROLE[role](receipt)
        if amount is None:
            continue
        rows.append(MoneyRow(role=role, label=label, amount=amount))
    return rows


def _build_sections(
    rng: random.Random,
    faker: Faker,
    prior: Prior,
    spec: LayoutSpec,
    receipt: Receipt,
) -> tuple[ReceiptBlock, ...]:
    """Resolve a spec's block stack into concrete, renderable blocks.

    Args:
        rng: The call's seeded RNG (already past the content draws).
        faker: The call's seeded Faker.
        prior: Text banks mined from the corpus.
        spec: The layout being realised.
        receipt: A fully validated receipt carrying the final money values.

    Returns:
        One :class:`ReceiptBlock` per entry in ``spec.blocks``, same order.
    """
    resolved = _resolve_money_rows(rng, faker, prior, spec, receipt)
    ledger_rows = tuple(row for row in resolved if row.role not in _PAYMENT_ROLES)
    payment_rows = tuple(row for row in resolved if row.role in _PAYMENT_ROLES)

    positions = _block_positions(spec.blocks)
    item_positions = positions[BlockType.ITEMS]
    chunk_by_position = dict(
        zip(
            item_positions, _partition_indices(len(receipt.items), len(item_positions)), strict=True
        )
    )

    ledger_at = _carrier(positions, (BlockType.ITEMS, BlockType.PAYMENT, BlockType.META))
    payment_at = _carrier(positions, (BlockType.PAYMENT, BlockType.ITEMS, BlockType.META))
    logo_at = _logo_position(spec, positions[BlockType.HEADER])

    divider = spec.style.divider_style
    show_quantity = spec.style.quantity_column == "PRESENT"
    meta_labels = _meta_label_bank(prior)
    footer = _footer_bank(prior)

    blocks: list[ReceiptBlock] = []
    for index, block_type in enumerate(spec.blocks):
        if index == ledger_at and index == payment_at:
            rows: tuple[MoneyRow, ...] = tuple(resolved)  # keep the spec's own order
        elif index == ledger_at:
            rows = ledger_rows
        elif index == payment_at:
            rows = payment_rows
        else:
            rows = ()

        alignment = (
            spec.style.header_alignment
            if block_type is BlockType.HEADER
            else ("LEFT" if block_type in _LEFT_ALIGNED_BLOCKS else "CENTER")
        )

        extra: dict[str, Any] = {}
        if block_type is BlockType.HEADER:
            extra["business_details"] = f"{receipt.merchant}\n{receipt.address}"
            if index == logo_at:
                extra["logo_path"] = _pick_logo(rng)
        elif block_type is BlockType.ITEMS:
            extra["item_indices"] = chunk_by_position[index]
            extra["show_quantity"] = show_quantity
        elif block_type is BlockType.CUSTOM:
            extra["text"] = rng.choice(footer) if footer else ""
        elif block_type is BlockType.DATE:
            extra["text"] = _make_timestamp(rng, faker)
        elif block_type is BlockType.BARCODE:
            extra["barcode_value"] = _make_barcode(rng)
        elif block_type is BlockType.META:
            extra["left_fields"], extra["right_fields"] = _meta_columns(rng, faker, meta_labels)

        blocks.append(
            ReceiptBlock(
                type=block_type,
                alignment=alignment,
                bottom_divider=divider,
                money_rows=rows,
                **extra,
            )
        )

    return tuple(blocks)


def _meta_columns(
    rng: random.Random, faker: Faker, labels: Sequence[str]
) -> tuple[tuple[MetaField, ...], tuple[MetaField, ...]]:
    """Draw disjoint left/right metadata columns from the mined label bank."""
    if not labels:
        return (), ()
    wanted = min(rng.randint(2, 4), len(labels))
    chosen = rng.sample(list(labels), k=wanted)
    fields = tuple(MetaField(title=label, value=_meta_value(rng, faker, label)) for label in chosen)
    split = (len(fields) + 1) // 2
    return fields[:split], fields[split:]


# ---------------------------------------------------------------------------
# Public factory
# ---------------------------------------------------------------------------


def make_receipt(
    seed: int,
    template: str | None = None,
    *,
    spec: LayoutSpec | None = None,
) -> Receipt:
    """Build a Faker-driven Receipt for the given seed, template and layout.

    Determinism: ``make_receipt(seed, template, spec=s)`` is a pure function of
    its arguments, guaranteed by ``Faker.seed_instance(seed)`` + a per-call
    ``random.Random(seed)``. Different templates produce different content
    distributions because each binds a different SKU corpus and persona.

    With ``spec=None`` this is byte-for-byte the v0.2 factory: no money
    modifiers, no sections, no style. Passing a spec keeps the same merchant,
    address, items, tax rate and card digits for that seed and *adds* the money
    modifiers the spec's rows imply plus the resolved block stack.

    Args:
        seed: Reproducibility seed. Same arguments -> identical Receipt.
        template: A registered template id (see ``TEMPLATE_IDS``). May be
            omitted when ``spec`` is given, in which case one is drawn from the
            registry with the call's seed -- a spec-driven batch then varies its
            merchants and SKUs instead of being all one persona.
        spec: Layout to realise into ``Receipt.sections`` / ``Receipt.style``.

    Returns:
        A Receipt with arithmetic-consistent ``subtotal``, ``tax``, ``total``
        and, when a spec was given, ``sections`` covering every spec block.

    Raises:
        ValueError: If neither ``template`` nor ``spec`` is given, or if
            ``template`` is not in the registry.
    """
    if template is None and spec is None:
        raise ValueError(
            "make_receipt requires a template, a spec, or both; "
            f"got neither. Valid templates: {', '.join(sorted(TEMPLATE_REGISTRY))}"
        )

    rng = random.Random(seed)
    if template is None:
        template = rng.choice(TEMPLATE_IDS)

    tpl = template_spec_for(template)
    corpus = _load_sku_corpus(tpl.corpus)

    faker = Faker(tpl.locale)
    faker.seed_instance(seed)

    # Sample N line items without replacement when possible.
    n_items = rng.randint(tpl.min_items, tpl.max_items)
    pool = corpus["items"]
    sampled = rng.sample(pool, k=min(n_items, len(pool)))

    items: list[LineItem] = []
    for entry in sampled:
        lo, hi = entry["price_range"]
        unit_price = round(rng.uniform(lo, hi), 2)
        # Quantity: 1 most of the time, 2-3 occasionally — feels natural.
        qty = rng.choices([1, 2, 3], weights=[7, 2, 1], k=1)[0]
        items.append(LineItem(sku=entry["sku"], qty=qty, unit_price=unit_price))

    tax_lo, tax_hi = corpus["tax_rate_range"]
    tax_rate = round(rng.uniform(tax_lo, tax_hi), 4)

    payment_last4 = f"{rng.randint(0, 9999):04d}"

    fields: dict[str, Any] = {
        "merchant": _make_merchant(faker, tpl.merchant_style),
        "address": _make_address(faker),
        "items": items,
        "tax_rate": tax_rate,
        "payment_last4": payment_last4,
        "currency": corpus.get("currency", "USD"),
    }

    receipt = Receipt(**fields)
    if spec is None:
        return receipt

    # Modifiers are sampled in dependency order -- each step re-validates, so an
    # inconsistent combination is impossible to reach rather than merely
    # unlikely. discount -> taxable_base -> tip -> total -> tender -> change.
    requested = set(spec.money_rows)
    if MoneyRole.DISCOUNT in requested:
        fields["discount"] = _sample_discount(rng, receipt.subtotal)
        receipt = Receipt(**fields)
    if MoneyRole.TIP in requested:
        fields["tip"] = _sample_tip(rng, receipt.taxable_base)
        receipt = Receipt(**fields)
    # CHANGE cannot be printed without a tender to subtract the total from.
    if requested & {MoneyRole.TENDER, MoneyRole.CHANGE}:
        fields["tender"] = _sample_tender(rng, receipt.total)
        receipt = Receipt(**fields)

    sections = _build_sections(rng, faker, load_prior(), spec, receipt)
    return Receipt(**fields, sections=sections, style=spec.style)


def make_minimal_receipt(seed: int) -> Receipt:
    """Back-compat shim: delegates to ``make_receipt(seed, 'thermal_minimal')``.

    Kept so v0.1 callers (tests, demos, scripts) don't break when migrating to
    the Faker-driven content factory.
    """
    return make_receipt(seed=seed, template="thermal_minimal")
