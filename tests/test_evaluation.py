"""Tests for the Evaluator framework."""

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PIL import Image

from document_simulator.augmentation import DocumentAugmenter
from document_simulator.data.datasets import DocumentDataset
from document_simulator.evaluation.evaluator import Evaluator

VALID_BOX = [[0.0, 0.0], [100.0, 0.0], [100.0, 20.0], [0.0, 20.0]]


def _make_ocr_mock(text: str = "Hello World", score: float = 0.95):
    mock = MagicMock()
    mock.recognize.return_value = {"text": text, "scores": [score], "boxes": []}
    return mock


def _make_augmenter_mock():
    mock = MagicMock(spec=DocumentAugmenter)
    mock.augment.side_effect = lambda img: img  # identity
    return mock


def _create_sample_dataset(tmp_path: Path, n: int = 3) -> DocumentDataset:
    for i in range(n):
        img = Image.new("RGB", (32, 32), color="white")
        img.save(tmp_path / f"doc_{i}.png")
        gt = {
            "image_path": f"doc_{i}.png",
            "text": "Hello World",
            "regions": [{"box": VALID_BOX, "text": "Hello World", "confidence": 1.0}],
        }
        (tmp_path / f"doc_{i}.json").write_text(json.dumps(gt))
    return DocumentDataset(tmp_path)


# ---------------------------------------------------------------------------
# evaluate_single
# ---------------------------------------------------------------------------

def test_evaluate_single_returns_all_keys():
    aug = _make_augmenter_mock()
    ocr = _make_ocr_mock()
    ev = Evaluator(aug, ocr)
    image = Image.new("RGB", (32, 32))
    result = ev.evaluate_single(image, "Hello World")
    for key in [
        "original_cer", "augmented_cer",
        "original_wer", "augmented_wer",
        "original_confidence", "augmented_confidence",
    ]:
        assert key in result


def test_evaluate_single_perfect_ocr():
    aug = _make_augmenter_mock()
    ocr = _make_ocr_mock("Hello World", score=1.0)
    ev = Evaluator(aug, ocr)
    result = ev.evaluate_single(Image.new("RGB", (32, 32)), "Hello World")
    assert result["original_cer"] == pytest.approx(0.0)
    assert result["original_confidence"] == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# evaluate_dataset
# ---------------------------------------------------------------------------

def test_evaluate_on_test_set(tmp_path):
    dataset = _create_sample_dataset(tmp_path, n=3)
    aug = _make_augmenter_mock()
    ocr = _make_ocr_mock("Hello World")
    ev = Evaluator(aug, ocr)
    result = ev.evaluate_dataset(dataset)
    assert result["n_samples"] == 3


def test_compute_aggregate_metrics(tmp_path):
    dataset = _create_sample_dataset(tmp_path, n=4)
    aug = _make_augmenter_mock()
    ocr = _make_ocr_mock("Hello World", score=0.9)
    ev = Evaluator(aug, ocr)
    result = ev.evaluate_dataset(dataset)
    assert "mean_original_cer" in result
    assert "std_original_cer" in result
    assert "mean_augmented_confidence" in result


def test_aggregate_empty_results():
    result = Evaluator._aggregate_results([])
    assert result == {"n_samples": 0}


def test_evaluate_dataset_empty(tmp_path):
    dataset = DocumentDataset(tmp_path)  # empty
    aug = _make_augmenter_mock()
    ocr = _make_ocr_mock()
    ev = Evaluator(aug, ocr)
    result = ev.evaluate_dataset(dataset)
    assert result["n_samples"] == 0
