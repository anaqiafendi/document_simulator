"""Plotly chart builders for CER/WER comparison, confidence distributions, and reward curves."""

from typing import Any, Dict, List

import plotly.graph_objects as go

# Colour palette (Original = blue, Augmented = orange)
_COLOUR_ORIG = "#2196F3"
_COLOUR_AUG = "#FF9800"
_COLOUR_REWARD = "#4CAF50"


def cer_wer_bar(metrics: Dict[str, Any]) -> go.Figure:
    """Grouped bar chart comparing CER and WER for original vs augmented images.

    Args:
        metrics: Dict with keys ``mean_original_cer``, ``mean_augmented_cer``,
                 ``mean_original_wer``, ``mean_augmented_wer``, and optionally
                 ``std_*`` variants for error bars.

    Returns:
        Plotly Figure with two bar traces.
    """
    categories = ["CER", "WER"]
    orig_vals = [
        metrics.get("mean_original_cer", 0.0),
        metrics.get("mean_original_wer", 0.0),
    ]
    aug_vals = [
        metrics.get("mean_augmented_cer", 0.0),
        metrics.get("mean_augmented_wer", 0.0),
    ]
    orig_err = [
        metrics.get("std_original_cer"),
        metrics.get("std_original_wer"),
    ]
    aug_err = [
        metrics.get("std_augmented_cer"),
        metrics.get("std_augmented_wer"),
    ]

    def _error_bar(errs):
        if any(e is not None for e in errs):
            return {"type": "data", "array": [e or 0 for e in errs], "visible": True}
        return None

    fig = go.Figure(
        data=[
            go.Bar(
                name="Original",
                x=categories,
                y=orig_vals,
                marker_color=_COLOUR_ORIG,
                error_y=_error_bar(orig_err),
            ),
            go.Bar(
                name="Augmented",
                x=categories,
                y=aug_vals,
                marker_color=_COLOUR_AUG,
                error_y=_error_bar(aug_err),
            ),
        ]
    )
    fig.update_layout(
        barmode="group",
        title="CER / WER: Original vs Augmented",
        yaxis_title="Error Rate",
        yaxis_range=[0, 1],
        legend={"orientation": "h", "y": -0.2},
    )
    return fig


def confidence_box(
    original_scores: List[float],
    augmented_scores: List[float],
) -> go.Figure:
    """Box plot comparing OCR confidence score distributions.

    Args:
        original_scores:  Confidence values for un-augmented images.
        augmented_scores: Confidence values for augmented images.

    Returns:
        Plotly Figure with two box traces.
    """
    fig = go.Figure(
        data=[
            go.Box(
                y=original_scores,
                name="Original",
                marker_color=_COLOUR_ORIG,
                boxmean="sd",
            ),
            go.Box(
                y=augmented_scores,
                name="Augmented",
                marker_color=_COLOUR_AUG,
                boxmean="sd",
            ),
        ]
    )
    fig.update_layout(
        title="OCR Confidence Distribution",
        yaxis_title="Confidence",
        yaxis_range=[0, 1],
        legend={"orientation": "h", "y": -0.2},
    )
    return fig


def reward_line(log_entries: List[Dict[str, Any]]) -> go.Figure:
    """Line chart of RL reward over training steps.

    Args:
        log_entries: List of dicts with keys ``step`` and ``reward``.
                     Additional numeric keys (``cer``, ``confidence``, etc.)
                     are plotted as secondary traces if present.

    Returns:
        Plotly Figure (empty if *log_entries* is empty).
    """
    if not log_entries:
        return go.Figure()

    steps = [e["step"] for e in log_entries]
    rewards = [e.get("reward", 0.0) for e in log_entries]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=steps,
            y=rewards,
            mode="lines+markers",
            line={"color": _COLOUR_REWARD},
            name="Reward",
        )
    )

    # Optionally overlay CER if logged
    if any("cer" in e for e in log_entries):
        cer_vals = [e.get("cer") for e in log_entries]
        fig.add_trace(
            go.Scatter(
                x=steps,
                y=cer_vals,
                mode="lines",
                line={"color": _COLOUR_AUG, "dash": "dot"},
                name="CER",
                yaxis="y2",
            )
        )
        fig.update_layout(
            yaxis2={
                "title": "CER",
                "overlaying": "y",
                "side": "right",
                "range": [0, 1],
            }
        )

    fig.update_layout(
        title="Training Reward",
        xaxis_title="Step",
        yaxis_title="Reward",
        legend={"orientation": "h", "y": -0.2},
    )
    return fig
