"""ZoneDataSampler and generate_respondent — Faker-based text generation per zone."""

from __future__ import annotations

import random

from faker import Faker

from document_simulator.synthesis.zones import ZoneConfig

# Providers that are drawn directly from the pre-generated respondent identity dict
# rather than from a fresh Faker call.
_IDENTITY_PROVIDERS = {"full_name", "first_name", "last_name", "initials", "address", "ssn"}


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
    return {
        "first_name": first,
        "last_name": last,
        "full_name": f"{first} {last}",
        "initials": f"{first[0].upper()}.{last[0].upper()}.",
        "address": fake.address(),
        "ssn": fake.ssn(),
    }


class ZoneDataSampler:
    """Sample text for a zone using its configured Faker provider."""

    @staticmethod
    def sample(zone: ZoneConfig, identity: dict[str, str], seed: int) -> str:
        """Return a text string for *zone*.

        Priority:
        1. ``custom_values`` pool — if non-empty, pick randomly from the pool.
        2. Identity fields — if ``faker_provider`` matches a pre-generated key.
        3. Fresh Faker call — for all other providers.
        """
        if zone.custom_values:
            rng = random.Random(seed)
            return rng.choice(zone.custom_values)

        provider = zone.faker_provider

        if provider in _IDENTITY_PROVIDERS:
            return identity[provider]

        # Fresh Faker call for standard providers (name, date, phone, etc.)
        fake = Faker("en_US")
        fake.seed_instance(hash((seed, zone.zone_id)) & 0xFFFFFFFF)
        try:
            return str(getattr(fake, provider)())
        except AttributeError:
            # Fallback: use numerify for custom patterns like "bothify:??####"
            if provider.startswith("bothify:"):
                return fake.bothify(provider.split(":", 1)[1])
            if provider.startswith("numerify:"):
                return fake.numerify(provider.split(":", 1)[1])
            return fake.word()
