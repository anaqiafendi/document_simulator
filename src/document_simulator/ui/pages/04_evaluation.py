"""Evaluation Dashboard — measure CER / WER / confidence across a labelled dataset."""

from pathlib import Path

import pandas as pd
import streamlit as st

from document_simulator.ui.components.metrics_charts import cer_wer_bar, confidence_box
from document_simulator.ui.state.session_state import SessionStateManager

st.set_page_config(page_title="Evaluation Dashboard", page_icon="📊", layout="wide")
st.title("📊 Evaluation Dashboard")

state = SessionStateManager()

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    data_dir = st.text_input("Dataset directory", value="./data/test", key="eval_data_dir")
    preset = st.selectbox(
        "Augmentation preset", ["light", "medium", "heavy"], index=1, key="eval_preset"
    )
    use_gpu = st.checkbox("GPU for OCR", value=False, key="eval_gpu")
    run_btn = st.button("Run Evaluation", type="primary")

# ── Run ───────────────────────────────────────────────────────────────────────

if run_btn:
    p = Path(data_dir)
    if not p.exists():
        st.error(f"Directory not found: {p.resolve()}")
    else:
        from document_simulator.augmentation import DocumentAugmenter
        from document_simulator.data import DocumentDataset
        from document_simulator.evaluation import Evaluator
        from document_simulator.ocr import OCREngine

        with st.spinner("Running evaluation… (this may take a while)"):
            augmenter = DocumentAugmenter(pipeline=str(preset))
            engine = OCREngine(use_gpu=bool(use_gpu))
            evaluator = Evaluator(augmenter, engine)
            dataset = DocumentDataset(p)

            if len(dataset) == 0:
                st.warning(
                    "No annotated image/ground-truth pairs found in the directory. "
                    "Each image needs a matching .json or .xml annotation file."
                )
            else:
                results = evaluator.evaluate_dataset(dataset)
                state.set_eval_results(results)

# ── Display ───────────────────────────────────────────────────────────────────

results = state.get_eval_results()

if results:
    n = results.get("n_samples", 0)
    col1, col2, col3 = st.columns(3)
    col1.metric("Samples evaluated", n)
    col2.metric(
        "Mean CER — augmented",
        f"{results.get('mean_augmented_cer', 0):.4f}",
        delta=f"+{results.get('mean_augmented_cer', 0) - results.get('mean_original_cer', 0):.4f}",
        delta_color="inverse",
    )
    col3.metric(
        "Mean Confidence — augmented",
        f"{results.get('mean_augmented_confidence', 0):.4f}",
        delta=f"{results.get('mean_augmented_confidence', 0) - results.get('mean_original_confidence', 0):.4f}",
        delta_color="inverse",
    )

    # Charts
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.plotly_chart(cer_wer_bar(results), use_container_width=True)
    with chart_col2:
        # Approximate distribution with mean ± std (real per-sample data would be ideal)
        orig_conf_approx = [
            results.get("mean_original_confidence", 0.9)
            + (i % 3 - 1) * results.get("std_original_confidence", 0.02)
            for i in range(max(n, 3))
        ]
        aug_conf_approx = [
            results.get("mean_augmented_confidence", 0.8)
            + (i % 3 - 1) * results.get("std_augmented_confidence", 0.04)
            for i in range(max(n, 3))
        ]
        st.plotly_chart(
            confidence_box(orig_conf_approx, aug_conf_approx), use_container_width=True
        )

    # Summary table
    st.subheader("Summary Statistics")
    table_data = {
        "Metric": ["CER", "WER", "Confidence"],
        "Original mean": [
            results.get("mean_original_cer"),
            results.get("mean_original_wer"),
            results.get("mean_original_confidence"),
        ],
        "Original std": [
            results.get("std_original_cer"),
            results.get("std_original_wer"),
            results.get("std_original_confidence"),
        ],
        "Augmented mean": [
            results.get("mean_augmented_cer"),
            results.get("mean_augmented_wer"),
            results.get("mean_augmented_confidence"),
        ],
        "Augmented std": [
            results.get("std_augmented_cer"),
            results.get("std_augmented_wer"),
            results.get("std_augmented_confidence"),
        ],
    }
    st.dataframe(pd.DataFrame(table_data).round(4), use_container_width=True)
else:
    st.info(
        "Point **Dataset directory** to a folder containing image/annotation pairs "
        "(e.g. `image.jpg` + `image.json`) and click **Run Evaluation**."
    )
