"""Hardcoded `Receipt` factory for v0.1 (no Faker yet).

Just enough variation by `seed` to differentiate adjacent seeds, fully deterministic.
"""

from __future__ import annotations

from document_simulator.synthesis.receipts.schema import LineItem, Receipt

_MERCHANTS: tuple[tuple[str, str], ...] = (
    ("BLUE BOTTLE COFFEE", "315 Linden St, San Francisco CA"),
    ("GREEN GROCER MARKET", "42 Market Lane, Brooklyn NY"),
    ("RED LANTERN DINER", "8 Pine Ave, Seattle WA"),
)

# Five fixed SKUs; seed perturbs qty and unit_price deterministically.
_SKUS: tuple[tuple[str, float], ...] = (
    ("ESPRESSO", 3.25),
    ("CROISSANT", 4.10),
    ("OAT LATTE", 5.75),
    ("BAGEL+CC", 6.20),
    ("MUFFIN", 3.40),
)


def make_minimal_receipt(seed: int) -> Receipt:
    """Build a deterministic 5-line-item receipt for the given seed.

    Args:
        seed: Selector for merchant + per-line qty/price perturbation. Adjacent
            seeds produce visibly different receipts.

    Returns:
        A Receipt with 5 line items, fixed structure but seed-varying content.
    """
    merchant, address = _MERCHANTS[seed % len(_MERCHANTS)]
    items: list[LineItem] = []
    for i, (sku, base_price) in enumerate(_SKUS):
        qty = 1 + ((seed + i) % 3)  # 1..3
        # Cents perturbation that depends on both seed and line index, kept >0
        price_cents = int(base_price * 100) + ((seed * 7 + i * 13) % 50)
        items.append(LineItem(sku=sku, qty=qty, unit_price=price_cents / 100))

    tax_rate = 0.06 + ((seed % 4) * 0.005)  # 0.060..0.075
    payment_last4 = f"{(1234 + seed * 31) % 10000:04d}"

    return Receipt(
        merchant=merchant,
        address=address,
        items=items,
        tax_rate=round(tax_rate, 4),
        payment_last4=payment_last4,
    )
