"""Unit tests for BatchAugmenter.augment_multi_template."""

import pytest
from PIL import Image

from document_simulator.augmentation.batch import BatchAugmenter


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sources():
    """Three distinct 64×64 RGB images used as template sources."""
    return [Image.new("RGB", (64, 64), color=(i * 80, i * 80, i * 80)) for i in range(3)]


@pytest.fixture
def two_sources():
    return [Image.new("RGB", (64, 64), color=(0, 0, 0)), Image.new("RGB", (64, 64), color=(255, 255, 255))]


@pytest.fixture
def batch():
    return BatchAugmenter(num_workers=1)


# ---------------------------------------------------------------------------
# per_template mode
# ---------------------------------------------------------------------------


def test_per_template_output_count(batch, two_sources):
    """N=2 sources × copies_per_template=3 should produce exactly 6 outputs."""
    results = batch.augment_multi_template(
        two_sources,
        mode="per_template",
        copies_per_template=3,
    )
    assert len(results) == 6


def test_per_template_output_types(batch, two_sources):
    """Each result must be a (PIL.Image.Image, str) tuple."""
    results = batch.augment_multi_template(
        two_sources,
        mode="per_template",
        copies_per_template=2,
    )
    for item in results:
        assert isinstance(item, tuple) and len(item) == 2
        img, stem = item
        assert isinstance(img, Image.Image)
        assert isinstance(stem, str)


def test_per_template_copies_equal_one(batch, sources):
    """copies_per_template=1 should return N outputs (one per source)."""
    results = batch.augment_multi_template(
        sources,
        mode="per_template",
        copies_per_template=1,
    )
    assert len(results) == len(sources)


def test_per_template_grouping(batch, two_sources):
    """Results should be grouped by source: all copies of source 0 before source 1."""
    results = batch.augment_multi_template(
        two_sources,
        mode="per_template",
        copies_per_template=2,
    )
    # First 2 stems should be the same; last 2 stems should be the same
    assert results[0][1] == results[1][1]
    assert results[2][1] == results[3][1]


def test_per_template_zero_copies_raises(batch, sources):
    """copies_per_template=0 must raise ValueError."""
    with pytest.raises(ValueError, match="copies_per_template"):
        batch.augment_multi_template(sources, mode="per_template", copies_per_template=0)


# ---------------------------------------------------------------------------
# random_sample mode
# ---------------------------------------------------------------------------


def test_random_sample_output_count(batch, sources):
    """total_outputs=10 with 3 sources should produce exactly 10 outputs."""
    results = batch.augment_multi_template(
        sources,
        mode="random_sample",
        total_outputs=10,
        seed=99,
    )
    assert len(results) == 10


def test_random_sample_output_types(batch, sources):
    """Each result must be a (PIL.Image.Image, str) tuple."""
    results = batch.augment_multi_template(
        sources,
        mode="random_sample",
        total_outputs=5,
        seed=7,
    )
    for item in results:
        assert isinstance(item, tuple) and len(item) == 2
        img, stem = item
        assert isinstance(img, Image.Image)
        assert isinstance(stem, str)


def test_random_sample_seed_reproducibility(batch, sources):
    """Two calls with the same seed must return the same sequence of stems."""
    results_a = batch.augment_multi_template(
        sources,
        mode="random_sample",
        total_outputs=8,
        seed=42,
    )
    results_b = batch.augment_multi_template(
        sources,
        mode="random_sample",
        total_outputs=8,
        seed=42,
    )
    stems_a = [stem for _, stem in results_a]
    stems_b = [stem for _, stem in results_b]
    assert stems_a == stems_b


def test_random_sample_different_seeds_differ(batch, sources):
    """Two calls with different seeds should (almost certainly) return different sequences."""
    results_a = batch.augment_multi_template(
        sources,
        mode="random_sample",
        total_outputs=10,
        seed=1,
    )
    results_b = batch.augment_multi_template(
        sources,
        mode="random_sample",
        total_outputs=10,
        seed=2,
    )
    stems_a = [stem for _, stem in results_a]
    stems_b = [stem for _, stem in results_b]
    # Very unlikely to be identical with different seeds across 10 draws from 3 sources
    assert stems_a != stems_b


def test_random_sample_zero_total_raises(batch, sources):
    """total_outputs=0 must raise ValueError."""
    with pytest.raises(ValueError, match="total_outputs"):
        batch.augment_multi_template(sources, mode="random_sample", total_outputs=0)


# ---------------------------------------------------------------------------
# Common validation
# ---------------------------------------------------------------------------


def test_empty_sources_raises(batch):
    """Empty sources list must raise ValueError regardless of mode."""
    with pytest.raises(ValueError, match="sources"):
        batch.augment_multi_template([], mode="per_template", copies_per_template=1)


def test_invalid_mode_raises(batch, sources):
    """Unknown mode string must raise ValueError."""
    with pytest.raises(ValueError, match="mode"):
        batch.augment_multi_template(sources, mode="invalid_mode")


# ---------------------------------------------------------------------------
# Backward compatibility — augment_batch must be unchanged
# ---------------------------------------------------------------------------


def test_augment_batch_backward_compat(batch):
    """augment_batch still works exactly as before — returns List[Image] (no tuples)."""
    images = [Image.new("RGB", (32, 32), "white") for _ in range(3)]
    results = batch.augment_batch(images, parallel=False)
    assert len(results) == 3
    for r in results:
        assert isinstance(r, Image.Image)
