"""Integration tests for the multi-template batch augmentation UI."""

import numpy as np
import pytest
from PIL import Image
from streamlit.testing.v1 import AppTest

PAGE = "src/document_simulator/ui/pages/03_batch_processing.py"
TIMEOUT = 30


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fake_images(n: int = 3) -> list:
    return [Image.fromarray(np.full((50, 50, 3), i * 60, dtype=np.uint8)) for i in range(n)]


# ---------------------------------------------------------------------------
# Basic load (must not break existing behaviour)
# ---------------------------------------------------------------------------


def test_batch_page_still_loads():
    """Page must load without error after multi-template changes."""
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    assert not at.exception


def test_batch_page_still_has_run_button():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    labels = [b.label for b in at.button]
    assert any("batch" in l.lower() or "run" in l.lower() for l in labels)


def test_batch_page_still_has_preset_selectbox():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    assert len(at.selectbox) > 0


def test_batch_page_still_has_worker_slider():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    slider_labels = [s.label for s in at.slider]
    assert any("worker" in l.lower() for l in slider_labels)


# ---------------------------------------------------------------------------
# New multi-template UI controls
# ---------------------------------------------------------------------------


def test_batch_page_has_mode_radio():
    """Sidebar must expose an 'Augmentation mode' radio with at least 3 options."""
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    radio_labels = [r.label for r in at.radio]
    assert any("mode" in l.lower() for l in radio_labels), (
        f"Expected a mode radio, found radios: {radio_labels}"
    )


def test_batch_page_mode_radio_has_three_options():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    mode_radio = next(r for r in at.radio if "mode" in r.label.lower())
    assert len(mode_radio.options) >= 3


def test_batch_page_copies_input_visible_in_per_template_mode():
    """Selecting N×M mode should expose a 'copies per template' number input."""
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    mode_radio = next(r for r in at.radio if "mode" in r.label.lower())
    # Select the second option (N×M)
    mode_radio.set_value(mode_radio.options[1]).run()
    assert not at.exception
    number_labels = [n.label.lower() for n in at.number_input]
    assert any("cop" in l for l in number_labels), (
        f"Expected copies input, found number_inputs: {number_labels}"
    )


def test_batch_page_total_input_visible_in_random_sample_mode():
    """Selecting M-total mode should expose a 'total outputs' number input."""
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    mode_radio = next(r for r in at.radio if "mode" in r.label.lower())
    # Select the third option (M-total)
    mode_radio.set_value(mode_radio.options[2]).run()
    assert not at.exception
    number_labels = [n.label.lower() for n in at.number_input]
    assert any("total" in l or "output" in l for l in number_labels), (
        f"Expected total outputs input, found number_inputs: {number_labels}"
    )


# ---------------------------------------------------------------------------
# Results rendering — multi-template outputs
# ---------------------------------------------------------------------------


def test_batch_page_shows_metrics_after_multi_template_results():
    """Processed metric should appear when multi-template results are in state."""
    fake_imgs = _fake_images(6)  # Simulates N=2, copies=3

    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    at.session_state["batch_results"] = fake_imgs
    at.session_state["batch_input_images"] = fake_imgs
    at.session_state["batch_elapsed"] = 2.0
    at.run()

    metric_labels = [m.label for m in at.metric]
    assert any(
        "processed" in l.lower() or "time" in l.lower() or "throughput" in l.lower()
        for l in metric_labels
    )


def test_batch_page_processed_metric_correct_count():
    """Processed metric must reflect the actual number of results."""
    fake_imgs = _fake_images(5)

    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    at.session_state["batch_results"] = fake_imgs
    at.session_state["batch_elapsed"] = 1.0
    at.run()

    processed_metric = next(m for m in at.metric if "processed" in m.label.lower())
    assert processed_metric.value == "5"
