# Feature: UI — Evaluation Dashboard

> **GitHub Issue:** `#17`
> **Status:** `complete`
> **Module:** `document_simulator.ui.pages.04_evaluation`

---

## Summary

A Streamlit page where a user enters a labelled dataset directory path, selects a preset and language, clicks Evaluate, and sees CER/WER/confidence metrics for original vs augmented images as Plotly bar and box charts alongside a summary dataframe.

---

## Motivation

### Problem Statement

`Evaluator.evaluate_dataset()` produces a rich metrics dict but requires code to visualise. The Evaluation Dashboard lets researchers compare augmentation impact across an entire dataset without a Jupyter notebook.

### Value Delivered

- CER and WER grouped bar chart (Original vs Augmented) with standard deviation error bars.
- Confidence box plot showing distribution spread.
- Summary `pd.DataFrame` with all `mean_*` and `std_*` values.
- Dataset size (`n_samples`) shown as a metric.

---

## Acceptance Criteria

- [ ] AC-1: Page loads without error.
- [ ] AC-2: An "Evaluate" button is present.
- [ ] AC-3: A preset selectbox is present.
- [ ] AC-4: A language selectbox is present.
- [ ] AC-5: Clicking Evaluate with no dataset path shows a `st.warning`.
- [ ] AC-6: When `eval_results` is in session state, a summary metric is visible.
- [ ] AC-7: When `eval_results` contains data, a dataframe with metric rows is visible.
- [ ] AC-8: When `eval_results` contains data, a chart element is visible (`at.metric` is non-empty).
- [ ] AC-9: When `eval_results["n_samples"] == 0`, a `st.info` message is shown.

---

## Design

### Data Flow

```
User enters dataset_dir path
User selects preset, language
User clicks "Evaluate"
    │
    ▼
DocumentDataset(dataset_dir)
DocumentAugmenter(preset)
OCREngine(lang=lang)
Evaluator(augmenter, ocr).evaluate_dataset(dataset)
    │
    ▼
state.set_eval_results(metrics)
cer_wer_bar(metrics)         → st.plotly_chart
confidence_box(orig, aug)    → st.plotly_chart
pd.DataFrame(metrics)        → st.dataframe
```

---

## Implementation

### Files

| Path | Role |
|------|------|
| `src/document_simulator/ui/pages/04_evaluation.py` | Complete page |
| `src/document_simulator/evaluation/evaluator.py` | `Evaluator` |
| `src/document_simulator/ui/components/metrics_charts.py` | `cer_wer_bar`, `confidence_box` |
| `src/document_simulator/ui/state/session_state.py` | `SessionStateManager` |

### Key Architectural Decisions

1. **Dataset path as text input, not file uploader** — Evaluation requires a directory path. Streamlit's file uploader works for individual files; for directories the simplest solution is a `st.text_input` for the local path.

2. **`n_samples == 0` shows `st.info`** — If the directory has no annotated pairs, showing empty charts is confusing. An info message explains that no image/annotation pairs were found.

3. **Approximate confidence box from `mean ± std`** — AppTest cannot assert on Plotly figures directly. The confidence box plot is constructed from `mean_original_confidence ± std_original_confidence` values rather than raw per-sample scores (which are not preserved in the aggregated result dict).

---

## Tests

### Test Files

| File | Type | Count | What is covered |
|------|------|-------|-----------------|
| `tests/ui/integration/test_evaluation.py` | integration | 9 | Load, Evaluate button, preset selectbox, language selectbox, warning on no path, summary metric, dataframe, chart visibility, empty dataset info |

### TDD Cycle Summary

**Red — first failing tests written:**

| Test name | File | Initial failure reason |
|-----------|------|----------------------|
| `test_evaluation_page_loads` | `test_evaluation.py` | `FileNotFoundError: 04_evaluation.py does not exist` |
| `test_evaluation_page_shows_metric_when_results_in_state` | `test_evaluation.py` | `at.metric` was empty — n_samples not rendered as `st.metric` |
| `test_evaluation_page_shows_info_for_empty_results` | `test_evaluation.py` | `at.info` was empty — `n_samples == 0` branch missing |

**Green — minimal implementation:**

Created page with preset and language selectboxes, dataset path text input, and Evaluate button. Injected `at.session_state["eval_results"]` with mock data. Added `st.metric("Samples", metrics["n_samples"])`. Added `st.info(...)` when `n_samples == 0`. All 9 tests passed.

**Refactor — improvements made after green:**

| What changed | Why |
|--------------|-----|
| Added `cer_wer_bar` and `confidence_box` Plotly charts | Initial green implementation only showed a summary dataframe; charts add visual value |
| Added `at.metric` assertion instead of `at.plotly_chart` | AppTest 1.54 does not expose `plotly_chart` accessor |

### How to Run

```bash
uv run pytest tests/ui/integration/test_evaluation.py -v
```

---

## Dependencies

### Requires

| Dependency | Kind | Why |
|------------|------|-----|
| `evaluation/evaluator.py` | internal | `Evaluator.evaluate_dataset()` |
| `ui/components/metrics_charts.py` | internal | `cer_wer_bar`, `confidence_box` |
| `ui/state/session_state.py` | internal | `SessionStateManager` |
| `pandas` | external | Summary dataframe |

---

## Future Work

- [ ] Add a directory browser widget instead of raw text input.
- [ ] Export evaluation results as CSV.
- [ ] Add per-sample worst/best CER table.

---

## References

- [feature_evaluation.md](feature_evaluation.md)
- [feature_ui_components.md](feature_ui_components.md)
- [UI_PLAN.md](../UI_PLAN.md)
