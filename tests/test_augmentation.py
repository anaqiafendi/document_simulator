"""Tests for document augmentation module."""

import numpy as np
import pytest
from PIL import Image

from document_simulator.augmentation import DocumentAugmenter


@pytest.fixture
def sample_image():
    """Create a sample image for testing."""
    return Image.new("RGB", (224, 224), color="white")


def test_augmenter_initialization():
    """Test DocumentAugmenter initialization."""
    augmenter = DocumentAugmenter(pipeline="default")
    assert augmenter.pipeline == "default"


def test_augment_pil_image(sample_image):
    """Test augmentation of PIL image."""
    augmenter = DocumentAugmenter()
    result = augmenter.augment(sample_image)
    assert isinstance(result, Image.Image)
    assert result.size == sample_image.size


def test_augment_numpy_array(sample_image):
    """Test augmentation of numpy array."""
    augmenter = DocumentAugmenter()
    image_array = np.array(sample_image)
    result = augmenter.augment(image_array)
    assert isinstance(result, np.ndarray)
    assert result.shape == image_array.shape
