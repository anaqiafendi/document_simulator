"""Unit tests for DocumentAugmenter custom_augmentations parameter."""

import numpy as np
from PIL import Image
from document_simulator.augmentation.augmenter import DocumentAugmenter
import augraphy.augmentations as aug_module


def make_image():
    return Image.fromarray(np.ones((64, 64, 3), dtype=np.uint8) * 200)


def test_custom_augmentations_runs_without_error():
    aug = DocumentAugmenter(
        custom_augmentations=[aug_module.Jpeg(quality_range=(60, 80), p=1.0)]
    )
    result = aug.augment(make_image())
    assert isinstance(result, Image.Image)


def test_custom_augmentations_empty_list_returns_image():
    aug = DocumentAugmenter(custom_augmentations=[])
    result = aug.augment(make_image())
    assert isinstance(result, Image.Image)


def test_preset_still_works_when_custom_is_none():
    aug = DocumentAugmenter(pipeline="light")
    result = aug.augment(make_image())
    assert isinstance(result, Image.Image)
