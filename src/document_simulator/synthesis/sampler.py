"""ZoneDataSampler and generate_respondent — Faker-based text generation per zone.

Supports per-zone locale and currency overrides so a multi-lingual,
multi-currency receipt (e.g. USD line items / CAD total) round-trips
faithfully when regenerated.
"""

from __future__ import annotations

import random
from collections.abc import Callable

from faker import Faker

from document_simulator.synthesis.field_schema import (
    _CURRENCY_INFO,
    format_currency,
    to_faker_locale,
)
from document_simulator.synthesis.zones import ZoneConfig

# Providers drawn from the pre-generated respondent identity dict
_IDENTITY_PROVIDERS = {
    "full_name", "first_name", "last_name", "initials", "address", "ssn",
    "signature",
}

# Static providers — fixed values regardless of Faker seed.
_STATIC_PROVIDERS: dict[str, str] = {
    "checkbox_checked": "☑",
    "checkbox_unchecked": "☐",
    "checkbox_x": "☒",
}

# Custom providers are called with a seeded Faker instance + an optional
# currency override (ISO 4217).
_CustomFn = Callable[[Faker, str | None], str]


def _price_short(f: Faker, currency: str | None) -> str:
    amount = f.random_int(1, 99) + f.random_int(0, 99) / 100
    return format_currency(amount, currency)


def _price_medium(f: Faker, currency: str | None) -> str:
    amount = f.random_int(100, 9_999) + f.random_int(0, 99) / 100
    return format_currency(amount, currency)


def _price_large(f: Faker, currency: str | None) -> str:
    amount = f.random_int(10_000, 999_999) + f.random_int(0, 99) / 100
    return format_currency(amount, currency)


def _pricetag(f: Faker, currency: str | None) -> str:
    # Convenience alias the LLM often emits ("pricetag").
    amount = f.random_int(1, 9_999) + f.random_int(0, 99) / 100
    return format_currency(amount, currency)


_CUSTOM_PROVIDERS: dict[str, _CustomFn] = {
    # ── Prices (currency-aware) ──────────────────────────────────────────────
    "price_short": _price_short,
    "price_medium": _price_medium,
    "price_large": _price_large,
    "pricetag": _pricetag,
    "amount": _pricetag,
    # ── Numbers ──────────────────────────────────────────────────────────────
    "number_short": lambda f, _c: f.numerify("####"),
    "number_medium": lambda f, _c: f.numerify("#######"),
    "number_long": lambda f, _c: f.numerify("############"),
    # ── Dates ────────────────────────────────────────────────────────────────
    "date_numeric": lambda f, _c: f.date(pattern="%m/%d/%Y"),
    "date_written": lambda f, _c: f.date_object().strftime("%B %d, %Y"),
    "signing_date": lambda f, _c: f.date_this_decade().strftime("%B %d, %Y"),
    "effective_date": lambda f, _c: f.date_this_decade().strftime("%B %d, %Y"),
    "termination_date": lambda f, _c: f.future_date(end_date="+3y").strftime("%B %d, %Y"),
    # ── Address ──────────────────────────────────────────────────────────────
    "address_single_line": lambda f, _c: f.address().replace("\n", ", "),
}


# Standard Faker methods we surface in the UI dropdown.  Grouped so the UI can
# render them under collapsible headings.  The actual Faker library has ~250
# methods — this is the curated subset relevant to document fields.
_FAKER_STANDARD_GROUPS: dict[str, list[str]] = {
    "person": [
        "name", "first_name", "last_name", "prefix", "suffix",
        "name_male", "name_female",
    ],
    "contact": [
        "email", "safe_email", "company_email", "free_email",
        "phone_number", "msisdn",
    ],
    "address": [
        "address", "street_address", "city", "state", "country",
        "country_code", "postcode", "zipcode",
    ],
    "company": [
        "company", "company_suffix", "bs", "catch_phrase", "job",
    ],
    "date_time": [
        "date", "date_of_birth", "date_this_century", "date_this_decade",
        "date_this_year", "date_this_month", "future_date", "past_date",
        "time", "day_of_month", "day_of_week", "month_name", "year",
    ],
    "finance": [
        "credit_card_number", "credit_card_expire", "credit_card_provider",
        "iban", "bban", "swift", "currency_code", "currency_name",
    ],
    "identifiers": [
        "uuid4", "ssn", "license_plate", "ean13",
    ],
    "text": [
        "word", "sentence", "paragraph", "text", "words", "sentences",
    ],
    "internet": [
        "url", "domain_name", "user_name", "ipv4", "ipv6",
    ],
}


def list_faker_providers() -> dict[str, list[dict[str, str]]]:
    """Enumerate every provider supported by :class:`ZoneDataSampler`.

    Returns a dict of ``category → [{name, label, description}]`` suitable for
    rendering in a grouped dropdown.  Used by the
    ``GET /api/synthesis/faker-providers`` endpoint.
    """
    catalog: dict[str, list[dict[str, str]]] = {
        "identity": [
            {"name": n, "label": n.replace("_", " ").title(), "description": "Respondent identity — correlated across zones."}
            for n in sorted(_IDENTITY_PROVIDERS)
        ],
        "static": [
            {"name": n, "label": n.replace("_", " ").title(), "description": f"Static: {v}"}
            for n, v in _STATIC_PROVIDERS.items()
        ],
        "custom": [
            {"name": n, "label": n.replace("_", " ").title(), "description": "Seeded custom provider (currency / locale aware)."}
            for n in _CUSTOM_PROVIDERS
        ],
    }
    for group_name, names in _FAKER_STANDARD_GROUPS.items():
        catalog[group_name] = [
            {"name": n, "label": n.replace("_", " ").title(), "description": f"Faker.{n}()"}
            for n in names
        ]
    return catalog


def list_currency_codes() -> list[dict[str, str]]:
    """Return the list of ISO 4217 currencies the sampler knows about."""
    return [
        {"code": code, "symbol": symbol}
        for code, (symbol, _places) in _CURRENCY_INFO.items()
    ]


def generate_respondent(
    group_id: str,
    global_seed: int,
    locale: str = "en_US",
) -> dict[str, str]:
    """Generate a correlated identity for one respondent group.

    Args:
        group_id: Logical group name (e.g. ``"respondent_a"``).
        global_seed: Seed shared across all respondents in a batch.
        locale: Faker locale (``"en_US"`` / ``"fr_FR"`` / …). Drives the
            language/format of names and addresses.
    """
    fake = Faker(locale)
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
        "signature": full,
    }


class ZoneDataSampler:
    """Sample text for a zone using its configured Faker provider.

    Locale and currency can be specified per-zone via optional attributes on
    ``ZoneConfig`` (``language`` / ``currency``). When absent, sampling falls
    back to ``en_US`` / ``USD`` so existing callers keep working unchanged.
    """

    @staticmethod
    def sample(
        zone: ZoneConfig,
        identity: dict[str, str],
        seed: int,
        locale: str | None = None,
        currency: str | None = None,
    ) -> str:
        """Return a generated string for *zone*.

        Priority of the generated value:

        1. ``zone.custom_values`` — pick deterministically from the pool.
        2. Static providers (checkbox symbols, …).
        3. Identity providers (respondent name / address / …).
        4. Custom providers (prices, dates) — currency-aware.
        5. Standard Faker provider called by name (locale-aware).
        """
        if zone.custom_values:
            rng = random.Random(seed)
            return rng.choice(zone.custom_values)

        provider = zone.faker_provider

        if provider in _STATIC_PROVIDERS:
            return _STATIC_PROVIDERS[provider]

        if provider in _IDENTITY_PROVIDERS:
            return identity[provider]

        # Resolve effective locale + currency, preferring explicit arguments,
        # then zone-level hints, then defaults.
        zone_lang = getattr(zone, "language", None)
        zone_currency = getattr(zone, "currency", None)
        effective_locale = locale or to_faker_locale(zone_lang)
        effective_currency = currency or zone_currency or "USD"

        if provider in _CUSTOM_PROVIDERS:
            fake = Faker(effective_locale)
            fake.seed_instance(hash((seed, zone.zone_id)) & 0xFFFFFFFF)
            return _CUSTOM_PROVIDERS[provider](fake, effective_currency)

        fake = Faker(effective_locale)
        fake.seed_instance(hash((seed, zone.zone_id)) & 0xFFFFFFFF)
        try:
            return str(getattr(fake, provider)())
        except AttributeError:
            if provider.startswith("bothify:"):
                return fake.bothify(provider.split(":", 1)[1])
            if provider.startswith("numerify:"):
                return fake.numerify(provider.split(":", 1)[1])
            return fake.word()


__all__ = [
    "ZoneDataSampler",
    "generate_respondent",
    "list_faker_providers",
    "list_currency_codes",
]
