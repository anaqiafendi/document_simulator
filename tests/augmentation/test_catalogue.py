"""Unit tests for the augmentation catalogue module."""

import pytest
from PIL import Image
import numpy as np
from document_simulator.augmentation.catalogue import (
    CATALOGUE,
    get_phase_augmentations,
    apply_single,
)

# Known broken in augraphy 8.2.6 on this platform — skip apply_single smoke tests
_SKIP_APPLY = {
    "Scribbles",   # matplotlib font_manager AttributeError
    "LensFlare",   # segfaults on all tested image sizes
}


@pytest.fixture
def tiny_image():
    return Image.fromarray(np.ones((64, 64, 3), dtype=np.uint8) * 200)


def test_catalogue_has_at_least_51_entries():
    assert len(CATALOGUE) >= 51


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


def test_catalogue_all_entries_have_slow_flag():
    for name, entry in CATALOGUE.items():
        assert "slow" in entry, f"{name} missing 'slow' flag"
        assert isinstance(entry["slow"], bool), f"{name} 'slow' must be bool"


def test_catalogue_ink_phase_new_entries():
    """Verify all 7 new ink-phase entries are present."""
    ink = get_phase_augmentations("ink")
    for name in ["InkMottling", "LowInkPeriodicLines", "LowInkRandomLines",
                 "Hollow", "Scribbles", "LinesDegradation", "BindingsAndFasteners"]:
        assert name in ink, f"{name} missing from ink phase"


def test_catalogue_paper_phase_new_entries():
    """Verify all 9 new paper-phase entries are present."""
    paper = get_phase_augmentations("paper")
    for name in ["BrightnessTexturize", "ColorPaper", "DirtyScreen", "Stains",
                 "NoisyLines", "PatternGenerator", "DelaunayTessellation",
                 "VoronoiTessellation", "PageBorder"]:
        assert name in paper, f"{name} missing from paper phase"


def test_catalogue_post_phase_new_entries():
    """Verify all 12 new post-phase entries are present."""
    post = get_phase_augmentations("post")
    for name in ["DepthSimulatedBlur", "DoubleExposure", "Faxify", "LCDScreenPattern",
                 "LensFlare", "LightingGradient", "Moire", "ReflectedLight",
                 "DotMatrix", "Rescale", "SectionShift", "Squish"]:
        assert name in post, f"{name} missing from post phase"


# DepthSimulatedBlur requires image larger than blur axes — use 256x256
_NEEDS_LARGER_IMAGE = {"DepthSimulatedBlur"}


@pytest.fixture
def medium_image():
    return Image.fromarray(np.ones((256, 256, 3), dtype=np.uint8) * 200)


@pytest.mark.parametrize("aug_name", [
    name for name in [
        "InkMottling", "LowInkPeriodicLines", "LowInkRandomLines", "Hollow",
        "LinesDegradation", "BindingsAndFasteners",
        "BrightnessTexturize", "ColorPaper", "DirtyScreen", "Stains",
        "NoisyLines", "PatternGenerator", "DelaunayTessellation",
        "VoronoiTessellation", "PageBorder",
        "DoubleExposure", "Faxify", "LCDScreenPattern",
        "LightingGradient", "Moire", "ReflectedLight",
        "DotMatrix", "Rescale", "SectionShift", "Squish",
    ] if name not in _SKIP_APPLY and name not in _NEEDS_LARGER_IMAGE
])
def test_apply_single_new_entries(aug_name, tiny_image):
    """Smoke test: apply_single should not raise for new catalogue entries."""
    result = apply_single(aug_name, tiny_image)
    assert isinstance(result, Image.Image)


def test_apply_single_depth_simulated_blur(medium_image):
    """DepthSimulatedBlur requires at least 256x256 due to seamlessClone minimum size."""
    result = apply_single("DepthSimulatedBlur", medium_image)
    assert isinstance(result, Image.Image)
