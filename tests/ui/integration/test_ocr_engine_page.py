"""Integration tests for the OCR Engine page."""

import numpy as np
import pytest
from PIL import Image
from streamlit.testing.v1 import AppTest


PAGE = "src/document_simulator/ui/pages/02_ocr_engine.py"
TIMEOUT = 30


def test_ocr_page_loads():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    assert not at.exception


def test_ocr_page_has_run_button():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    labels = [b.label for b in at.button]
    assert any("ocr" in l.lower() or "run" in l.lower() for l in labels)


def test_ocr_page_has_language_selectbox():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    assert len(at.selectbox) > 0


def test_ocr_page_language_options_include_english():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    sb = at.selectbox[0]
    assert "en" in [str(o) for o in sb.options]


def test_ocr_page_warning_when_no_image():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    run_btn = next(b for b in at.button if "ocr" in b.label.lower() or "run" in b.label.lower())
    run_btn.click().run()
    assert len(at.warning) > 0


def test_ocr_page_shows_metrics_when_result_in_state():
    from unittest.mock import MagicMock, patch

    mock_result = {
        "text": "Hello World",
        "boxes": [[[10, 5], [80, 5], [80, 25], [10, 25]]],
        "scores": [0.95],
        "raw": None,
    }
    fake_img = Image.fromarray(np.full((50, 50, 3), 200, dtype=np.uint8))

    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    at.session_state["last_uploaded_image"] = fake_img
    at.session_state["last_ocr_result"] = mock_result
    at.run()

    metric_labels = [m.label for m in at.metric]
    assert any("confidence" in l.lower() for l in metric_labels)


def test_ocr_page_shows_region_table_when_result_in_state():
    mock_result = {
        "text": "Invoice",
        "boxes": [[[5, 5], [60, 5], [60, 20], [5, 20]]],
        "scores": [0.88],
        "raw": None,
    }
    fake_img = Image.fromarray(np.full((50, 50, 3), 200, dtype=np.uint8))

    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    at.session_state["last_uploaded_image"] = fake_img
    at.session_state["last_ocr_result"] = mock_result
    at.run()

    assert len(at.dataframe) > 0


def test_ocr_page_shows_page_selector_for_pdf():
    """When ocr_is_pdf=True and multiple pages are stored, a slider should appear."""
    fake_img = Image.fromarray(np.full((50, 50, 3), 200, dtype=np.uint8))

    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    at.session_state["ocr_is_pdf"] = True
    at.session_state["ocr_pdf_pages"] = [fake_img, fake_img, fake_img]
    at.session_state["ocr_pdf_page_idx"] = 0
    at.run()

    assert len(at.slider) >= 1


def test_ocr_page_warns_when_no_document_uploaded():
    """Clicking Run OCR with no image in state should show a warning."""
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    # Ensure no image in state
    at.session_state["last_uploaded_image"] = None
    run_btn = next(b for b in at.button if "ocr" in b.label.lower() or "run" in b.label.lower())
    run_btn.click().run()
    assert len(at.warning) > 0


def test_ocr_page_shows_region_count_metric():
    mock_result = {
        "text": "A\nB",
        "boxes": [
            [[5, 5], [30, 5], [30, 15], [5, 15]],
            [[35, 5], [65, 5], [65, 15], [35, 15]],
        ],
        "scores": [0.9, 0.85],
        "raw": None,
    }
    fake_img = Image.fromarray(np.full((50, 50, 3), 200, dtype=np.uint8))

    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    at.session_state["last_uploaded_image"] = fake_img
    at.session_state["last_ocr_result"] = mock_result
    at.run()

    metric_labels = [m.label for m in at.metric]
    assert any("region" in l.lower() for l in metric_labels)
