"""Integration tests for the RL Training page."""

import pytest
from streamlit.testing.v1 import AppTest


PAGE = "src/document_simulator/ui/pages/05_rl_training.py"
TIMEOUT = 30


def test_rl_training_page_loads():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    assert not at.exception


def test_rl_page_has_start_button():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    labels = [b.label for b in at.button]
    assert any("start" in l.lower() or "▶" in l for l in labels)


def test_rl_page_has_stop_button():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    labels = [b.label for b in at.button]
    assert any("stop" in l.lower() or "⏹" in l for l in labels)


def test_rl_page_has_learning_rate_input():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    all_labels = (
        [s.label for s in at.slider]
        + [ti.label for ti in at.text_input]
        + [ni.label for ni in at.number_input]
    )
    assert any("learning" in l.lower() or "lr" in l.lower() or "rate" in l.lower() for l in all_labels)


def test_rl_page_has_batch_size_input():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    all_labels = [ni.label for ni in at.number_input]
    assert any("batch" in l.lower() for l in all_labels)


def test_rl_page_has_env_slider():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    slider_labels = [s.label for s in at.slider]
    assert any("env" in l.lower() for l in slider_labels)


def test_rl_page_renders_without_error_when_log_available(sample_training_log):
    """With training log in state the page should render without exceptions.
    (AppTest does not expose st.plotly_chart as a named widget accessor.)
    """
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    at.session_state["training_log"] = sample_training_log
    at.session_state["training_running"] = False
    at.run()
    assert not at.exception


def test_rl_page_shows_step_metric_when_log_available(sample_training_log):
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    at.session_state["training_log"] = sample_training_log
    at.session_state["training_running"] = False
    at.run()
    metric_labels = [m.label for m in at.metric]
    assert any("step" in l.lower() or "reward" in l.lower() for l in metric_labels)


def test_rl_page_shows_reward_metric_when_log_available(sample_training_log):
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    at.session_state["training_log"] = sample_training_log
    at.session_state["training_running"] = False
    at.run()
    metric_labels = [m.label for m in at.metric]
    assert any("reward" in l.lower() for l in metric_labels)
