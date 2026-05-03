"""Faker-driven `Receipt` content factory (FDD #28, v0.2).

Public API:
    make_receipt(seed, template) -> Receipt
        Faker-backed, locale-aware, arithmetic-consistent receipt for a given template.
    make_minimal_receipt(seed) -> Receipt
        Back-compat wrapper -> make_receipt(seed, "thermal_minimal").

Each template binds to a specific SKU corpus (small JSON files bundled in
``sku_corpora/``) and a content distribution (number of line items, presence of
tip lines, etc.). Output is fully deterministic for a fixed (seed, template)
pair: Faker is seeded per call via ``Faker.seed_instance(seed)`` and a private
``random.Random(seed)`` is used for any non-Faker numeric draws.
"""

from __future__ import annotations

import json
import random
from functools import cache
from importlib.resources import files
from typing import Any, Final

from faker import Faker

from document_simulator.synthesis.receipts.schema import LineItem, Receipt

# ---------------------------------------------------------------------------
# Template registry — each template binds a SKU corpus, locale, and item-count
# distribution. Adding a new template == adding an entry here + a Jinja2 file.
# ---------------------------------------------------------------------------

_TEMPLATE_REGISTRY: Final[dict[str, dict[str, Any]]] = {
    "thermal_minimal": {
        "corpus": "grocery",
        "locale": "en_US",
        "min_items": 3,
        "max_items": 8,
        "merchant_style": "grocery",
    },
    "restaurant_tip": {
        "corpus": "restaurant",
        "locale": "en_US",
        "min_items": 2,
        "max_items": 6,
        "merchant_style": "restaurant",
    },
    "retail_multicol": {
        "corpus": "grocery",
        "locale": "en_US",
        "min_items": 5,
        "max_items": 10,
        "merchant_style": "retail",
    },
    "a4_invoice": {
        "corpus": "restaurant",
        "locale": "en_US",
        "min_items": 3,
        "max_items": 7,
        "merchant_style": "company",
    },
    "taxi_stub": {
        "corpus": "services",
        "locale": "en_US",
        "min_items": 3,
        "max_items": 5,
        "merchant_style": "taxi",
    },
}


# ---------------------------------------------------------------------------
# SKU corpus loader — cached at module level so repeated `make_receipt` calls
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
# Per-style merchant generators — wrap Faker with style-specific suffixes so a
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
# Public factory
# ---------------------------------------------------------------------------


def make_receipt(seed: int, template: str) -> Receipt:
    """Build a Faker-driven Receipt for the given seed and template.

    Determinism: ``make_receipt(seed, template) == make_receipt(seed, template)``
    is guaranteed by ``Faker.seed_instance(seed)`` + a per-call
    ``random.Random(seed)``. Different templates produce different content
    distributions because each binds a different SKU corpus and persona.

    Args:
        seed: Reproducibility seed. Same seed + template -> identical Receipt.
        template: One of the registered template names. Currently:
            ``thermal_minimal``, ``restaurant_tip``, ``retail_multicol``,
            ``a4_invoice``, ``taxi_stub``.

    Returns:
        A Receipt with arithmetic-consistent ``subtotal``, ``tax``, ``total``.

    Raises:
        ValueError: If ``template`` is not in the registry.
    """
    if template not in _TEMPLATE_REGISTRY:
        valid = ", ".join(sorted(_TEMPLATE_REGISTRY))
        raise ValueError(f"Unknown template {template!r}. Valid templates: {valid}")

    spec = _TEMPLATE_REGISTRY[template]
    corpus = _load_sku_corpus(spec["corpus"])

    rng = random.Random(seed)
    faker = Faker(spec["locale"])
    faker.seed_instance(seed)

    # Sample N line items without replacement when possible.
    min_items, max_items = spec["min_items"], spec["max_items"]
    n_items = rng.randint(min_items, max_items)
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

    return Receipt(
        merchant=_make_merchant(faker, spec["merchant_style"]),
        address=_make_address(faker),
        items=items,
        tax_rate=tax_rate,
        payment_last4=payment_last4,
    )


def make_minimal_receipt(seed: int) -> Receipt:
    """Back-compat shim: delegates to ``make_receipt(seed, 'thermal_minimal')``.

    Kept so v0.1 callers (tests, demos, scripts) don't break when migrating to
    the Faker-driven content factory.
    """
    return make_receipt(seed=seed, template="thermal_minimal")
