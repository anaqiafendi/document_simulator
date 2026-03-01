"""Unit tests for metrics_charts component."""

import pytest
import plotly.graph_objects as go


# ---------------------------------------------------------------------------
# cer_wer_bar
# ---------------------------------------------------------------------------


def test_cer_wer_bar_returns_figure(sample_eval_metrics):
    from document_simulator.ui.components.metrics_charts import cer_wer_bar

    fig = cer_wer_bar(sample_eval_metrics)
    assert isinstance(fig, go.Figure)


def test_cer_wer_bar_has_two_traces(sample_eval_metrics):
    from document_simulator.ui.components.metrics_charts import cer_wer_bar

    fig = cer_wer_bar(sample_eval_metrics)
    assert len(fig.data) == 2


def test_cer_wer_bar_trace_names(sample_eval_metrics):
    from document_simulator.ui.components.metrics_charts import cer_wer_bar

    fig = cer_wer_bar(sample_eval_metrics)
    names = [t.name for t in fig.data]
    assert "Original" in names
    assert "Augmented" in names


def test_cer_wer_bar_values_match(sample_eval_metrics):
    from document_simulator.ui.components.metrics_charts import cer_wer_bar

    fig = cer_wer_bar(sample_eval_metrics)
    orig_trace = next(t for t in fig.data if t.name == "Original")
    assert orig_trace.y[0] == pytest.approx(sample_eval_metrics["mean_original_cer"])


def test_cer_wer_bar_empty_metrics():
    from document_simulator.ui.components.metrics_charts import cer_wer_bar

    fig = cer_wer_bar({})
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2


# ---------------------------------------------------------------------------
# confidence_box
# ---------------------------------------------------------------------------


def test_confidence_box_returns_figure():
    from document_simulator.ui.components.metrics_charts import confidence_box

    fig = confidence_box([0.9, 0.95, 0.88], [0.75, 0.80, 0.70])
    assert isinstance(fig, go.Figure)


def test_confidence_box_has_two_traces():
    from document_simulator.ui.components.metrics_charts import confidence_box

    fig = confidence_box([0.9, 0.95], [0.75, 0.80])
    assert len(fig.data) == 2


def test_confidence_box_trace_names():
    from document_simulator.ui.components.metrics_charts import confidence_box

    fig = confidence_box([0.9], [0.8])
    names = [t.name for t in fig.data]
    assert "Original" in names
    assert "Augmented" in names


def test_confidence_box_empty_lists():
    from document_simulator.ui.components.metrics_charts import confidence_box

    fig = confidence_box([], [])
    assert isinstance(fig, go.Figure)


# ---------------------------------------------------------------------------
# reward_line
# ---------------------------------------------------------------------------


def test_reward_line_returns_figure():
    from document_simulator.ui.components.metrics_charts import reward_line

    log = [{"step": 0, "reward": 0.1}, {"step": 1000, "reward": 0.4}]
    fig = reward_line(log)
    assert isinstance(fig, go.Figure)


def test_reward_line_empty_log():
    from document_simulator.ui.components.metrics_charts import reward_line

    fig = reward_line([])
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 0


def test_reward_line_has_reward_trace():
    from document_simulator.ui.components.metrics_charts import reward_line

    log = [{"step": 0, "reward": 0.1}, {"step": 500, "reward": 0.5}]
    fig = reward_line(log)
    trace_names = [t.name for t in fig.data]
    assert "Reward" in trace_names


def test_reward_line_adds_cer_trace_when_present(sample_training_log):
    from document_simulator.ui.components.metrics_charts import reward_line

    fig = reward_line(sample_training_log)
    trace_names = [t.name for t in fig.data]
    assert "CER" in trace_names


def test_reward_line_x_values_match_steps(sample_training_log):
    from document_simulator.ui.components.metrics_charts import reward_line

    fig = reward_line(sample_training_log)
    reward_trace = next(t for t in fig.data if t.name == "Reward")
    assert list(reward_trace.x) == [e["step"] for e in sample_training_log]
