"""Integration tests for the augmentation → OCR pipeline.

These tests mock PaddleOCR so they run without heavy ML dependencies.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from PIL import Image

from document_simulator.augmentation import BatchAugmenter, DocumentAugmenter
from document_simulator.data.datasets import DocumentDataset

VALID_BOX = [[0.0, 0.0], [100.0, 0.0], [100.0, 20.0], [0.0, 20.0]]


def _make_ocr_mock(text="Hello World"):
    mock_ocr_instance = MagicMock()
    mock_ocr_instance.recognize.return_value = {
        "text": text,
        "boxes": [VALID_BOX],
        "scores": [0.95],
        "raw": None,
    }
    return mock_ocr_instance


# ---------------------------------------------------------------------------
# Augmentation → basic checks
# ---------------------------------------------------------------------------

def test_augmentation_pipeline_produces_image():
    """DocumentAugmenter returns an image of the same size."""
    augmenter = DocumentAugmenter(pipeline="light")
    image = Image.new("RGB", (128, 128), color="white")
    result = augmenter.augment(image)
    assert isinstance(result, Image.Image)
    assert result.size == (128, 128)


def test_augmentation_numpy_roundtrip():
    augmenter = DocumentAugmenter(pipeline="light")
    arr = np.full((64, 64, 3), 200, dtype=np.uint8)
    result = augmenter.augment(arr)
    assert isinstance(result, np.ndarray)
    assert result.shape == (64, 64, 3)


def test_augmentation_pipeline_to_ocr():
    """Augmented image can be passed to a (mock) OCR engine."""
    augmenter = DocumentAugmenter(pipeline="light")
    ocr = _make_ocr_mock("Hello World")

    image = Image.new("RGB", (128, 128), color="white")
    augmented = augmenter.augment(image)
    result = ocr.recognize(augmented)

    assert "Hello" in result["text"]
    assert len(result["boxes"]) > 0
    assert all(0 <= s <= 1 for s in result["scores"])


# ---------------------------------------------------------------------------
# Batch augmentation with directory
# ---------------------------------------------------------------------------

def test_batch_augmentation_with_saving(tmp_path):
    """BatchAugmenter writes augmented images to output directory."""
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()

    n = 3
    for i in range(n):
        Image.new("RGB", (64, 64), color="white").save(input_dir / f"img_{i}.png")

    aug = BatchAugmenter(num_workers=1)
    aug.augment_directory(input_dir, output_dir, parallel=False)

    assert len(list(output_dir.glob("*.png"))) == n


# ---------------------------------------------------------------------------
# Dataset loading → augmentation
# ---------------------------------------------------------------------------

def test_dataset_augmentation_pipeline(tmp_path):
    """Load dataset samples and augment them successfully."""
    for i in range(2):
        Image.new("RGB", (32, 32)).save(tmp_path / f"doc_{i}.png")
        gt = {"image_path": f"doc_{i}.png", "text": "text", "regions": []}
        (tmp_path / f"doc_{i}.json").write_text(json.dumps(gt))

    dataset = DocumentDataset(tmp_path)
    augmenter = DocumentAugmenter(pipeline="light")

    for image, gt in dataset:
        result = augmenter.augment(image)
        assert isinstance(result, Image.Image)
