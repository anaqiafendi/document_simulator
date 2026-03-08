"""Static catalogue of Augraphy augmentation classes available in 8.2.6."""
from __future__ import annotations

from typing import Any

# Each entry: display_name, phase (ink/paper/post), default_params dict,
# slow (bool — skip in auto-thumbnail generation), description (1 sentence)
CATALOGUE: dict[str, dict[str, Any]] = {
    # ── Ink phase ─────────────────────────────────────────────────────────────
    "InkBleed": {
        "display_name": "Ink Bleed",
        "phase": "ink",
        "description": "Simulates ink bleeding through paper fibres.",
        "slow": False,
        "default_params": {"intensity_range": (0.1, 0.3), "p": 0.9},
    },
    "LowLightNoise": {
        "display_name": "Low Light / Fading",
        "phase": "ink",
        "description": "Darkens image to simulate faded or low-light document.",
        "slow": False,
        "default_params": {"p": 0.9},
    },
    "Markup": {
        "display_name": "Markup",
        "phase": "ink",
        "description": "Adds handwritten markup lines over text.",
        "slow": False,
        "default_params": {"num_lines_range": (2, 4), "markup_type": "strikethrough", "p": 0.9},
    },
    "BleedThrough": {
        "display_name": "Bleed Through",
        "phase": "ink",
        "description": "Simulates ink bleed-through from the reverse side of a page.",
        "slow": False,
        "default_params": {"intensity_range": (0.1, 0.3), "p": 0.9},
    },
    "BadPhotoCopy": {
        "display_name": "Bad Photocopy",
        "phase": "ink",
        "description": "Applies photocopy noise and darkening artifacts.",
        "slow": False,
        "default_params": {"p": 0.9},
    },
    "InkColorSwap": {
        "display_name": "Ink Color Swap",
        "phase": "ink",
        "description": "Swaps the ink color to a different hue.",
        "slow": False,
        "default_params": {"p": 0.9},
    },
    "InkShifter": {
        "display_name": "Ink Shifter",
        "phase": "ink",
        "description": "Shifts ink pixels to simulate smudging.",
        "slow": False,
        "default_params": {"text_shift_scale_range": (18, 27), "text_shift_factor_range": (1, 4), "p": 0.9},
    },
    "Letterpress": {
        "display_name": "Letterpress",
        "phase": "ink",
        "description": "Simulates letterpress printing texture.",
        "slow": False,
        "default_params": {"n_samples": (100, 300), "n_clusters": (300, 500), "p": 0.9},
    },
    "ShadowCast": {
        "display_name": "Shadow Cast",
        "phase": "ink",
        "description": "Adds a directional shadow over part of the document.",
        "slow": False,
        "default_params": {"shadow_side": "left", "shadow_opacity_range": (0.5, 0.8), "p": 0.9},
    },
    # ── Paper phase ───────────────────────────────────────────────────────────
    "NoiseTexturize": {
        "display_name": "Noise Texturize",
        "phase": "paper",
        "description": "Adds paper grain / noise texture to the background.",
        "slow": False,
        "default_params": {"sigma_range": (3, 10), "turbulence_range": (2, 5), "p": 0.9},
    },
    "ColorShift": {
        "display_name": "Color Shift",
        "phase": "paper",
        "description": "Shifts colour channels to simulate aged or scanned paper.",
        "slow": False,
        "default_params": {
            "color_shift_offset_x_range": (5, 15),
            "color_shift_offset_y_range": (5, 15),
            "color_shift_iterations": (2, 3),
            "p": 0.9,
        },
    },
    "DirtyDrum": {
        "display_name": "Dirty Drum",
        "phase": "paper",
        "description": "Adds drum-roll ink smears from a dirty scanner roller.",
        "slow": False,
        "default_params": {"line_width_range": (1, 4), "line_concentration": 0.1, "p": 0.9},
    },
    "DirtyRollers": {
        "display_name": "Dirty Rollers",
        "phase": "paper",
        "description": "Adds periodic roller marks from a dirty copying machine.",
        "slow": False,
        "default_params": {"line_width_range": (2, 6), "p": 0.9},
    },
    "SubtleNoise": {
        "display_name": "Subtle Noise",
        "phase": "paper",
        "description": "Adds fine random noise over the entire page.",
        "slow": False,
        "default_params": {"subtle_range": 10, "p": 0.9},
    },
    "WaterMark": {
        "display_name": "Watermark",
        "phase": "paper",
        "description": "Overlays a faint watermark text stamp.",
        "slow": False,
        "default_params": {
            "watermark_word": "DRAFT",
            "watermark_font_size": (60, 100),
            "watermark_rotation": (30, 60),
            "watermark_font_type": 0,  # cv2.FONT_HERSHEY_SIMPLEX
            "p": 0.9,
        },
    },
    # ── Post phase ────────────────────────────────────────────────────────────
    "Jpeg": {
        "display_name": "JPEG Compression",
        "phase": "post",
        "description": "Applies lossy JPEG compression artifacts.",
        "slow": False,
        "default_params": {"quality_range": (40, 80), "p": 0.9},
    },
    "Brightness": {
        "display_name": "Brightness",
        "phase": "post",
        "description": "Adjusts overall image brightness.",
        "slow": False,
        "default_params": {"brightness_range": (0.7, 1.3), "numba_jit": 0, "p": 0.9},
    },
    "Gamma": {
        "display_name": "Gamma",
        "phase": "post",
        "description": "Applies gamma correction to simulate scanner exposure.",
        "slow": False,
        "default_params": {"gamma_range": (0.5, 2.0), "p": 0.9},
    },
    "Dithering": {
        "display_name": "Dithering",
        "phase": "post",
        "description": "Converts image to a dithered halftone pattern.",
        "slow": False,
        "default_params": {"numba_jit": 0, "p": 0.9},
    },
    "GlitchEffect": {
        "display_name": "Glitch Effect",
        "phase": "post",
        "description": "Adds digital glitch / data-corruption artifacts.",
        "slow": False,
        "default_params": {"glitch_number_range": (8, 16), "glitch_size_range": (5, 50), "p": 0.9},
    },
    "Geometric": {
        "display_name": "Geometric Distortion",
        "phase": "post",
        "description": "Applies rotation and perspective distortion to the page.",
        "slow": False,
        "default_params": {"rotate_range": (-10, 10), "p": 0.9},
    },
    "Folding": {
        "display_name": "Folding",
        "phase": "post",
        "description": "Simulates a page fold crease.",
        "slow": False,
        "default_params": {"fold_count": 1, "p": 0.9},
    },
    "BookBinding": {
        "display_name": "Book Binding",
        "phase": "post",
        "description": "Simulates book-binding curvature and shadow.",
        "slow": False,
        "default_params": {"p": 0.9},
    },
}


def get_phase_augmentations(phase: str) -> dict[str, dict]:
    """Return CATALOGUE entries for a given phase (ink/paper/post).

    Args:
        phase: One of "ink", "paper", or "post".

    Returns:
        Filtered dict of CATALOGUE entries for the given phase.
    """
    return {k: v for k, v in CATALOGUE.items() if v["phase"] == phase}


def apply_single(aug_name: str, image: Any, params: dict | None = None) -> Any:
    """Apply a single augmentation by catalogue name.

    Args:
        aug_name: Key in CATALOGUE (e.g. "InkBleed").
        image: PIL Image or numpy array.
        params: Override default_params. If None, uses CATALOGUE defaults.

    Returns:
        Augmented PIL Image (if input was PIL) or numpy array.

    Raises:
        KeyError: If aug_name is not in CATALOGUE.
        AttributeError: If aug_name is not a class in augraphy.augmentations.
    """
    import numpy as np
    from PIL import Image as PILImage
    from augraphy import AugraphyPipeline
    import augraphy.augmentations as aug_module

    entry = CATALOGUE[aug_name]
    effective_params = {**entry["default_params"], **(params or {})}

    aug_class = getattr(aug_module, aug_name)
    aug_instance = aug_class(**effective_params)

    input_is_pil = isinstance(image, PILImage.Image)
    arr = np.array(image.convert("RGB")) if input_is_pil else image

    phase = entry["phase"]
    pipeline = AugraphyPipeline(
        ink_phase=[aug_instance] if phase == "ink" else [],
        paper_phase=[aug_instance] if phase == "paper" else [],
        post_phase=[aug_instance] if phase == "post" else [],
    )
    result = pipeline(arr)
    return PILImage.fromarray(result) if input_is_pil else result
