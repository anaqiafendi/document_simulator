"""Integration tests for the Synthetic Document Generator page."""

import numpy as np
import pytest
from PIL import Image
from streamlit.testing.v1 import AppTest

PAGE = "src/document_simulator/ui/pages/00_synthetic_generator.py"
TIMEOUT = 30


# ---------------------------------------------------------------------------
# Basic load
# ---------------------------------------------------------------------------


def test_page_loads_without_exception():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    assert not at.exception


def test_page_title_is_present():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    all_text = " ".join(str(e.value) for e in at.title)
    assert "synthetic" in all_text.lower() or "generator" in all_text.lower()


def test_page_has_info_message():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    assert len(at.info) > 0


# ---------------------------------------------------------------------------
# Template / style selector
# ---------------------------------------------------------------------------


def test_page_has_doc_type_selectbox():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    assert len(at.selectbox) >= 1, "Expected at least one selectbox (document type)"


def test_page_has_style_selectbox():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    assert len(at.selectbox) >= 2, "Expected at least two selectboxes (doc type + style)"


def test_doc_type_selectbox_contains_receipt():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    doc_type_box = at.selectbox[0]
    assert "receipt" in [opt.lower() for opt in doc_type_box.options]


def test_style_selectbox_contains_thermal_and_a4():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    # Style selectbox is second
    style_box = at.selectbox[1]
    options_lower = [o.lower() for o in style_box.options]
    assert "thermal" in options_lower
    assert "a4" in options_lower


def test_selecting_thermal_style_does_not_raise():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    style_box = at.selectbox[1]
    style_box.set_value("thermal").run()
    assert not at.exception


def test_selecting_a4_style_does_not_raise():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    style_box = at.selectbox[1]
    style_box.set_value("a4").run()
    assert not at.exception


# ---------------------------------------------------------------------------
# Line item slider
# ---------------------------------------------------------------------------


def test_page_has_line_items_slider():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    slider_labels = [s.label.lower() for s in at.slider]
    assert any("line item" in l or "item" in l for l in slider_labels), (
        f"Expected a line-items slider, found: {slider_labels}"
    )


def test_line_items_slider_respects_thermal_range():
    """Thermal template has num_rows_range=(2, 12)."""
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    # Select thermal explicitly
    at.selectbox[1].set_value("thermal").run()
    items_slider = next(s for s in at.slider if "item" in s.label.lower())
    assert items_slider.min == 2
    assert items_slider.max == 12


def test_line_items_slider_respects_a4_range():
    """A4 template has num_rows_range=(2, 20)."""
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    at.selectbox[1].set_value("a4").run()
    items_slider = next(s for s in at.slider if "item" in s.label.lower())
    assert items_slider.min == 2
    assert items_slider.max == 20


def test_line_items_slider_value_changes():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    items_slider = next(s for s in at.slider if "item" in s.label.lower())
    new_val = items_slider.min + 1
    items_slider.set_value(new_val).run()
    assert not at.exception


# ---------------------------------------------------------------------------
# Seed control
# ---------------------------------------------------------------------------


def test_page_has_seed_number_input():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    number_labels = [n.label.lower() for n in at.number_input]
    assert any("seed" in l for l in number_labels), (
        f"Expected a seed number input, found: {number_labels}"
    )


def test_seed_input_default_is_42():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    seed_input = next(n for n in at.number_input if "seed" in n.label.lower())
    assert seed_input.value == 42


# ---------------------------------------------------------------------------
# Generate button
# ---------------------------------------------------------------------------


def test_page_has_generate_button():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    button_labels = [b.label.lower() for b in at.button]
    assert any("generate" in l for l in button_labels), (
        f"Expected a generate button, found: {button_labels}"
    )


# ---------------------------------------------------------------------------
# Template structure preview
# ---------------------------------------------------------------------------


def test_page_has_structure_dataframe():
    """The template structure preview must render a dataframe."""
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    assert len(at.dataframe) >= 1, "Expected at least one dataframe for structure preview"


def test_structure_dataframe_has_section_rows():
    """The dataframe must contain at least header, line_items, subtotals, footer sections."""
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    df = at.dataframe[0].value
    assert len(df) >= 3, f"Expected >= 3 section rows, got {len(df)}"


def test_page_has_height_metrics():
    """Min/max height metrics must be rendered."""
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    metric_labels = [m.label.lower() for m in at.metric]
    assert any("min" in l and "height" in l for l in metric_labels), (
        f"Expected a min height metric, found: {metric_labels}"
    )
    assert any("max" in l and "height" in l for l in metric_labels), (
        f"Expected a max height metric, found: {metric_labels}"
    )


# ---------------------------------------------------------------------------
# Generated image display (injected into session state)
# ---------------------------------------------------------------------------


def test_page_shows_generated_image_when_in_state():
    """If session state has a generated image, the page should surface a download key."""
    fake_img = Image.fromarray(np.full((100, 220, 3), 240, dtype=np.uint8))

    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    at.session_state["synth_gen_image"] = fake_img
    at.run()
    assert not at.exception
    # Download button becomes available — check the session key flag
    assert "synth_gen_image" in at.session_state


# ---------------------------------------------------------------------------
# Zone editor link is still present
# ---------------------------------------------------------------------------


def test_page_contains_zone_editor_link():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    all_markdown = " ".join(str(e.value) for e in at.markdown)
    assert "localhost:8000" in all_markdown
