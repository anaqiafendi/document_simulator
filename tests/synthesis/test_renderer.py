"""Unit tests for StyleResolver and ZoneRenderer (renderer.py)."""

import numpy as np
import pytest
from PIL import Image

from document_simulator.synthesis.renderer import ResolvedStyle, StyleResolver, ZoneRenderer
from document_simulator.synthesis.zones import FieldTypeConfig, RespondentConfig, SynthesisConfig, ZoneConfig


def _make_config_with_two_field_types() -> SynthesisConfig:
    ft_std = FieldTypeConfig(
        field_type_id="standard",
        display_name="Standard",
        font_color="#000000",
        font_size_range=(10, 12),
        fill_style="typed",
    )
    ft_sig = FieldTypeConfig(
        field_type_id="signature",
        display_name="Signature",
        font_color="#00008B",
        font_size_range=(18, 22),
        fill_style="handwritten-font",
        bold=True,
    )
    respondent = RespondentConfig(
        respondent_id="person_a", display_name="Person A", field_types=[ft_std, ft_sig]
    )
    zones = [
        ZoneConfig(
            zone_id="z1",
            label="name",
            box=[[10, 10], [200, 10], [200, 40], [10, 40]],
            faker_provider="name",
            respondent_id="person_a",
            field_type_id="standard",
        ),
        ZoneConfig(
            zone_id="z2",
            label="sig",
            box=[[10, 60], [200, 60], [200, 90], [10, 90]],
            faker_provider="name",
            respondent_id="person_a",
            field_type_id="signature",
        ),
    ]
    return SynthesisConfig(respondents=[respondent], zones=zones)


# ---------------------------------------------------------------------------
# StyleResolver
# ---------------------------------------------------------------------------


def test_style_resolver_returns_resolved_style():
    config = _make_config_with_two_field_types()
    resolver = StyleResolver(config, seed=42)
    style = resolver.resolve("person_a", "standard")
    assert isinstance(style, ResolvedStyle)


def test_style_resolver_color_matches_field_type():
    config = _make_config_with_two_field_types()
    resolver = StyleResolver(config, seed=42)
    std_style = resolver.resolve("person_a", "standard")
    sig_style = resolver.resolve("person_a", "signature")
    assert std_style.font_color == "#000000"
    assert sig_style.font_color == "#00008B"


def test_style_resolver_fill_style_matches_field_type():
    config = _make_config_with_two_field_types()
    resolver = StyleResolver(config, seed=42)
    std_style = resolver.resolve("person_a", "standard")
    sig_style = resolver.resolve("person_a", "signature")
    assert std_style.fill_style == "typed"
    assert sig_style.fill_style == "handwritten-font"


def test_style_resolver_size_within_range():
    config = _make_config_with_two_field_types()
    resolver = StyleResolver(config, seed=42)
    std_style = resolver.resolve("person_a", "standard")
    sig_style = resolver.resolve("person_a", "signature")
    assert 10 <= std_style.font_size <= 12
    assert 18 <= sig_style.font_size <= 22


def test_style_resolver_caches_same_size_per_field_type(monkeypatch):
    """Same (respondent, field_type) must return identical size within one resolver instance."""
    config = _make_config_with_two_field_types()
    resolver = StyleResolver(config, seed=42)
    style_a = resolver.resolve("person_a", "standard")
    style_b = resolver.resolve("person_a", "standard")
    assert style_a.font_size == style_b.font_size


def test_style_resolver_different_field_types_may_differ():
    config = _make_config_with_two_field_types()
    resolver = StyleResolver(config, seed=42)
    std_style = resolver.resolve("person_a", "standard")
    sig_style = resolver.resolve("person_a", "signature")
    # Colors and fill styles are definitely different
    assert std_style.font_color != sig_style.font_color


# ---------------------------------------------------------------------------
# ZoneRenderer
# ---------------------------------------------------------------------------


def _blank_canvas(w: int = 400, h: int = 300) -> Image.Image:
    return Image.new("RGB", (w, h), color=(255, 255, 255))


def test_zone_renderer_returns_image():
    config = _make_config_with_two_field_types()
    resolver = StyleResolver(config, seed=42)
    style = resolver.resolve("person_a", "standard")
    zone = config.zones[0]
    canvas = _blank_canvas()
    result = ZoneRenderer.draw(canvas, "Hello", style, zone)
    assert isinstance(result, Image.Image)
    assert result.size == canvas.size


def test_zone_renderer_modifies_canvas():
    """Canvas should differ from blank after drawing text."""
    config = _make_config_with_two_field_types()
    resolver = StyleResolver(config, seed=42)
    style = resolver.resolve("person_a", "standard")
    zone = config.zones[0]
    canvas = _blank_canvas()
    original_arr = np.array(canvas.copy())
    result = ZoneRenderer.draw(canvas, "Test text here", style, zone)
    result_arr = np.array(result)
    assert not np.array_equal(original_arr, result_arr)


def test_zone_renderer_does_not_mutate_original_canvas():
    config = _make_config_with_two_field_types()
    resolver = StyleResolver(config, seed=42)
    style = resolver.resolve("person_a", "standard")
    zone = config.zones[0]
    canvas = _blank_canvas()
    original_arr = np.array(canvas).copy()
    ZoneRenderer.draw(canvas, "Hello", style, zone)
    assert np.array_equal(np.array(canvas), original_arr)
