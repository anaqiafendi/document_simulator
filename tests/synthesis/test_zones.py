"""Unit tests for synthesis configuration models (zones.py)."""

import json

import pytest

from document_simulator.synthesis.zones import (
    FieldTypeConfig,
    GeneratorConfig,
    RespondentConfig,
    SynthesisConfig,
    ZoneConfig,
)


# ---------------------------------------------------------------------------
# FieldTypeConfig
# ---------------------------------------------------------------------------


def test_field_type_config_defaults():
    ft = FieldTypeConfig(field_type_id="standard", display_name="Standard text")
    assert ft.font_family == "sans-serif"
    assert ft.font_color == "#000000"
    assert ft.fill_style == "typed"
    assert ft.bold is False
    assert ft.italic is False
    assert ft.jitter_x == 0.0
    assert ft.baseline_wander == 0.0


def test_field_type_config_custom():
    ft = FieldTypeConfig(
        field_type_id="signature",
        display_name="Signature",
        font_family="handwriting",
        font_size_range=(16, 22),
        font_color="#00008B",
        bold=True,
        fill_style="handwritten-font",
        jitter_x=0.05,
        baseline_wander=0.2,
    )
    assert ft.font_family == "handwriting"
    assert ft.font_color == "#00008B"
    assert ft.bold is True
    assert ft.fill_style == "handwritten-font"
    assert ft.font_size_range == (16, 22)


# ---------------------------------------------------------------------------
# RespondentConfig
# ---------------------------------------------------------------------------


def test_respondent_config_requires_field_types():
    ft = FieldTypeConfig(field_type_id="standard", display_name="Standard")
    r = RespondentConfig(respondent_id="person_a", display_name="Person A", field_types=[ft])
    assert r.respondent_id == "person_a"
    assert len(r.field_types) == 1


def test_respondent_config_get_field_type_found():
    ft_std = FieldTypeConfig(field_type_id="standard", display_name="Standard")
    ft_sig = FieldTypeConfig(field_type_id="signature", display_name="Signature")
    r = RespondentConfig(
        respondent_id="person_a", display_name="Person A", field_types=[ft_std, ft_sig]
    )
    assert r.get_field_type("signature") is ft_sig


def test_respondent_config_get_field_type_missing_raises():
    ft = FieldTypeConfig(field_type_id="standard", display_name="Standard")
    r = RespondentConfig(respondent_id="person_a", display_name="Person A", field_types=[ft])
    with pytest.raises(KeyError):
        r.get_field_type("nonexistent")


def test_respondent_config_default_field_type_is_first():
    ft_std = FieldTypeConfig(field_type_id="standard", display_name="Standard")
    ft_sig = FieldTypeConfig(field_type_id="signature", display_name="Signature")
    r = RespondentConfig(
        respondent_id="person_a", display_name="Person A", field_types=[ft_std, ft_sig]
    )
    assert r.default_field_type is ft_std


# ---------------------------------------------------------------------------
# ZoneConfig
# ---------------------------------------------------------------------------


def test_zone_config_defaults():
    z = ZoneConfig(
        zone_id="z1",
        label="first_name",
        box=[[10, 20], [200, 20], [200, 50], [10, 50]],
        faker_provider="first_name",
    )
    assert z.respondent_id == "default"
    assert z.field_type_id == "standard"
    assert z.alignment == "left"
    assert z.custom_values == []


def test_zone_config_with_respondent_and_field_type():
    z = ZoneConfig(
        zone_id="z2",
        label="signature",
        box=[[10, 100], [200, 100], [200, 140], [10, 140]],
        faker_provider="name",
        respondent_id="person_a",
        field_type_id="signature",
    )
    assert z.respondent_id == "person_a"
    assert z.field_type_id == "signature"


def test_zone_config_custom_values_override():
    z = ZoneConfig(
        zone_id="z3",
        label="status",
        box=[[0, 0], [100, 0], [100, 30], [0, 30]],
        faker_provider="name",
        custom_values=["APPROVED", "PENDING", "REJECTED"],
    )
    assert "APPROVED" in z.custom_values


# ---------------------------------------------------------------------------
# GeneratorConfig
# ---------------------------------------------------------------------------


def test_generator_config_defaults():
    from document_simulator.synthesis.zones import GeneratorConfig

    gc = GeneratorConfig()
    assert gc.n == 1
    assert gc.seed == 42
    assert gc.output_dir == "output"


# ---------------------------------------------------------------------------
# SynthesisConfig — round-trip JSON serialisation (AC-7)
# ---------------------------------------------------------------------------


def _make_synthesis_config() -> SynthesisConfig:
    ft_std = FieldTypeConfig(field_type_id="standard", display_name="Standard")
    ft_sig = FieldTypeConfig(
        field_type_id="signature",
        display_name="Signature",
        font_family="handwriting",
        font_size_range=(16, 22),
        font_color="#00008B",
        bold=True,
        fill_style="handwritten-font",
    )
    respondent_a = RespondentConfig(
        respondent_id="person_a", display_name="Person A", field_types=[ft_std, ft_sig]
    )
    respondent_b = RespondentConfig(
        respondent_id="person_b",
        display_name="Person B",
        field_types=[FieldTypeConfig(field_type_id="standard", display_name="Standard")],
    )
    zones = [
        ZoneConfig(
            zone_id="z1",
            label="first_name",
            box=[[10, 20], [200, 20], [200, 50], [10, 50]],
            faker_provider="first_name",
            respondent_id="person_a",
            field_type_id="standard",
        ),
        ZoneConfig(
            zone_id="z2",
            label="signature",
            box=[[10, 100], [300, 100], [300, 140], [10, 140]],
            faker_provider="name",
            respondent_id="person_a",
            field_type_id="signature",
        ),
    ]
    return SynthesisConfig(respondents=[respondent_a, respondent_b], zones=zones)


def test_synthesis_config_json_roundtrip():
    config = _make_synthesis_config()
    json_str = config.model_dump_json()
    restored = SynthesisConfig.model_validate_json(json_str)
    assert len(restored.respondents) == 2
    assert len(restored.zones) == 2
    assert restored.zones[0].label == "first_name"
    assert restored.respondents[0].field_types[1].font_color == "#00008B"


def test_synthesis_config_get_respondent_found():
    config = _make_synthesis_config()
    r = config.get_respondent("person_a")
    assert r.display_name == "Person A"


def test_synthesis_config_get_respondent_missing_raises():
    config = _make_synthesis_config()
    with pytest.raises(KeyError):
        config.get_respondent("nobody")


def test_synthesis_config_default_respondent_exists_when_no_respondents_provided():
    """SynthesisConfig with no respondents creates a default respondent automatically."""
    zones = [
        ZoneConfig(
            zone_id="z1",
            label="name",
            box=[[0, 0], [100, 0], [100, 30], [0, 30]],
            faker_provider="name",
        )
    ]
    config = SynthesisConfig(zones=zones)
    # No respondents provided → validator inserts one named "default"
    r = config.get_respondent("default")
    assert r is not None
    assert r.get_field_type("standard") is not None


def test_synthesis_config_explicit_respondents_not_augmented():
    """If respondents are provided, no extra 'default' respondent is injected."""
    config = _make_synthesis_config()
    assert len(config.respondents) == 2
