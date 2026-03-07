"""Unit tests for the augmentation catalogue module."""

import pytest
from PIL import Image
import numpy as np
from document_simulator.augmentation.catalogue import (
    CATALOGUE,
    get_phase_augmentations,
    apply_single,
)


@pytest.fixture
def tiny_image():
    return Image.fromarray(np.ones((64, 64, 3), dtype=np.uint8) * 200)


def test_catalogue_has_at_least_20_entries():
    assert len(CATALOGUE) >= 20


def test_catalogue_entries_have_required_keys():
    for name, entry in CATALOGUE.items():
        assert "phase" in entry, f"{name} missing 'phase'"
        assert "display_name" in entry, f"{name} missing 'display_name'"
        assert "default_params" in entry, f"{name} missing 'default_params'"
        assert entry["phase"] in ("ink", "paper", "post"), f"{name} has invalid phase"


def test_get_phase_augmentations_ink():
    ink = get_phase_augmentations("ink")
    assert len(ink) > 0
    assert all(v["phase"] == "ink" for v in ink.values())


def test_get_phase_augmentations_post():
    post = get_phase_augmentations("post")
    assert len(post) > 0
    assert all(v["phase"] == "post" for v in post.values())


def test_apply_single_jpeg(tiny_image):
    result = apply_single("Jpeg", tiny_image)
    assert isinstance(result, Image.Image)
    assert result.size == tiny_image.size


def test_apply_single_gamma(tiny_image):
    result = apply_single("Gamma", tiny_image)
    assert isinstance(result, Image.Image)


def test_apply_single_brightness(tiny_image):
    result = apply_single("Brightness", tiny_image, {"numba_jit": 0, "p": 1.0})
    assert isinstance(result, Image.Image)


def test_apply_single_unknown_name_raises():
    with pytest.raises((KeyError, AttributeError)):
        apply_single("NonExistentAug", Image.new("RGB", (64, 64)))
