"""Unit tests for augmentation presets."""

import pytest

from document_simulator.augmentation.presets import AugmentationPreset, PresetFactory


@pytest.mark.parametrize("name", ["light", "medium", "heavy", "default"])
def test_preset_factory_known_names(name):
    """PresetFactory.create() returns an AugmentationPreset for known names."""
    preset = PresetFactory.create(name)
    assert isinstance(preset, AugmentationPreset)


def test_preset_factory_unknown_name_raises():
    """PresetFactory.create() raises KeyError for unknown preset name."""
    with pytest.raises(KeyError):
        PresetFactory.create("nonexistent")


@pytest.mark.parametrize("creator", [
    PresetFactory.create_light,
    PresetFactory.create_medium,
    PresetFactory.create_heavy,
])
def test_preset_has_all_phases(creator):
    """Every preset has non-empty ink, paper, and post phases."""
    preset = creator()
    assert len(preset.ink_phase) > 0
    assert len(preset.paper_phase) > 0
    assert len(preset.post_phase) > 0


@pytest.mark.parametrize("creator", [
    PresetFactory.create_light,
    PresetFactory.create_medium,
    PresetFactory.create_heavy,
])
def test_preset_parameter_bounds(creator):
    """All augmentation probabilities must be in [0.0, 1.0]."""
    preset = creator()
    for phase in [preset.ink_phase, preset.paper_phase, preset.post_phase]:
        for aug in phase:
            p = getattr(aug, "p", None)
            if p is not None:
                assert 0.0 <= p <= 1.0, (
                    f"{type(aug).__name__}.p={p} out of bounds in preset '{preset.name}'"
                )


def test_light_preset_name():
    assert PresetFactory.create_light().name == "light"


def test_medium_preset_name():
    assert PresetFactory.create_medium().name == "medium"


def test_heavy_preset_name():
    assert PresetFactory.create_heavy().name == "heavy"


def test_heavy_has_more_augmentations_than_light():
    """Heavy preset should have more or equal augmentations than light."""
    light = PresetFactory.create_light()
    heavy = PresetFactory.create_heavy()
    light_total = len(light.ink_phase) + len(light.paper_phase) + len(light.post_phase)
    heavy_total = len(heavy.ink_phase) + len(heavy.paper_phase) + len(heavy.post_phase)
    assert heavy_total >= light_total
