"""Integration tests for the Batch Processing page."""

import numpy as np
import pytest
from PIL import Image
from streamlit.testing.v1 import AppTest


PAGE = "src/document_simulator/ui/pages/03_batch_processing.py"
TIMEOUT = 30


def test_batch_page_loads():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    assert not at.exception


def test_batch_page_has_run_button():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    labels = [b.label for b in at.button]
    assert any("batch" in l.lower() or "run" in l.lower() for l in labels)


def test_batch_page_has_preset_selectbox():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    assert len(at.selectbox) > 0


def test_batch_page_has_worker_slider():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    slider_labels = [s.label for s in at.slider]
    assert any("worker" in l.lower() for l in slider_labels)


def test_batch_page_has_parallel_checkbox():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    cb_labels = [c.label for c in at.checkbox]
    assert any("parallel" in l.lower() for l in cb_labels)


def test_batch_page_warning_when_no_files():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    run_btn = next(b for b in at.button if "batch" in b.label.lower() or "run" in b.label.lower())
    run_btn.click().run()
    assert len(at.warning) > 0


def test_batch_page_shows_metrics_after_results_in_state():
    fake_imgs = [Image.fromarray(np.full((50, 50, 3), i * 40, dtype=np.uint8)) for i in range(3)]

    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    at.session_state["batch_results"] = fake_imgs
    at.session_state["batch_input_images"] = fake_imgs
    at.session_state["batch_elapsed"] = 1.5
    at.run()

    metric_labels = [m.label for m in at.metric]
    assert any(
        "processed" in l.lower() or "time" in l.lower() or "throughput" in l.lower()
        for l in metric_labels
    )


def test_batch_page_shows_processed_metric_after_results():
    """When results are in session state, Processed metric should be visible.
    (AppTest does not expose st.download_button as a named widget accessor.)
    """
    fake_imgs = [Image.fromarray(np.full((50, 50, 3), 100, dtype=np.uint8))]

    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    at.session_state["batch_results"] = fake_imgs
    at.session_state["batch_elapsed"] = 0.5
    at.run()

    metric_labels = [m.label for m in at.metric]
    assert any("processed" in l.lower() for l in metric_labels)
