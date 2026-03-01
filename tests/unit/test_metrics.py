"""Unit tests for OCR quality metrics."""

import pytest

from document_simulator.ocr.metrics import (
    aggregate_confidence,
    calculate_cer,
    calculate_levenshtein,
    calculate_wer,
)


# ---------------------------------------------------------------------------
# Levenshtein
# ---------------------------------------------------------------------------

def test_levenshtein_identical():
    assert calculate_levenshtein("hello", "hello") == 0


def test_levenshtein_empty_strings():
    assert calculate_levenshtein("", "") == 0


def test_levenshtein_one_empty():
    assert calculate_levenshtein("abc", "") == 3
    assert calculate_levenshtein("", "abc") == 3


def test_levenshtein_single_substitution():
    assert calculate_levenshtein("abc", "axc") == 1


def test_levenshtein_single_insertion():
    assert calculate_levenshtein("ac", "abc") == 1


def test_levenshtein_single_deletion():
    assert calculate_levenshtein("abc", "ac") == 1


# ---------------------------------------------------------------------------
# CER
# ---------------------------------------------------------------------------

def test_cer_empty_strings():
    """CER of two empty strings should be 0."""
    assert calculate_cer("", "") == 0.0


def test_cer_identical_strings():
    """CER of identical strings should be 0."""
    assert calculate_cer("hello", "hello") == 0.0


def test_cer_completely_different():
    """CER of completely different strings of same length."""
    assert calculate_cer("abc", "xyz") == 1.0


def test_cer_case_sensitive():
    """CER should be case-sensitive by default."""
    assert calculate_cer("Hello", "hello") > 0.0


def test_cer_ground_truth_empty_predicted_nonempty():
    """When ground truth is empty and predicted is not, CER = 1.0."""
    assert calculate_cer("something", "") == 1.0


def test_cer_ground_truth_empty_predicted_empty():
    """When both are empty, CER = 0.0."""
    assert calculate_cer("", "") == 0.0


def test_cer_single_substitution():
    # "helo world!" vs "hello world" — 2 edits on 11 chars
    predicted = "helo world!"
    ground_truth = "hello world"
    cer = calculate_cer(predicted, ground_truth)
    assert 0.0 <= cer <= 1.0
    assert cer == pytest.approx(2 / 11)


def test_cer_returns_float():
    assert isinstance(calculate_cer("a", "b"), float)


# ---------------------------------------------------------------------------
# WER
# ---------------------------------------------------------------------------

def test_wer_empty_strings():
    assert calculate_wer("", "") == 0.0


def test_wer_identical():
    assert calculate_wer("hello world", "hello world") == 0.0


def test_wer_completely_wrong():
    # 2 wrong words out of 2
    assert calculate_wer("foo bar", "hello world") == 1.0


def test_wer_with_extra_words():
    """WER calculation with insertions."""
    wer = calculate_wer("hello world", "hello beautiful world")
    assert wer > 0.0


def test_wer_ground_truth_empty_predicted_nonempty():
    assert calculate_wer("extra words", "") == 1.0


def test_wer_ground_truth_empty_both_empty():
    assert calculate_wer("", "") == 0.0


def test_wer_returns_float():
    assert isinstance(calculate_wer("a", "b"), float)


# ---------------------------------------------------------------------------
# aggregate_confidence
# ---------------------------------------------------------------------------

def test_aggregate_confidence_empty():
    assert aggregate_confidence([]) == 0.0


def test_aggregate_confidence_single():
    assert aggregate_confidence([0.9]) == pytest.approx(0.9)


def test_aggregate_confidence_multiple():
    assert aggregate_confidence([0.8, 0.9, 1.0]) == pytest.approx(0.9)


def test_aggregate_confidence_zero():
    assert aggregate_confidence([0.0, 0.0]) == pytest.approx(0.0)
