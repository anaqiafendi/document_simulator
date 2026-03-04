"""Unit tests for SessionStateManager."""

from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# Import
# ---------------------------------------------------------------------------


def test_session_state_imports():
    from document_simulator.ui.state.session_state import SessionStateManager

    assert SessionStateManager is not None


# ---------------------------------------------------------------------------
# get_uploaded_image
# ---------------------------------------------------------------------------


def test_get_uploaded_image_returns_none_when_unset():
    from document_simulator.ui.state.session_state import SessionStateManager

    with patch("streamlit.session_state", {}):
        assert SessionStateManager().get_uploaded_image() is None


def test_set_and_get_uploaded_image(blank_image):
    from document_simulator.ui.state.session_state import SessionStateManager

    state = {}
    with patch("streamlit.session_state", state):
        mgr = SessionStateManager()
        mgr.set_uploaded_image(blank_image)
        assert mgr.get_uploaded_image() is blank_image


# ---------------------------------------------------------------------------
# aug image
# ---------------------------------------------------------------------------


def test_set_and_get_aug_image(blank_image):
    from document_simulator.ui.state.session_state import SessionStateManager

    state = {}
    with patch("streamlit.session_state", state):
        mgr = SessionStateManager()
        mgr.set_aug_image(blank_image)
        assert mgr.get_aug_image() is blank_image


def test_get_aug_image_returns_none_when_unset():
    from document_simulator.ui.state.session_state import SessionStateManager

    with patch("streamlit.session_state", {}):
        assert SessionStateManager().get_aug_image() is None


# ---------------------------------------------------------------------------
# OCR result
# ---------------------------------------------------------------------------


def test_set_and_get_ocr_result(sample_ocr_result):
    from document_simulator.ui.state.session_state import SessionStateManager

    state = {}
    with patch("streamlit.session_state", state):
        mgr = SessionStateManager()
        mgr.set_ocr_result(sample_ocr_result)
        assert mgr.get_ocr_result()["text"] == "Hello World"


def test_get_ocr_result_returns_none_when_unset():
    from document_simulator.ui.state.session_state import SessionStateManager

    with patch("streamlit.session_state", {}):
        assert SessionStateManager().get_ocr_result() is None


# ---------------------------------------------------------------------------
# Training state
# ---------------------------------------------------------------------------


def test_training_not_running_by_default():
    from document_simulator.ui.state.session_state import SessionStateManager

    with patch("streamlit.session_state", {}):
        assert SessionStateManager().is_training_running() is False


def test_set_training_running_true():
    from document_simulator.ui.state.session_state import SessionStateManager

    state = {}
    with patch("streamlit.session_state", state):
        mgr = SessionStateManager()
        mgr.set_training_running(True)
        assert mgr.is_training_running() is True


def test_append_and_get_training_log(sample_training_log):
    from document_simulator.ui.state.session_state import SessionStateManager

    state = {}
    with patch("streamlit.session_state", state):
        mgr = SessionStateManager()
        for entry in sample_training_log:
            mgr.append_training_log(entry)
        log = mgr.get_training_log()
        assert len(log) == len(sample_training_log)
        assert log[-1]["step"] == 3000


def test_get_training_log_empty_by_default():
    from document_simulator.ui.state.session_state import SessionStateManager

    with patch("streamlit.session_state", {}):
        assert SessionStateManager().get_training_log() == []


# ---------------------------------------------------------------------------
# clear
# ---------------------------------------------------------------------------


def test_clear_resets_all_keys(blank_image, sample_ocr_result):
    from document_simulator.ui.state.session_state import SessionStateManager

    state = {}
    with patch("streamlit.session_state", state):
        mgr = SessionStateManager()
        mgr.set_uploaded_image(blank_image)
        mgr.set_ocr_result(sample_ocr_result)
        mgr.set_training_running(True)
        mgr.clear()
        assert mgr.get_uploaded_image() is None
        assert mgr.get_ocr_result() is None
        assert mgr.is_training_running() is False


# ---------------------------------------------------------------------------
# Batch helpers
# ---------------------------------------------------------------------------


def test_set_and_get_batch_results(small_image):
    from document_simulator.ui.state.session_state import SessionStateManager

    state = {}
    with patch("streamlit.session_state", state):
        mgr = SessionStateManager()
        images = [small_image, small_image]
        mgr.set_batch_results(images)
        assert len(mgr.get_batch_results()) == 2


def test_batch_elapsed_default_zero():
    from document_simulator.ui.state.session_state import SessionStateManager

    with patch("streamlit.session_state", {}):
        assert SessionStateManager().get_batch_elapsed() == pytest.approx(0.0)
