"""Tests for batch augmentation."""

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from document_simulator.augmentation.batch import BatchAugmenter


@pytest.fixture
def sample_images():
    return [Image.new("RGB", (64, 64), color="white") for _ in range(4)]


@pytest.fixture
def image_dir(tmp_path, sample_images):
    for i, img in enumerate(sample_images):
        img.save(tmp_path / f"img_{i:02d}.png")
    return tmp_path


# ---------------------------------------------------------------------------
# augment_batch — sequential
# ---------------------------------------------------------------------------

def test_batch_augmentation_sequential(sample_images):
    aug = BatchAugmenter(num_workers=1)
    results = aug.augment_batch(sample_images, parallel=False)
    assert len(results) == len(sample_images)
    for r in results:
        assert isinstance(r, Image.Image)
        assert r.size == (64, 64)


def test_batch_accepts_file_paths(image_dir):
    paths = list(image_dir.glob("*.png"))
    aug = BatchAugmenter(num_workers=1)
    results = aug.augment_batch(paths, parallel=False)
    assert len(results) == len(paths)


def test_batch_empty_list():
    aug = BatchAugmenter(num_workers=1)
    results = aug.augment_batch([], parallel=False)
    assert results == []


def test_batch_preserves_order(sample_images):
    aug = BatchAugmenter(num_workers=1)
    results = aug.augment_batch(sample_images, parallel=False)
    assert len(results) == len(sample_images)


# ---------------------------------------------------------------------------
# augment_directory
# ---------------------------------------------------------------------------

def test_augment_directory(image_dir, tmp_path):
    output_dir = tmp_path / "output"
    aug = BatchAugmenter(num_workers=1)
    out_paths = aug.augment_directory(image_dir, output_dir, parallel=False)
    assert len(out_paths) == 4
    for p in out_paths:
        assert p.exists()


def test_augment_directory_creates_output_dir(image_dir, tmp_path):
    output_dir = tmp_path / "new" / "nested" / "output"
    aug = BatchAugmenter(num_workers=1)
    aug.augment_directory(image_dir, output_dir, parallel=False)
    assert output_dir.exists()


def test_augment_directory_empty_input(tmp_path):
    output_dir = tmp_path / "out"
    aug = BatchAugmenter(num_workers=1)
    result = aug.augment_directory(tmp_path, output_dir, parallel=False)
    assert result == []


def test_augment_directory_output_count_matches_input(image_dir, tmp_path):
    input_count = len(list(image_dir.glob("*.png")))
    output_dir = tmp_path / "out"
    aug = BatchAugmenter(num_workers=1)
    out_paths = aug.augment_directory(image_dir, output_dir, parallel=False)
    assert len(out_paths) == input_count
