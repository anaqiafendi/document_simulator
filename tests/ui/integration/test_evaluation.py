"""Integration tests for the Evaluation Dashboard page."""

import pytest
from streamlit.testing.v1 import AppTest


PAGE = "src/document_simulator/ui/pages/04_evaluation.py"
TIMEOUT = 30


def test_evaluation_page_loads():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    assert not at.exception


def test_evaluation_page_has_run_button():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    labels = [b.label for b in at.button]
    assert any("eval" in l.lower() or "run" in l.lower() for l in labels)


def test_evaluation_page_has_preset_selectbox():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    assert len(at.selectbox) > 0


def test_evaluation_page_has_data_dir_input():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    assert len(at.text_input) > 0


def test_evaluation_page_error_on_missing_dir():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    ti = at.text_input[0]
    ti.set_value("/nonexistent/path/xyz").run()
    run_btn = next(b for b in at.button if "eval" in b.label.lower() or "run" in b.label.lower())
    run_btn.click().run()
    assert len(at.error) > 0


def test_evaluation_page_shows_dataframe_when_results_in_state(sample_eval_metrics):
    """When results are in state, the summary table (dataframe) should be rendered.
    (AppTest does not expose st.plotly_chart as a named widget accessor.)
    """
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    at.session_state["eval_results"] = sample_eval_metrics
    at.run()
    assert len(at.dataframe) > 0


def test_evaluation_page_shows_summary_table(sample_eval_metrics):
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    at.session_state["eval_results"] = sample_eval_metrics
    at.run()
    assert len(at.dataframe) > 0


def test_evaluation_page_shows_n_samples_metric(sample_eval_metrics):
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    at.session_state["eval_results"] = sample_eval_metrics
    at.run()
    metric_labels = [m.label for m in at.metric]
    assert any("sample" in l.lower() for l in metric_labels)


def test_evaluation_page_shows_cer_metric(sample_eval_metrics):
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    at.session_state["eval_results"] = sample_eval_metrics
    at.run()
    metric_labels = [m.label for m in at.metric]
    assert any("cer" in l.lower() for l in metric_labels)
