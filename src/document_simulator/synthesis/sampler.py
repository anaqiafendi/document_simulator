"""ZoneDataSampler and generate_respondent — Faker-based text generation per zone."""

from __future__ import annotations

import random
from typing import Callable

from faker import Faker

from document_simulator.synthesis.zones import ZoneConfig

# Providers that are drawn directly from the pre-generated respondent identity dict
# rather than from a fresh Faker call.
_IDENTITY_PROVIDERS = {
    "full_name", "first_name", "last_name", "initials", "address", "ssn",
    "signature",  # handwriting-style name — same value as full_name per respondent
}

# Static providers that return a fixed value regardless of Faker seed.
_STATIC_PROVIDERS: dict[str, str] = {
    "checkbox_checked": "☑",
    "checkbox_unchecked": "☐",
    "checkbox_x": "☒",
}

# Custom providers: called with a seeded Faker instance, return a string.
_CustomFn = Callable[[Faker], str]

_CUSTOM_PROVIDERS: dict[str, _CustomFn] = {
    # ── Prices ───────────────────────────────────────────────────────────────
    "price_short": lambda f: f"${f.random_int(1, 99)}.{f.random_int(0, 99):02d}",
    "price_medium": lambda f: f"${f.random_int(100, 9_999):,}.{f.random_int(0, 99):02d}",
    "price_large": lambda f: f"${f.random_int(10_000, 999_999):,}.{f.random_int(0, 99):02d}",
    # ── Numbers ──────────────────────────────────────────────────────────────
    "number_short": lambda f: f.numerify("####"),           # 4 digits
    "number_medium": lambda f: f.numerify("#######"),       # 7 digits
    "number_long": lambda f: f.numerify("############"),    # 12 digits
    # ── Dates ────────────────────────────────────────────────────────────────
    "date_numeric": lambda f: f.date(pattern="%m/%d/%Y"),
    "date_written": lambda f: f.date_object().strftime("%B %d, %Y"),
    "signing_date": lambda f: f.date_this_decade().strftime("%B %d, %Y"),
    "effective_date": lambda f: f.date_this_decade().strftime("%B %d, %Y"),
    "termination_date": lambda f: f.future_date(end_date="+3y").strftime("%B %d, %Y"),
    # ── Address ──────────────────────────────────────────────────────────────
    "address_single_line": lambda f: f.address().replace("\n", ", "),
}


def generate_respondent(group_id: str, global_seed: int) -> dict[str, str]:
    """Generate a correlated set of identity fields for one respondent.

    All fields come from the same seeded Faker instance, called in a fixed
    order so the result is reproducible given the same ``global_seed`` and
    ``group_id``.
    """
    fake = Faker("en_US")
    fake.seed_instance(hash((global_seed, group_id)) & 0xFFFFFFFF)
    first = fake.first_name()
    last = fake.last_name()
    full = f"{first} {last}"
    return {
        "first_name": first,
        "last_name": last,
        "full_name": full,
        "initials": f"{first[0].upper()}.{last[0].upper()}.",
        "address": fake.street_address(),
        "ssn": fake.ssn(),
        "signature": full,  # same as full_name — rendered with handwriting font
    }


class ZoneDataSampler:
    """Sample text for a zone using its configured Faker provider."""

    @staticmethod
    def sample(zone: ZoneConfig, identity: dict[str, str], seed: int) -> str:
        """Return a text string for *zone*.

        Priority:
        1. ``custom_values`` pool — if non-empty, pick randomly from the pool.
        2. Static providers — fixed Unicode values (checkbox symbols).
        3. Identity fields — pre-generated correlated respondent fields.
        4. Custom providers — seeded lambda functions for prices, dates, etc.
        5. Fresh Faker method call by name — for all other providers.
        """
        if zone.custom_values:
            rng = random.Random(seed)
            return rng.choice(zone.custom_values)

        provider = zone.faker_provider

        if provider in _STATIC_PROVIDERS:
            return _STATIC_PROVIDERS[provider]

        if provider in _IDENTITY_PROVIDERS:
            return identity[provider]

        # Custom seeded providers (prices, numbers, dates, address)
        if provider in _CUSTOM_PROVIDERS:
            fake = Faker("en_US")
            fake.seed_instance(hash((seed, zone.zone_id)) & 0xFFFFFFFF)
            return _CUSTOM_PROVIDERS[provider](fake)

        # Fresh Faker call for standard providers (name, email, phone, etc.)
        fake = Faker("en_US")
        fake.seed_instance(hash((seed, zone.zone_id)) & 0xFFFFFFFF)
        try:
            return str(getattr(fake, provider)())
        except AttributeError:
            # Fallback: prefix-encoded patterns like "bothify:??####"
            if provider.startswith("bothify:"):
                return fake.bothify(provider.split(":", 1)[1])
            if provider.startswith("numerify:"):
                return fake.numerify(provider.split(":", 1)[1])
            return fake.word()
