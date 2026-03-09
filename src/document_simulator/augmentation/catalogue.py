"""Static catalogue of Augraphy augmentation classes available in 8.2.6."""
from __future__ import annotations

from typing import Any

# Each entry: display_name, phase (ink/paper/post), default_params dict,
# slow (bool — skip in auto-thumbnail generation), description (1 sentence)
#
# Known platform issues in augraphy 8.2.6:
#   - Scribbles: crashes with "module 'matplotlib' has no attribute 'font_manager'"
#     on some matplotlib versions; marked slow=True to skip auto-thumbnail.
#   - LensFlare: segfaults on all tested image sizes due to a native code bug;
#     marked slow=True to skip auto-thumbnail generation.
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
    # ── Ink phase (additional) ────────────────────────────────────────────────
    "InkMottling": {
        "display_name": "Ink Mottling",
        "phase": "ink",
        "description": "Adds mottling texture to ink areas, simulating uneven ink absorption.",
        "slow": False,
        "default_params": {
            "ink_mottling_alpha_range": (0.2, 0.3),
            "ink_mottling_noise_scale_range": (2, 2),
            "ink_mottling_gaussian_kernel_range": (3, 5),
            "p": 0.9,
        },
    },
    "LowInkPeriodicLines": {
        "display_name": "Low Ink Periodic Lines",
        "phase": "ink",
        "description": "Simulates low-ink streaks that appear periodically along lines.",
        "slow": False,
        "default_params": {
            "count_range": (2, 5),
            "period_range": (10, 30),
            "use_consistent_lines": True,
            "noise_probability": 0.1,
            "p": 0.9,
        },
    },
    "LowInkRandomLines": {
        "display_name": "Low Ink Random Lines",
        "phase": "ink",
        "description": "Simulates low-ink streaks that appear at random positions.",
        "slow": False,
        "default_params": {
            "count_range": (5, 10),
            "use_consistent_lines": True,
            "noise_probability": 0.1,
            "p": 0.9,
        },
    },
    "Hollow": {
        "display_name": "Hollow",
        "phase": "ink",
        "description": "Removes ink from the centre of characters, leaving hollow outlines.",
        "slow": False,
        "default_params": {
            "hollow_median_kernel_value_range": (71, 101),
            "hollow_min_width_range": (1, 2),
            "hollow_max_width_range": (150, 200),
            "hollow_min_height_range": (1, 2),
            "hollow_max_height_range": (150, 200),
            "hollow_min_area_range": (10, 20),
            "hollow_max_area_range": (2000, 5000),
            "hollow_dilation_kernel_size_range": (1, 2),
            "p": 0.9,
        },
    },
    "Scribbles": {
        "display_name": "Scribbles",
        "phase": "ink",
        "description": "Overlays handwritten scribble marks on the document.",
        "slow": True,  # augraphy 8.2.6: crashes with some matplotlib versions
        "default_params": {
            "scribbles_type": "random",
            "scribbles_ink": "random",
            "scribbles_location": "random",
            "scribbles_size_range": (400, 600),
            "scribbles_count_range": (1, 6),
            "scribbles_thickness_range": (1, 3),
            "scribbles_brightness_change": [32, 64, 128],
            "p": 0.9,
        },
    },
    "LinesDegradation": {
        "display_name": "Lines Degradation",
        "phase": "ink",
        "description": "Degrades horizontal or vertical lines to simulate worn print.",
        "slow": False,
        "default_params": {
            "line_roi": (0.0, 0.0, 1.0, 1.0),
            "line_gradient_range": (32, 255),
            "line_gradient_direction": (0, 2),
            "line_split_probability": (0.2, 0.4),
            "line_replacement_value": (250, 255),
            "line_min_length": (30, 40),
            "line_long_to_short_ratio": (5, 7),
            "line_replacement_probability": (0.4, 0.5),
            "line_replacement_thickness": (1, 3),
            "p": 0.9,
        },
    },
    "BindingsAndFasteners": {
        "display_name": "Bindings and Fasteners",
        "phase": "ink",
        "description": "Overlays binding or fastener shadows (staples, punch holes, rings).",
        "slow": True,
        "default_params": {
            "overlay_types": "random",
            "foreground": None,
            "effect_type": "random",
            "width_range": "random",
            "height_range": "random",
            "angle_range": (-30, 30),
            "ntimes": (2, 6),
            "nscales": (1.0, 1.5),
            "edge": "random",
            "edge_offset": (5, 20),
            "use_figshare_library": 0,
            "p": 0.9,
        },
    },
    # ── Paper phase (additional) ──────────────────────────────────────────────
    "BrightnessTexturize": {
        "display_name": "Brightness Texturize",
        "phase": "paper",
        "description": "Adds subtle brightness variation texture to simulate paper grain.",
        "slow": False,
        "default_params": {
            "texturize_range": (0.8, 0.99),
            "deviation": 0.08,
            "p": 0.9,
        },
    },
    "ColorPaper": {
        "display_name": "Color Paper",
        "phase": "paper",
        "description": "Tints the page background to simulate coloured paper stock.",
        "slow": False,
        "default_params": {
            "hue_range": (28, 45),
            "saturation_range": (10, 40),
            "p": 0.9,
        },
    },
    "PaperFactory": {
        "display_name": "Paper Factory",
        "phase": "paper",
        "description": "Generates a procedural paper texture and overlays it onto the document.",
        "slow": False,
        "default_params": {
            "generate_texture": 1,
            "texture_enable_color": 0,
            "texture_color_blend_method": "overlay",
            "p": 0.9,
        },
    },
    "DirtyScreen": {
        "display_name": "Dirty Screen",
        "phase": "paper",
        "description": "Adds clustered dust and smudge artifacts to simulate a dirty scanner screen.",
        "slow": False,
        "default_params": {
            "n_clusters": (50, 100),
            "n_samples": (2, 20),
            "std_range": (1, 5),
            "value_range": (150, 250),
            "p": 0.9,
        },
    },
    "Stains": {
        "display_name": "Stains",
        "phase": "paper",
        "description": "Overlays organic stain blobs on the paper surface.",
        "slow": False,
        "default_params": {
            "stains_type": "random",
            "stains_blend_method": "darken",
            "stains_blend_alpha": 0.5,
            "p": 0.9,
        },
    },
    "NoisyLines": {
        "display_name": "Noisy Lines",
        "phase": "paper",
        "description": "Draws faint noisy lines over the page, simulating ruled paper or scan artifacts.",
        "slow": False,
        "default_params": {
            "noisy_lines_direction": "random",
            "noisy_lines_location": "random",
            "noisy_lines_number_range": (5, 20),
            "noisy_lines_color": (0, 0, 0),
            "noisy_lines_thickness_range": (1, 2),
            "noisy_lines_random_noise_intensity_range": (0.01, 0.1),
            "noisy_lines_length_interval_range": (0, 100),
            "noisy_lines_gaussian_kernel_value_range": (3, 5),
            "noisy_lines_overlay_method": "ink_to_paper",
            "p": 0.9,
        },
    },
    "PatternGenerator": {
        "display_name": "Pattern Generator",
        "phase": "paper",
        "description": "Generates and overlays a mathematical tiling pattern on the background.",
        "slow": False,
        "default_params": {
            "imgx": 512,
            "imgy": 512,
            "n_rotation_range": (10, 15),
            "color": "random",
            "alpha_range": (0.25, 0.5),
            "numba_jit": 0,
            "p": 0.9,
        },
    },
    "DelaunayTessellation": {
        "display_name": "Delaunay Tessellation",
        "phase": "paper",
        "description": "Overlays a Delaunay triangulation pattern to simulate textured paper.",
        "slow": True,
        "default_params": {
            "n_points_range": (500, 800),
            "n_horizontal_points_range": (500, 800),
            "n_vertical_points_range": (500, 800),
            "noise_type": "random",
            "color_list": "default",
            "color_list_alternate": "default",
            "p": 0.9,
        },
    },
    "VoronoiTessellation": {
        "display_name": "Voronoi Tessellation",
        "phase": "paper",
        "description": "Overlays a Voronoi diagram pattern on the paper background.",
        "slow": True,
        "default_params": {
            "mult_range": (50, 80),
            "seed": 19829813472,
            "num_cells_range": (500, 1000),
            "noise_type": "random",
            "background_value": (200, 255),
            "numba_jit": 0,
            "p": 0.9,
        },
    },
    "PageBorder": {
        "display_name": "Page Border",
        "phase": "paper",
        "description": "Adds realistic page border shadows and curl effects from scanning.",
        "slow": True,
        "default_params": {
            "page_border_width_height": "random",
            "page_border_color": (0, 0, 0),
            "page_border_background_color": (0, 0, 0),
            "page_border_use_cache_images": 0,
            "page_border_trim_sides": (0, 0, 0, 0),
            "page_numbers": "random",
            "page_rotate_angle_in_order": 1,
            "page_rotation_angle_range": (-3, 3),
            "curve_frequency": (0, 1),
            "curve_height": (2, 4),
            "curve_length_one_side": (50, 100),
            "same_page_border": 1,
            "numba_jit": 0,
            "p": 0.9,
        },
    },
    # ── Post phase (additional) ───────────────────────────────────────────────
    "DepthSimulatedBlur": {
        "display_name": "Depth Simulated Blur",
        "phase": "post",
        "description": "Blurs an elliptical region to simulate depth-of-field camera defocus.",
        "slow": False,
        "default_params": {
            "blur_center": "random",
            "blur_major_axes_length_range": (120, 200),
            "blur_minor_axes_length_range": (120, 200),
            "blur_iteration_range": (8, 10),
            "p": 0.9,
        },
    },
    "DoubleExposure": {
        "display_name": "Double Exposure",
        "phase": "post",
        "description": "Overlays a shifted ghost copy of the image to simulate double exposure.",
        "slow": False,
        "default_params": {
            "gaussian_kernel_range": (9, 12),
            "offset_direction": "random",
            "offset_range": (18, 25),
            "p": 0.9,
        },
    },
    "Faxify": {
        "display_name": "Faxify",
        "phase": "post",
        "description": "Simulates fax transmission degradation with halftoning and monochroming.",
        "slow": False,
        "default_params": {
            "scale_range": (1.0, 1.25),
            "monochrome": -1,
            "monochrome_method": "random",
            "monochrome_arguments": {},
            "halftone": -1,
            "invert": 1,
            "half_kernel_size": (1, 1),
            "angle": (0, 360),
            "sigma": (1, 3),
            "numba_jit": 0,
            "p": 0.9,
        },
    },
    "LCDScreenPattern": {
        "display_name": "LCD Screen Pattern",
        "phase": "post",
        "description": "Overlays an LCD pixel grid pattern to simulate a screen photograph.",
        "slow": False,
        "default_params": {
            "pattern_type": "random",
            "pattern_value_range": (0, 16),
            "pattern_skip_distance_range": (3, 5),
            "pattern_overlay_method": "darken",
            "pattern_overlay_alpha": 0.3,
            "p": 0.9,
        },
    },
    "LensFlare": {
        "display_name": "Lens Flare",
        "phase": "post",
        "description": "Adds a lens flare artifact to simulate camera or scanner lighting.",
        "slow": True,  # augraphy 8.2.6: segfaults on all tested image sizes
        "default_params": {
            "lens_flare_location": "random",
            "lens_flare_color": "random",
            "lens_flare_size": (0.5, 5),
            "numba_jit": 0,
            "p": 0.9,
        },
    },
    "LightingGradient": {
        "display_name": "Lighting Gradient",
        "phase": "post",
        "description": "Applies a directional brightness gradient to simulate uneven illumination.",
        "slow": False,
        "default_params": {
            "light_position": None,
            "direction": None,
            "max_brightness": 255,
            "min_brightness": 0,
            "mode": "gaussian",
            "linear_decay_rate": None,
            "transparency": None,
            "numba_jit": 0,
            "p": 0.9,
        },
    },
    "Moire": {
        "display_name": "Moire Pattern",
        "phase": "post",
        "description": "Adds a moire interference pattern to simulate scan artifacts.",
        "slow": False,
        "default_params": {
            "moire_density": (15, 20),
            "moire_blend_method": "normal",
            "moire_blend_alpha": 0.1,
            "numba_jit": 0,
            "p": 0.9,
        },
    },
    "ReflectedLight": {
        "display_name": "Reflected Light",
        "phase": "post",
        "description": "Adds a bright elliptical reflection spot to simulate glossy surface reflections.",
        "slow": True,  # ZeroDivisionError in augraphy 8.2.6 on small images
        "default_params": {
            "reflected_light_smoothness": 0.8,
            "reflected_light_internal_radius_range": (0.0, 0.2),
            "reflected_light_external_radius_range": (0.1, 0.8),
            "reflected_light_minor_major_ratio_range": (0.9, 1.0),
            "reflected_light_color": (255, 255, 255),
            "reflected_light_internal_max_brightness_range": (0.9, 1.0),
            "reflected_light_external_max_brightness_range": (0.75, 0.9),
            "reflected_light_location": "random",
            "reflected_light_ellipse_angle_range": (0, 360),
            "reflected_light_gaussian_kernel_size_range": (5, 310),
            "p": 0.9,
        },
    },
    "DotMatrix": {
        "display_name": "Dot Matrix",
        "phase": "post",
        "description": "Converts text regions to dot-matrix print style.",
        "slow": False,
        "default_params": {
            "dot_matrix_shape": "random",
            "dot_matrix_dot_width_range": (3, 19),
            "dot_matrix_dot_height_range": (3, 19),
            "dot_matrix_min_width_range": (1, 2),
            "dot_matrix_max_width_range": (150, 200),
            "dot_matrix_min_height_range": (1, 2),
            "dot_matrix_max_height_range": (150, 200),
            "dot_matrix_min_area_range": (10, 20),
            "dot_matrix_max_area_range": (2000, 5000),
            "dot_matrix_median_kernel_value_range": (128, 255),
            "dot_matrix_gaussian_kernel_value_range": (1, 3),
            "dot_matrix_rotate_value_range": (0, 360),
            "numba_jit": 0,
            "p": 0.9,
        },
    },
    "Rescale": {
        "display_name": "Rescale",
        "phase": "post",
        "description": "Resamples the image to a target DPI, simulating resolution changes.",
        "slow": False,
        "default_params": {
            "target_dpi": 300,
            "p": 0.9,
        },
    },
    "SectionShift": {
        "display_name": "Section Shift",
        "phase": "post",
        "description": "Shifts horizontal bands of the image to simulate misaligned scanning.",
        "slow": False,
        "default_params": {
            "section_shift_number_range": (3, 5),
            "section_shift_locations": "random",
            "section_shift_x_range": (-10, 10),
            "section_shift_y_range": (-10, 10),
            "section_shift_fill_value": -1,
            "p": 0.9,
        },
    },
    "Squish": {
        "display_name": "Squish",
        "phase": "post",
        "description": "Squishes rows or columns together to simulate compression distortion.",
        "slow": False,
        "default_params": {
            "squish_direction": "random",
            "squish_location": "random",
            "squish_number_range": (5, 10),
            "squish_distance_range": (5, 7),
            "squish_line": "random",
            "squish_line_thickness_range": (1, 1),
            "p": 0.9,
        },
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
    import cv2
    import numpy as np
    from PIL import Image as PILImage
    import augraphy.augmentations as aug_module

    entry = CATALOGUE[aug_name]
    effective_params = {**entry["default_params"], **(params or {})}

    input_is_pil = isinstance(image, PILImage.Image)
    arr = np.array(image.convert("RGB")) if input_is_pil else image

    # PaperFactory lives in augraphy.base and returns a texture, not an augmented image.
    if aug_name == "PaperFactory":
        from augraphy.base.paperfactory import PaperFactory
        aug_instance = PaperFactory(**effective_params)
        texture = aug_instance(arr)
        if texture is None:
            result = arr
        else:
            # texture may be 2D grayscale or 3D RGB depending on texture_enable_color
            h, w = arr.shape[:2]
            tex = np.array(texture)
            # Ensure 2D before resize to avoid cv2 producing unexpected shapes
            if tex.ndim == 3:
                tex_gray = cv2.cvtColor(tex, cv2.COLOR_RGB2GRAY) if tex.shape[2] == 3 else tex[:, :, 0]
                tex_resized = cv2.resize(tex_gray, (w, h), interpolation=cv2.INTER_LINEAR)
                texture_rgb = np.stack([tex_resized] * 3, axis=-1).astype(np.float32) / 255.0
            else:
                tex_resized = cv2.resize(tex, (w, h), interpolation=cv2.INTER_LINEAR)
                texture_rgb = np.stack([tex_resized] * 3, axis=-1).astype(np.float32) / 255.0
            base = arr.astype(np.float32) / 255.0
            blended = np.clip(base * texture_rgb * 2.0, 0.0, 1.0)
            result = (blended * 255).astype(np.uint8)
    else:
        aug_class = getattr(aug_module, aug_name)
        aug_instance = aug_class(**effective_params)
        result = aug_instance(arr)
        # Some augraphy augmentations return None (pipeline-mode only); fall back to original.
        if result is None:
            result = arr

    return PILImage.fromarray(result) if input_is_pil else result
