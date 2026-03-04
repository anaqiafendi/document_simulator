"""Evaluation Dashboard — measure CER / WER / confidence across a labelled dataset."""

from pathlib import Path

import pandas as pd
import streamlit as st

from document_simulator.ui.components.file_uploader import extract_zip_to_tempdir, list_sample_files
from document_simulator.ui.components.metrics_charts import cer_wer_bar, confidence_box
from document_simulator.ui.state.session_state import SessionStateManager

st.set_page_config(page_title="Evaluation Dashboard", page_icon="📊", layout="wide")
st.title("📊 Evaluation Dashboard")
st.info(
    "**How to use:** Upload a ZIP of document/annotation pairs, use the built-in sample "
    "dataset, or specify a local directory path (Advanced). Each document (image or PDF) "
    "must have a matching `.json` or `.xml` annotation file with the same filename stem. "
    "The **Synthetic Generator** produces these pairs automatically when you run a batch. "
    "Select an augmentation preset and click **Run Evaluation** to measure CER, WER, and "
    "OCR confidence before and after augmentation across the whole dataset."
)

with st.expander("What do these metrics mean?"):
    st.markdown(
        """
### Character Error Rate (CER)
**Formula:** `edit_distance(predicted, ground_truth) / len(ground_truth)`

CER measures how many character-level edits (insertions, deletions, substitutions) are needed
to turn the OCR output into the ground truth text, expressed as a fraction of the ground truth
length.

| Value | Meaning |
|-------|---------|
| `0.00` | Perfect match — OCR output is identical to ground truth |
| `0.05` | 5% error — 5 edits per 100 ground truth characters (good) |
| `0.20` | 20% error — noticeable OCR degradation |
| `1.00` | As many edits as there are ground truth characters |
| `> 1.0` | More edits than reference characters — see note below |

**Why CER can exceed 1.0:** CER is not capped at 1. If the OCR output is much longer than
the ground truth (e.g. the ground truth only contains filled-field text but OCR also reads
background template text), the Levenshtein distance can exceed the reference length. A value
of `10` means the OCR output required 10× as many edits as the ground truth has characters —
this almost always means the ground truth text in the `.json` file covers only a small portion
of what is visible in the document. The red dashed line on the chart marks the `1.0` threshold.

---

### Word Error Rate (WER)
**Formula:** `word_edit_distance(predicted_words, ground_truth_words) / len(ground_truth_words)`

WER is the same idea as CER but at the word level — each token (whitespace-delimited) counts
as one unit. WER is usually higher than CER on the same document because a single wrong
character can make a whole word wrong.

| Value | Meaning |
|-------|---------|
| `0.00` | All words match exactly |
| `0.10` | 1 in 10 words is wrong |
| `1.00` | Every ground truth word has an error |
| `> 1.0` | More word-level errors than reference words (same root cause as CER > 1) |

---

### OCR Confidence
**Formula:** mean of per-region confidence scores returned by PaddleOCR

PaddleOCR returns a confidence score in `[0, 1]` for each detected text region. This metric
is the mean across all detected regions in a document. It reflects the model's certainty
about what it read — **not** whether it read the right thing (a confident wrong answer still
scores high). Use it alongside CER/WER rather than in isolation.

| Value | Meaning |
|-------|---------|
| `> 0.90` | High confidence — model is certain about its output |
| `0.70–0.90` | Moderate — some regions are ambiguous |
| `< 0.70` | Low — heavy degradation or difficult layout |

---

### Original vs Augmented
Each sample is OCR'd **twice** — once on the original image and once after applying the
selected augmentation preset. The delta in the headline metrics shows how much augmentation
increases error rate / decreases confidence. A small delta means the pipeline is robust;
a large delta highlights documents that degrade poorly under augmentation.

---

### Confidence box plot note
The box plot is constructed from `mean ± std` approximations rather than per-sample values
(the evaluator currently aggregates before returning). The shape gives a rough sense of
spread but should not be treated as a precise distribution.
        """
    )

state = SessionStateManager()

# ── Dataset source ────────────────────────────────────────────────────────────

st.subheader("Dataset")

# 1. ZIP upload (primary)
zip_upload = st.file_uploader(
    "Upload dataset as ZIP (PDF/image + JSON pairs)",
    type=["zip"],
    key="eval_zip",
)
if zip_upload is not None:
    tmp = extract_zip_to_tempdir(zip_upload)
    st.session_state["_eval_temp_dir"] = tmp   # keep alive — GC deletes files
    st.session_state["eval_effective_dir"] = tmp.name

# 2. Sample data
_samples_dir = Path("data/samples/evaluation")
_sample_files = list_sample_files("evaluation", (".pdf", ".png", ".jpg", ".jpeg", ".json"))
_has_samples = _samples_dir.exists() and any(
    p for p in _sample_files if p.suffix.lower() != ".json"
)

sample_col, _ = st.columns([1, 3])
if sample_col.button(
    "Use sample data",
    disabled=not _has_samples,
    help="Load the built-in sample dataset from data/samples/evaluation/"
    if _has_samples
    else "No sample files found in data/samples/evaluation/",
):
    st.session_state.pop("_eval_temp_dir", None)
    st.session_state["eval_effective_dir"] = str(_samples_dir)

# 3. Advanced — local directory
with st.expander("Advanced — use local directory path"):
    typed_dir = st.text_input(
        "Dataset directory",
        value=st.session_state.get("eval_effective_dir", "./data/test"),
        key="eval_data_dir",
    )
    if st.button("Use this directory", key="eval_use_dir"):
        st.session_state.pop("_eval_temp_dir", None)
        st.session_state["eval_effective_dir"] = typed_dir

# Show current effective dataset
_effective_dir = st.session_state.get("eval_effective_dir")
if _effective_dir:
    st.caption(f"Dataset: `{_effective_dir}`")

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    preset = st.selectbox(
        "Augmentation preset", ["light", "medium", "heavy"], index=1, key="eval_preset"
    )
    use_gpu = st.checkbox("GPU for OCR", value=False, key="eval_gpu")
    run_btn = st.button("Run Evaluation", type="primary")

# ── Run ───────────────────────────────────────────────────────────────────────

if run_btn:
    effective_dir = st.session_state.get("eval_effective_dir")
    if not effective_dir:
        st.error("Please select a dataset — upload a ZIP, use sample data, or specify a directory.")
    else:
        p = Path(effective_dir)
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
                        "No annotated document/ground-truth pairs found in the directory. "
                        "Each document (image or PDF) needs a matching .json or .xml annotation file."
                    )
                else:
                    results = evaluator.evaluate_dataset(dataset)
                    state.set_eval_results(results)

# ── Display ───────────────────────────────────────────────────────────────────

results = state.get_eval_results()

if results:
    n = results.get("n_samples", 0)

    orig_cer = results.get("mean_original_cer", 0.0)
    aug_cer = results.get("mean_augmented_cer", 0.0)
    aug_conf = results.get("mean_augmented_confidence", 0.0)
    orig_conf = results.get("mean_original_confidence", 0.0)
    cer_delta = aug_cer - orig_cer
    conf_delta = aug_conf - orig_conf

    col1, col2, col3 = st.columns(3)
    col1.metric("Samples evaluated", n)
    col2.metric(
        "Mean CER — augmented",
        f"{aug_cer:.1%}",
        delta=f"{cer_delta:+.1%}",
        delta_color="inverse",
    )
    col3.metric(
        "Mean Confidence — augmented",
        f"{aug_conf:.1%}",
        delta=f"{conf_delta:+.1%}",
        delta_color="inverse",
    )

    # Warn when error rates exceed 1 — almost always a ground truth coverage issue
    if aug_cer > 1.0 or orig_cer > 1.0:
        st.warning(
            f"CER exceeds 1.0 (original: {orig_cer:.2f}, augmented: {aug_cer:.2f}). "
            "This usually means the ground truth `.json` only contains partial text "
            "(e.g. filled-field text from the Synthetic Generator) while OCR is reading "
            "all visible text including background template content. "
            "Consider updating the `text` field in your annotations to include all "
            "text visible in the document."
        )

    # Charts
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.plotly_chart(cer_wer_bar(results), use_container_width=True)
    with chart_col2:
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
            f"{results.get('mean_original_cer', 0):.1%}",
            f"{results.get('mean_original_wer', 0):.1%}",
            f"{results.get('mean_original_confidence', 0):.1%}",
        ],
        "Original std": [
            f"{results.get('std_original_cer', 0):.1%}",
            f"{results.get('std_original_wer', 0):.1%}",
            f"{results.get('std_original_confidence', 0):.1%}",
        ],
        "Augmented mean": [
            f"{results.get('mean_augmented_cer', 0):.1%}",
            f"{results.get('mean_augmented_wer', 0):.1%}",
            f"{results.get('mean_augmented_confidence', 0):.1%}",
        ],
        "Augmented std": [
            f"{results.get('std_augmented_cer', 0):.1%}",
            f"{results.get('std_augmented_wer', 0):.1%}",
            f"{results.get('std_augmented_confidence', 0):.1%}",
        ],
        "Delta (aug − orig)": [
            f"{results.get('mean_augmented_cer', 0) - results.get('mean_original_cer', 0):+.1%}",
            f"{results.get('mean_augmented_wer', 0) - results.get('mean_original_wer', 0):+.1%}",
            f"{results.get('mean_augmented_confidence', 0) - results.get('mean_original_confidence', 0):+.1%}",
        ],
    }
    st.dataframe(pd.DataFrame(table_data), use_container_width=True)
else:
    st.caption("Configure the dataset above and click **Run Evaluation** in the sidebar to begin.")
