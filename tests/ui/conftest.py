"""Shared fixtures for all UI tests."""

import io

import numpy as np
import pytest
from PIL import Image


@pytest.fixture
def blank_image():
    """224×224 white RGB image."""
    return Image.fromarray(np.full((224, 224, 3), 255, dtype=np.uint8))


@pytest.fixture
def small_image():
    """50×50 grey RGB image for lightweight tests."""
    return Image.fromarray(np.full((50, 50, 3), 128, dtype=np.uint8))


@pytest.fixture
def fake_uploaded_file(small_image):
    """Duck-typed UploadedFile with a PNG payload."""

    class _FakeFile:
        def __init__(self, img: Image.Image, name: str = "test.png"):
            self.name = name
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            self._data = buf.getvalue()

        def getvalue(self) -> bytes:
            return self._data

        def read(self) -> bytes:
            return self._data

    return _FakeFile(small_image)


@pytest.fixture
def sample_ocr_result():
    return {
        "text": "Hello World",
        "boxes": [[[10, 5], [80, 5], [80, 25], [10, 25]]],
        "scores": [0.95],
        "raw": None,
    }


@pytest.fixture
def sample_eval_metrics():
    return {
        "n_samples": 10,
        "mean_original_cer": 0.04,
        "std_original_cer": 0.01,
        "mean_augmented_cer": 0.12,
        "std_augmented_cer": 0.03,
        "mean_original_wer": 0.06,
        "std_original_wer": 0.01,
        "mean_augmented_wer": 0.18,
        "std_augmented_wer": 0.04,
        "mean_original_confidence": 0.94,
        "std_original_confidence": 0.02,
        "mean_augmented_confidence": 0.87,
        "std_augmented_confidence": 0.04,
    }


@pytest.fixture
def sample_training_log():
    return [
        {"step": 0, "reward": 0.10},
        {"step": 1000, "reward": 0.35},
        {"step": 2000, "reward": 0.52},
        {"step": 3000, "reward": 0.60, "cer": 0.09, "confidence": 0.88},
    ]
