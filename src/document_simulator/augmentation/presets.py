"""Augmentation pipeline presets for different degradation levels."""

from dataclasses import dataclass, field
from typing import List


# ---------------------------------------------------------------------------
# Parameter constants
# ---------------------------------------------------------------------------

class _LightParams:
    INK_BLEED_P = 0.2
    INK_BLEED_INTENSITY = (0.1, 0.3)
    LOW_LIGHT_P = 0.2
    NOISE_P = 0.3
    NOISE_SIGMA = (3, 5)
    COLOR_SHIFT_P = 0.2
    COLOR_SHIFT_RANGE = (5, 10)
    BRIGHTNESS_P = 0.3
    BRIGHTNESS_RANGE = (0.9, 1.1)
    JPEG_P = 0.2
    JPEG_QUALITY = (85, 95)


class _MediumParams:
    INK_BLEED_P = 0.5
    INK_BLEED_INTENSITY = (0.2, 0.5)
    LOW_LIGHT_P = 0.4
    MARKUP_P = 0.3
    NOISE_P = 0.5
    NOISE_SIGMA = (5, 10)
    COLOR_SHIFT_P = 0.4
    COLOR_SHIFT_RANGE = (10, 20)
    BRIGHTNESS_P = 0.5
    BRIGHTNESS_RANGE = (0.8, 1.2)
    GAMMA_P = 0.3
    JPEG_P = 0.4
    JPEG_QUALITY = (70, 85)


class _HeavyParams:
    INK_BLEED_P = 0.8
    INK_BLEED_INTENSITY = (0.4, 0.8)
    LOW_LIGHT_P = 0.6
    MARKUP_P = 0.5
    NOISE_P = 0.8
    NOISE_SIGMA = (10, 20)
    COLOR_SHIFT_P = 0.7
    COLOR_SHIFT_RANGE = (20, 40)
    BRIGHTNESS_P = 0.7
    BRIGHTNESS_RANGE = (0.6, 1.4)
    GAMMA_P = 0.5
    DITHERING_P = 0.4
    JPEG_P = 0.7
    JPEG_QUALITY = (40, 70)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class AugmentationPreset:
    """Defines an augmentation pipeline configuration.

    Ink, paper, and post-phase lists contain configured Augraphy augmentation
    objects ready to be passed to ``AugraphyPipeline``.
    """

    name: str
    ink_phase: List = field(default_factory=list)
    paper_phase: List = field(default_factory=list)
    post_phase: List = field(default_factory=list)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def _validate_preset(preset: AugmentationPreset) -> None:
    """Raise ValueError if any augmentation probability is out of [0, 1]."""
    for phase_name, phase in [
        ("ink_phase", preset.ink_phase),
        ("paper_phase", preset.paper_phase),
        ("post_phase", preset.post_phase),
    ]:
        for aug in phase:
            p = getattr(aug, "p", None)
            if p is not None and not (0.0 <= p <= 1.0):
                raise ValueError(
                    f"Preset '{preset.name}' {phase_name}: "
                    f"{type(aug).__name__}.p={p} is not in [0, 1]"
                )


class PresetFactory:
    """Factory for creating named augmentation presets."""

    @staticmethod
    def create(name: str) -> AugmentationPreset:
        """Create a preset by name.

        Args:
            name: One of 'light', 'medium', 'heavy', or 'default'.

        Returns:
            Configured :class:`AugmentationPreset`.

        Raises:
            KeyError: If *name* is not a known preset.
        """
        creators = {
            "light": PresetFactory.create_light,
            "medium": PresetFactory.create_medium,
            "heavy": PresetFactory.create_heavy,
            "default": PresetFactory.create_medium,
        }
        if name not in creators:
            raise KeyError(
                f"Unknown preset '{name}'. Valid options: {list(creators)}"
            )
        return creators[name]()

    @staticmethod
    def create_light() -> AugmentationPreset:
        """Light degradation — preserves high OCR accuracy (>95%)."""
        from augraphy.augmentations import (
            Brightness,
            ColorShift,
            InkBleed,
            Jpeg,
            LowLightNoise,
            NoiseTexturize,
        )

        p = _LightParams
        preset = AugmentationPreset(
            name="light",
            ink_phase=[
                InkBleed(p=p.INK_BLEED_P, intensity_range=p.INK_BLEED_INTENSITY),
                LowLightNoise(p=p.LOW_LIGHT_P),
            ],
            paper_phase=[
                NoiseTexturize(p=p.NOISE_P, sigma_range=p.NOISE_SIGMA),
                ColorShift(
                    p=p.COLOR_SHIFT_P,
                    color_shift_offset_x_range=p.COLOR_SHIFT_RANGE,
                    color_shift_offset_y_range=p.COLOR_SHIFT_RANGE,
                ),
            ],
            post_phase=[
                Brightness(p=p.BRIGHTNESS_P, brightness_range=p.BRIGHTNESS_RANGE),
                Jpeg(p=p.JPEG_P, quality_range=p.JPEG_QUALITY),
            ],
        )
        _validate_preset(preset)
        return preset

    @staticmethod
    def create_medium() -> AugmentationPreset:
        """Medium degradation — balanced realism and OCR accuracy."""
        from augraphy.augmentations import (
            Brightness,
            ColorShift,
            Gamma,
            InkBleed,
            Jpeg,
            LowLightNoise,
            Markup,
            NoiseTexturize,
        )

        p = _MediumParams
        preset = AugmentationPreset(
            name="medium",
            ink_phase=[
                InkBleed(p=p.INK_BLEED_P, intensity_range=p.INK_BLEED_INTENSITY),
                LowLightNoise(p=p.LOW_LIGHT_P),
                Markup(p=p.MARKUP_P),
            ],
            paper_phase=[
                NoiseTexturize(p=p.NOISE_P, sigma_range=p.NOISE_SIGMA),
                ColorShift(
                    p=p.COLOR_SHIFT_P,
                    color_shift_offset_x_range=p.COLOR_SHIFT_RANGE,
                    color_shift_offset_y_range=p.COLOR_SHIFT_RANGE,
                ),
            ],
            post_phase=[
                Brightness(p=p.BRIGHTNESS_P, brightness_range=p.BRIGHTNESS_RANGE),
                Gamma(p=p.GAMMA_P),
                Jpeg(p=p.JPEG_P, quality_range=p.JPEG_QUALITY),
            ],
        )
        _validate_preset(preset)
        return preset

    @staticmethod
    def create_heavy() -> AugmentationPreset:
        """Heavy degradation — significant visual change for robustness testing."""
        from augraphy.augmentations import (
            Brightness,
            ColorShift,
            Dithering,
            Gamma,
            InkBleed,
            Jpeg,
            LowLightNoise,
            Markup,
            NoiseTexturize,
        )

        p = _HeavyParams
        preset = AugmentationPreset(
            name="heavy",
            ink_phase=[
                InkBleed(p=p.INK_BLEED_P, intensity_range=p.INK_BLEED_INTENSITY),
                LowLightNoise(p=p.LOW_LIGHT_P),
                Markup(p=p.MARKUP_P),
            ],
            paper_phase=[
                NoiseTexturize(p=p.NOISE_P, sigma_range=p.NOISE_SIGMA),
                ColorShift(
                    p=p.COLOR_SHIFT_P,
                    color_shift_offset_x_range=p.COLOR_SHIFT_RANGE,
                    color_shift_offset_y_range=p.COLOR_SHIFT_RANGE,
                ),
            ],
            post_phase=[
                Brightness(p=p.BRIGHTNESS_P, brightness_range=p.BRIGHTNESS_RANGE),
                Gamma(p=p.GAMMA_P),
                Dithering(p=p.DITHERING_P),
                Jpeg(p=p.JPEG_P, quality_range=p.JPEG_QUALITY),
            ],
        )
        _validate_preset(preset)
        return preset
