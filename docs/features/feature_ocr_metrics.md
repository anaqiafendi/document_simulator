# Feature: OCR Metrics

> **GitHub Issue:** `#5`
> **Status:** `complete`
> **Module:** `document_simulator.ocr.metrics`

---

## Summary

Pure-Python functions for evaluating OCR output quality: Character Error Rate (CER), Word Error Rate (WER), raw Levenshtein edit distance, and mean confidence aggregation. All functions are dependency-free and operate on plain strings or lists of floats.

---

## Motivation

### Problem Statement

Standard libraries like `jiwer` or `editdistance` add heavy transitive dependencies and have their own normalisation opinions (case folding, punctuation removal). This project needs simple, predictable metrics that behave identically across CPU, GPU, and test environments.

### Value Delivered

- No external dependencies — pure Python, works in any environment.
- CER and WER boundary cases (empty strings, both-empty) handled explicitly and documented.
- `aggregate_confidence()` provides the scalar summary needed for UI metrics and RL reward.
- Two-row DP Levenshtein keeps memory at O(min(len_a, len_b)) for long documents.

---

## User Stories

| Role | Goal | So That |
|------|------|---------|
| Evaluator | I call `calculate_cer(predicted, ground_truth)` | I get a normalised float for dataset benchmarking |
| UI user | I upload a `.txt` ground truth file on the OCR page | CER and WER appear as metric widgets |
| RL agent | I call `calculate_cer()` inside `_calculate_reward()` | The reward reflects OCR accuracy on the augmented image |
| Developer | I call `aggregate_confidence(scores)` | I get a single float for mean OCR confidence |

---

## Acceptance Criteria

- [ ] AC-1: `calculate_cer("hello", "hello")` returns `0.0`.
- [ ] AC-2: `calculate_cer("abc", "xyz")` returns `1.0` (3 substitutions on 3 chars).
- [ ] AC-3: `calculate_cer("something", "")` returns `1.0` (non-empty predicted, empty GT).
- [ ] AC-4: `calculate_cer("", "")` returns `0.0`.
- [ ] AC-5: `calculate_wer("hello world", "hello world")` returns `0.0`.
- [ ] AC-6: `calculate_wer("foo bar", "hello world")` returns `1.0`.
- [ ] AC-7: `aggregate_confidence([])` returns `0.0`.
- [ ] AC-8: `aggregate_confidence([0.8, 0.9, 1.0])` returns `0.9` (approx).
- [ ] AC-9: `calculate_levenshtein("abc", "axc")` returns `1`.

---

## Design

### Public API

```python
from document_simulator.ocr.metrics import (
    calculate_cer,
    calculate_wer,
    calculate_levenshtein,
    aggregate_confidence,
)

cer: float = calculate_cer(predicted, ground_truth)
wer: float = calculate_wer(predicted, ground_truth)
dist: int   = calculate_levenshtein(predicted, ground_truth)
conf: float = aggregate_confidence(scores)
```

### Data Flow

```
calculate_cer(predicted, ground_truth)
    │
    ├─► len(ground_truth) == 0?  →  0.0 or 1.0 (edge case)
    │
    ▼
_levenshtein(predicted, ground_truth)  ← char-level DP, O(min(a,b)) memory
    │
    ▼
distance / len(ground_truth)  →  float [0.0, ∞)

calculate_wer(predicted, ground_truth)
    │
    ├─► Split on whitespace → word lists
    │
    ▼
_word_levenshtein(pred_words, gt_words)  ← word-level DP
    │
    ▼
distance / len(gt_words)  →  float [0.0, ∞)
```

### Key Interfaces

| Symbol | Kind | Responsibility |
|--------|------|---------------|
| `calculate_cer(predicted, ground_truth)` | function | Character Error Rate normalised by GT length |
| `calculate_wer(predicted, ground_truth)` | function | Word Error Rate normalised by GT word count |
| `calculate_levenshtein(predicted, ground_truth)` | function | Raw char-level edit distance (integer) |
| `aggregate_confidence(scores)` | function | Mean of a list of per-region confidence floats |
| `_levenshtein(a, b)` | private function | Two-row DP implementation, swaps args to keep memory at O(min) |
| `_word_levenshtein(pred_words, gt_words)` | private function | Word-level DP; avoids null-byte join trick for correctness |

### Configuration

No `.env` settings — all functions are stateless and configuration-free.

---

## Implementation

### Files

| Path | Role |
|------|------|
| `src/document_simulator/ocr/metrics.py` | Full implementation: all four public functions + two private DP helpers |

### Key Architectural Decisions

1. **Own Levenshtein, not `editdistance` or `jellyfish`** — Avoids C extension dependencies that complicate cross-platform packaging. The two-row DP is O(m×n) time and O(min(m,n)) space, which is adequate for typical OCR output lengths.

2. **Word-level DP for WER, not null-byte join** — An early implementation joined word lists with `"\x00"` and ran char-level Levenshtein. This was incorrect when words contained `"\x00"`. Replaced with a dedicated `_word_levenshtein` that treats each word as an atomic token.

3. **CER can exceed 1.0** — When there are more insertions than ground-truth characters, CER > 1.0. This is the standard definition and is documented explicitly. The RL reward clamps `cer` to `[0, 1]` via `min(cer, 1.0)`.

4. **`aggregate_confidence` returns 0.0 for empty list** — Rather than raising, this avoids a special-case check in every caller when OCR finds no regions.

### Known Edge Cases & Constraints

- CER is case-sensitive by design. Callers that want case-insensitive comparison should normalise strings before calling.
- CER can exceed 1.0 for pathological predictions; the RL environment clamps it.

---

## Tests

### Test Files

| File | Type | Count | What is covered |
|------|------|-------|-----------------|
| `tests/unit/test_metrics.py` | unit | 25 | Levenshtein (6), CER (9), WER (7), `aggregate_confidence` (4) |

### TDD Cycle Summary

**Red — first failing tests written:**

| Test name | File | Initial failure reason |
|-----------|------|----------------------|
| `test_cer_empty_strings` | `tests/unit/test_metrics.py` | `ImportError: cannot import name 'calculate_cer'` |
| `test_wer_completely_wrong` | `tests/unit/test_metrics.py` | `ImportError: cannot import name 'calculate_wer'` |
| `test_aggregate_confidence_empty` | `tests/unit/test_metrics.py` | `ImportError: cannot import name 'aggregate_confidence'` |

**Green — minimal implementation:**

Wrote `calculate_cer` and `calculate_wer` using a naive O(m×n) Levenshtein with a full matrix. All edge-case tests passed. `test_wer_completely_wrong` initially failed because of the null-byte join approach: `_levenshtein("\x00".join(["foo","bar"]), "\x00".join(["hello","world"]))` returned a distance of 9 instead of 2 (char-level, not word-level).

**Refactor — improvements made after green:**

| What changed | Why |
|--------------|-----|
| Replaced null-byte join WER with `_word_levenshtein()` | `test_wer_completely_wrong` revealed the join approach computes char-level distance on the concatenated string, not word-level distance |
| Replaced full Levenshtein matrix with two-row rolling array | Memory profile for long documents was O(m×n); rolling array is O(min(m,n)) |
| Added `_levenshtein` arg swap when `len_a < len_b` | Ensures shorter string always forms the columns (rolling array dimension) |

Two additional tests were added post-refactor to cover the WER insertion case (`test_wer_with_extra_words`) and the explicit returns-float assertion (`test_wer_returns_float`).

### How to Run

```bash
uv run pytest tests/unit/test_metrics.py -v
uv run pytest tests/unit/test_metrics.py --cov=document_simulator.ocr.metrics
```

---

## Dependencies

### Requires

| Dependency | Kind | Why |
|------------|------|-----|
| None | — | Pure Python stdlib only |

### Required By

| Consumer | How it uses this feature |
|----------|------------------------|
| `ocr/engine.py` | No direct use — metrics applied by callers of `recognize()` |
| `evaluation/evaluator.py` | `calculate_cer()`, `calculate_wer()`, `aggregate_confidence()` per sample |
| `rl/environment.py` | `calculate_cer()` in `_calculate_reward()`; `aggregate_confidence()` for confidence term |
| `ui/pages/02_ocr_engine.py` | `calculate_cer()`, `calculate_wer()` when GT file is uploaded; `aggregate_confidence()` for mean confidence metric |

---

## Usage Examples

### Minimal

```python
from document_simulator.ocr.metrics import calculate_cer

cer = calculate_cer("Helo World", "Hello World")
print(f"CER: {cer:.3f}")  # 0.091
```

### Typical

```python
from document_simulator.ocr.metrics import calculate_cer, calculate_wer, aggregate_confidence

result = ocr_engine.recognize(image)
cer = calculate_cer(result["text"], ground_truth)
wer = calculate_wer(result["text"], ground_truth)
conf = aggregate_confidence(result["scores"])
print(f"CER={cer:.3f}  WER={wer:.3f}  Confidence={conf:.3f}")
```

### Advanced / Edge Case

```python
# CER can exceed 1.0 — clamp when used as a reward signal
from document_simulator.ocr.metrics import calculate_cer

cer = calculate_cer(very_wrong_prediction, short_ground_truth)
car = 1.0 - min(cer, 1.0)   # Character Accuracy Rate, clamped to [0, 1]
```

---

## Future Work

- [ ] Add `calculate_bleu()` for sentence-level accuracy.
- [ ] Add case-insensitive variant parameters: `calculate_cer(a, b, ignore_case=True)`.
- [ ] Benchmark against `jiwer` for large-scale equivalence test.

---

## References

- [feature_ocr_engine.md](feature_ocr_engine.md)
- [IMPLEMENTATION_PLAN.md — Phase 2](../IMPLEMENTATION_PLAN.md)
