"""Tests for DocumentDataset."""

import json
from pathlib import Path

import pytest
from PIL import Image

from document_simulator.data.datasets import DocumentDataset
from document_simulator.data.ground_truth import GroundTruth

VALID_BOX = [[0.0, 0.0], [100.0, 0.0], [100.0, 20.0], [0.0, 20.0]]


def _make_sample(directory: Path, name: str, text: str = "Hello") -> None:
    """Write a small PNG + matching JSON annotation into *directory*."""
    img = Image.new("RGB", (32, 32), color="white")
    img.save(directory / f"{name}.png")
    gt = {
        "image_path": f"{name}.png",
        "text": text,
        "regions": [{"box": VALID_BOX, "text": text, "confidence": 1.0}],
    }
    (directory / f"{name}.json").write_text(json.dumps(gt))


@pytest.fixture
def dataset_dir(tmp_path):
    """Create a small dataset directory with 5 samples."""
    for i in range(5):
        _make_sample(tmp_path, f"doc_{i:03d}", text=f"Document {i}")
    return tmp_path


# ---------------------------------------------------------------------------
# Basic loading
# ---------------------------------------------------------------------------

def test_load_custom_dataset(dataset_dir):
    ds = DocumentDataset(dataset_dir)
    assert len(ds) == 5


def test_dataset_iteration(dataset_dir):
    ds = DocumentDataset(dataset_dir)
    for image, gt in ds:
        assert isinstance(image, Image.Image)
        assert isinstance(gt, GroundTruth)
        assert len(gt.text) > 0


def test_dataset_getitem(dataset_dir):
    ds = DocumentDataset(dataset_dir)
    image, gt = ds[0]
    assert isinstance(image, Image.Image)
    assert isinstance(gt, GroundTruth)


def test_dataset_empty_dir(tmp_path):
    ds = DocumentDataset(tmp_path)
    assert len(ds) == 0


def test_dataset_ignores_files_without_annotation(tmp_path):
    # Only an image, no matching JSON/XML
    Image.new("RGB", (32, 32)).save(tmp_path / "lonely.png")
    ds = DocumentDataset(tmp_path)
    assert len(ds) == 0


# ---------------------------------------------------------------------------
# Train / val / test split
# ---------------------------------------------------------------------------

def test_dataset_train_val_split(dataset_dir):
    ds = DocumentDataset(dataset_dir)
    train, val, test = ds.split(val_ratio=0.2, test_ratio=0.2, seed=0)
    assert len(train) + len(val) + len(test) == len(ds)


def test_dataset_split_no_overlap(dataset_dir):
    ds = DocumentDataset(dataset_dir)
    train, val, test = ds.split(val_ratio=0.2, test_ratio=0.2, seed=0)
    train_paths = {str(p) for p, _ in train._samples}
    val_paths = {str(p) for p, _ in val._samples}
    test_paths = {str(p) for p, _ in test._samples}
    assert train_paths.isdisjoint(val_paths)
    assert train_paths.isdisjoint(test_paths)
    assert val_paths.isdisjoint(test_paths)


def test_dataset_split_reproducible(dataset_dir):
    ds = DocumentDataset(dataset_dir)
    train_a, _, _ = ds.split(seed=99)
    train_b, _, _ = ds.split(seed=99)
    assert [str(p) for p, _ in train_a._samples] == [str(p) for p, _ in train_b._samples]


# ---------------------------------------------------------------------------
# Transform
# ---------------------------------------------------------------------------

def test_dataset_transform_applied(dataset_dir):
    calls = []

    def my_transform(img):
        calls.append(1)
        return img

    ds = DocumentDataset(dataset_dir, transform=my_transform)
    _ = ds[0]
    assert calls == [1]
