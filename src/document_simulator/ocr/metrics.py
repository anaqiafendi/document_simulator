"""OCR quality metrics: CER, WER, Levenshtein distance."""

from typing import List


def _levenshtein(a: str, b: str) -> int:
    """Compute Levenshtein edit distance between two strings."""
    if a == b:
        return 0
    len_a, len_b = len(a), len(b)
    if len_a == 0:
        return len_b
    if len_b == 0:
        return len_a

    # Use two-row DP to keep memory O(min(len_a, len_b))
    if len_a < len_b:
        a, b = b, a
        len_a, len_b = len_b, len_a

    prev = list(range(len_b + 1))
    for i, ch_a in enumerate(a, 1):
        curr = [i] + [0] * len_b
        for j, ch_b in enumerate(b, 1):
            curr[j] = min(
                prev[j] + 1,          # deletion
                curr[j - 1] + 1,      # insertion
                prev[j - 1] + (ch_a != ch_b),  # substitution
            )
        prev = curr
    return prev[len_b]


def calculate_levenshtein(predicted: str, ground_truth: str) -> int:
    """Character-level Levenshtein edit distance.

    Args:
        predicted: Predicted text string.
        ground_truth: Reference text string.

    Returns:
        Integer edit distance (>= 0).
    """
    return _levenshtein(predicted, ground_truth)


def calculate_cer(predicted: str, ground_truth: str) -> float:
    """Character Error Rate (CER).

    CER = Levenshtein(predicted, ground_truth) / len(ground_truth)

    Returns 0.0 when both strings are empty.  Returns 1.0 when
    ground_truth is empty but predicted is not.

    Args:
        predicted: Predicted text string.
        ground_truth: Reference text string.

    Returns:
        Float in [0.0, inf).  Values > 1.0 are possible when there are
        more insertions than ground-truth characters.
    """
    if len(ground_truth) == 0:
        return 0.0 if len(predicted) == 0 else 1.0
    return _levenshtein(predicted, ground_truth) / len(ground_truth)


def calculate_wer(predicted: str, ground_truth: str) -> float:
    """Word Error Rate (WER).

    WER = Levenshtein(predicted_words, ground_truth_words) / len(ground_truth_words)

    Words are split on whitespace.  Returns 0.0 when both are empty.
    Returns 1.0 when ground_truth is empty but predicted is not.

    Args:
        predicted: Predicted text string.
        ground_truth: Reference text string.

    Returns:
        Float in [0.0, inf).
    """
    gt_words = ground_truth.split()
    pred_words = predicted.split()

    if len(gt_words) == 0:
        return 0.0 if len(pred_words) == 0 else 1.0

    # Treat each word as a single "character" for the Levenshtein distance
    gt_joined = "\x00".join(gt_words)
    pred_joined = "\x00".join(pred_words)
    distance = _levenshtein(pred_joined, gt_joined)
    # The join adds (n-1) separators; we want word-level distance.
    # Use a word-level DP instead for correctness.
    distance = _word_levenshtein(pred_words, gt_words)
    return distance / len(gt_words)


def _word_levenshtein(pred_words: List[str], gt_words: List[str]) -> int:
    """Word-level Levenshtein distance."""
    len_p, len_g = len(pred_words), len(gt_words)
    if len_p == 0:
        return len_g
    if len_g == 0:
        return len_p

    prev = list(range(len_g + 1))
    for i, pw in enumerate(pred_words, 1):
        curr = [i] + [0] * len_g
        for j, gw in enumerate(gt_words, 1):
            curr[j] = min(
                prev[j] + 1,
                curr[j - 1] + 1,
                prev[j - 1] + (pw != gw),
            )
        prev = curr
    return prev[len_g]


def aggregate_confidence(scores: List[float]) -> float:
    """Mean OCR confidence across detected text regions.

    Args:
        scores: Per-region confidence scores in [0.0, 1.0].

    Returns:
        Mean confidence, or 0.0 if *scores* is empty.
    """
    if not scores:
        return 0.0
    return sum(scores) / len(scores)
