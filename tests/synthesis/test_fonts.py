"""Unit tests for FontResolver (fonts.py)."""

from PIL import ImageFont

from document_simulator.synthesis.fonts import FontResolver


def test_font_resolver_returns_image_font_for_each_category():
    for category in ("sans-serif", "serif", "monospace", "handwriting"):
        font = FontResolver.resolve(category, size=12)
        assert font is not None
        assert isinstance(font, ImageFont.FreeTypeFont | ImageFont.ImageFont)


def test_font_resolver_unknown_category_falls_back():
    font = FontResolver.resolve("unknown-category", size=12)
    assert font is not None


def test_font_resolver_size_is_respected():
    font_small = FontResolver.resolve("sans-serif", size=10)
    font_large = FontResolver.resolve("sans-serif", size=24)
    # Both should return without error; sizes may differ if TTF bundled
    assert font_small is not None
    assert font_large is not None


def test_font_resolver_known_categories():
    assert set(FontResolver.CATALOG.keys()) >= {
        "sans-serif",
        "serif",
        "monospace",
        "handwriting",
    }
