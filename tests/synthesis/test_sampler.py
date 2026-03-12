"""Unit tests for ZoneDataSampler and generate_respondent (sampler.py)."""

import pytest

from document_simulator.synthesis.sampler import ZoneDataSampler, generate_respondent
from document_simulator.synthesis.zones import ZoneConfig


# ---------------------------------------------------------------------------
# generate_respondent
# ---------------------------------------------------------------------------


def test_generate_respondent_returns_required_keys():
    identity = generate_respondent("person_a", global_seed=42)
    for key in ("first_name", "last_name", "full_name", "initials", "address"):
        assert key in identity


def test_generate_respondent_full_name_matches_parts():
    identity = generate_respondent("person_a", global_seed=42)
    assert identity["first_name"] in identity["full_name"]
    assert identity["last_name"] in identity["full_name"]


def test_generate_respondent_initials_derived():
    identity = generate_respondent("person_a", global_seed=42)
    expected_first = identity["first_name"][0].upper()
    expected_last = identity["last_name"][0].upper()
    assert expected_first in identity["initials"]
    assert expected_last in identity["initials"]


def test_generate_respondent_deterministic_with_same_seed():
    a = generate_respondent("person_a", global_seed=99)
    b = generate_respondent("person_a", global_seed=99)
    assert a == b


def test_generate_respondent_different_groups_produce_different_data():
    a = generate_respondent("person_a", global_seed=42)
    b = generate_respondent("person_b", global_seed=42)
    # Names should differ (may occasionally collide, but extremely unlikely)
    assert a["full_name"] != b["full_name"] or a["address"] != b["address"]


def test_generate_respondent_different_seeds_produce_different_data():
    a = generate_respondent("person_a", global_seed=1)
    b = generate_respondent("person_a", global_seed=2)
    assert a["full_name"] != b["full_name"] or a["address"] != b["address"]


# ---------------------------------------------------------------------------
# ZoneDataSampler
# ---------------------------------------------------------------------------


def _make_zone(provider: str, custom_values: list[str] | None = None) -> ZoneConfig:
    return ZoneConfig(
        zone_id="z1",
        label="test",
        box=[[0, 0], [100, 0], [100, 30], [0, 30]],
        faker_provider=provider,
        custom_values=custom_values or [],
    )


def test_zone_data_sampler_name_provider_returns_string():
    zone = _make_zone("name")
    identity = generate_respondent("default", global_seed=42)
    text = ZoneDataSampler.sample(zone, identity, seed=42)
    assert isinstance(text, str)
    assert len(text) > 0


def test_zone_data_sampler_custom_values_override_faker():
    zone = _make_zone("name", custom_values=["FIXED_VALUE"])
    identity = generate_respondent("default", global_seed=42)
    text = ZoneDataSampler.sample(zone, identity, seed=42)
    assert text == "FIXED_VALUE"


def test_zone_data_sampler_custom_values_pool_sampled():
    pool = ["A", "B", "C"]
    zone = _make_zone("name", custom_values=pool)
    identity = generate_respondent("default", global_seed=42)
    results = {ZoneDataSampler.sample(zone, identity, seed=i) for i in range(20)}
    assert results.issubset(set(pool))


def test_zone_data_sampler_first_name_provider():
    zone = _make_zone("first_name")
    identity = generate_respondent("default", global_seed=10)
    text = ZoneDataSampler.sample(zone, identity, seed=10)
    assert isinstance(text, str)
    assert len(text) > 0


def test_zone_data_sampler_full_name_uses_respondent_identity():
    zone = _make_zone("full_name")
    identity = generate_respondent("person_a", global_seed=42)
    text = ZoneDataSampler.sample(zone, identity, seed=42)
    assert text == identity["full_name"]


def test_zone_data_sampler_initials_uses_respondent_identity():
    zone = _make_zone("initials")
    identity = generate_respondent("person_a", global_seed=42)
    text = ZoneDataSampler.sample(zone, identity, seed=42)
    assert text == identity["initials"]


# ---------------------------------------------------------------------------
# New field types — prices, numbers, dates, address, signature, checkbox
# ---------------------------------------------------------------------------

import re

@pytest.mark.parametrize("provider", ["price_short", "price_medium", "price_large"])
def test_price_providers_return_currency_string(provider):
    zone = _make_zone(provider)
    identity = generate_respondent("default", global_seed=1)
    text = ZoneDataSampler.sample(zone, identity, seed=1)
    assert isinstance(text, str) and len(text) > 0
    assert "$" in text
    assert any(c.isdigit() for c in text)


@pytest.mark.parametrize("provider,min_len,max_len", [
    ("number_short", 3, 5),
    ("number_medium", 6, 9),
    ("number_long", 10, 14),
])
def test_number_providers_return_expected_length(provider, min_len, max_len):
    zone = _make_zone(provider)
    identity = generate_respondent("default", global_seed=7)
    text = ZoneDataSampler.sample(zone, identity, seed=7)
    assert text.isdigit()
    assert min_len <= len(text) <= max_len


def test_date_numeric_format():
    zone = _make_zone("date_numeric")
    identity = generate_respondent("default", global_seed=3)
    text = ZoneDataSampler.sample(zone, identity, seed=3)
    # Expect MM/DD/YYYY
    assert re.match(r"\d{2}/\d{2}/\d{4}", text), f"Unexpected format: {text!r}"


@pytest.mark.parametrize("provider", ["date_written", "signing_date", "effective_date", "termination_date"])
def test_written_date_providers_return_month_and_year(provider):
    zone = _make_zone(provider)
    identity = generate_respondent("default", global_seed=5)
    text = ZoneDataSampler.sample(zone, identity, seed=5)
    assert isinstance(text, str) and len(text) > 6
    # Should contain a 4-digit year
    assert re.search(r"\d{4}", text), f"No year in: {text!r}"


def test_address_single_line_has_comma():
    zone = _make_zone("address_single_line")
    identity = generate_respondent("default", global_seed=9)
    text = ZoneDataSampler.sample(zone, identity, seed=9)
    assert "," in text
    assert len(text) > 10


def test_signature_uses_respondent_identity():
    zone = _make_zone("signature")
    identity = generate_respondent("person_a", global_seed=42)
    text = ZoneDataSampler.sample(zone, identity, seed=42)
    assert text == identity["signature"]
    assert text == identity["full_name"]


@pytest.mark.parametrize("provider,expected", [
    ("checkbox_checked", "☑"),
    ("checkbox_unchecked", "☐"),
    ("checkbox_x", "☒"),
])
def test_checkbox_providers_return_unicode_symbol(provider, expected):
    zone = _make_zone(provider)
    identity = generate_respondent("default", global_seed=1)
    text = ZoneDataSampler.sample(zone, identity, seed=1)
    assert text == expected


def test_checkbox_providers_ignore_seed_variation():
    """Checkbox values must be static regardless of seed."""
    zone = _make_zone("checkbox_checked")
    identity = generate_respondent("default", global_seed=1)
    results = {ZoneDataSampler.sample(zone, identity, seed=s) for s in range(10)}
    assert results == {"☑"}


def test_generate_respondent_includes_signature():
    identity = generate_respondent("person_a", global_seed=42)
    assert "signature" in identity
    assert identity["signature"] == identity["full_name"]
