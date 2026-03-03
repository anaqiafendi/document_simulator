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
