"""Static catalogue of Augraphy augmentation classes available in 8.2.6."""
from __future__ import annotations

from typing import Any

# Each entry: display_name, phase (ink/paper/post), default_params dict,
# slow (bool — skip in auto-thumbnail generation), description (1 sentence)
#
# Known platform issues in augraphy 8.2.6:
#   - Scribbles: needs matplotlib.font_manager pre-imported before first call;
#     fixed in apply_single() by importing it eagerly.
#   - LensFlare: segfaults unconditionally (numba parallel crash in native code);
#     marked disabled=True — hidden from UI and skipped by apply_single().
#   - Moire, DotMatrix: numba_jit=0 causes 'get_call_template' crash; fixed to 1.
# disabled=True entries are hidden from the API catalogue listing.
CATALOGUE: dict[str, dict[str, Any]] = {
    # ── Ink phase ─────────────────────────────────────────────────────────────
    "InkBleed": {
        "display_name": "Ink Bleed",
        "phase": "ink",
        "description": "Ink seeps outward from the printed characters, creating fuzzy or feathered edges — common in cheap or wet paper.",
        "slow": False,
        "default_params": {"intensity_range": (0.1, 0.3), "p": 0.9},
    },
    "LowLightNoise": {
        "display_name": "Ink Fading",
        "phase": "ink",
        "description": "The printed ink appears faded or washed out, as though the document was left in sunlight or printed with low toner.",
        "slow": False,
        "default_params": {"p": 0.9},
    },
    "Markup": {
        "display_name": "Handwritten Markup",
        "phase": "ink",
        "description": "Handwritten strikethrough lines or annotations are drawn over the printed text, as if someone reviewed and marked up the document.",
        "slow": False,
        "default_params": {"num_lines_range": (2, 4), "markup_type": "strikethrough", "p": 0.9},
    },
    "BleedThrough": {
        "display_name": "Reverse-Side Bleed Through",
        "phase": "ink",
        "description": "Text or images from the other side of the page show through as a ghost image — common in thin paper receipts and newspapers.",
        "slow": False,
        "default_params": {"intensity_range": (0.1, 0.3), "p": 0.9},
    },
    "BadPhotoCopy": {
        "display_name": "Poor Photocopy Quality",
        "phase": "ink",
        "description": "The document looks like a bad photocopy — uneven darkness, smearing, and noise typical of a worn-out office copier.",
        "slow": False,
        "default_params": {"p": 0.9},
    },
    "InkColorSwap": {
        "display_name": "Ink Colour Change",
        "phase": "ink",
        "description": "The ink colour shifts to an unusual hue, as might happen with a malfunctioning colour printer or age-related chemical change.",
        "slow": False,
        "default_params": {"p": 0.9},
    },
    "InkShifter": {
        "display_name": "Ink Smear",
        "phase": "ink",
        "description": "Ink is smeared across the page as if the paper was touched before it dried, displacing characters slightly.",
        "slow": False,
        "default_params": {"text_shift_scale_range": (18, 27), "text_shift_factor_range": (1, 4), "p": 0.9},
    },
    "Letterpress": {
        "display_name": "Letterpress Print Texture",
        "phase": "ink",
        "description": "Characters show the embossed, uneven ink distribution of old letterpress or typewriter printing.",
        "slow": False,
        "default_params": {"n_samples": (100, 300), "n_clusters": (300, 500), "p": 0.9},
    },
    "ShadowCast": {
        "display_name": "Shadow from Holding",
        "phase": "ink",
        "description": "A shadow falls across one side of the document, as if someone's hand was partly blocking the scanner light.",
        "slow": False,
        "default_params": {"shadow_side": "left", "shadow_opacity_range": (0.5, 0.8), "p": 0.9},
    },
    # ── Paper phase ───────────────────────────────────────────────────────────
    "NoiseTexturize": {
        "display_name": "Paper Grain",
        "phase": "paper",
        "description": "Random grain is added to the page background to simulate rough, recycled, or textured paper stock.",
        "slow": False,
        "default_params": {"sigma_range": (3, 10), "turbulence_range": (2, 5), "p": 0.9},
    },
    "ColorShift": {
        "display_name": "Scanner Colour Drift",
        "phase": "paper",
        "description": "The colour channels are slightly misaligned, producing a faint colour fringe around text — seen in poorly calibrated or ageing scanners.",
        "slow": False,
        "default_params": {
            "color_shift_offset_x_range": (5, 15),
            "color_shift_offset_y_range": (5, 15),
            "color_shift_iterations": (2, 3),
            "p": 0.9,
        },
    },
    "DirtyDrum": {
        "display_name": "Scanner Drum Smear",
        "phase": "paper",
        "description": "Repeating dark streaks run along the page, left by ink build-up on a scanner or photocopier drum roller.",
        "slow": False,
        "default_params": {"line_width_range": (1, 4), "line_concentration": 0.1, "p": 0.9},
    },
    "DirtyRollers": {
        "display_name": "Roller Feed Marks",
        "phase": "paper",
        "description": "Periodic marks appear across the page where dirty feed rollers on a photocopier or printer pressed against the paper.",
        "slow": False,
        "default_params": {"line_width_range": (2, 6), "p": 0.9},
    },
    "SubtleNoise": {
        "display_name": "Fine Background Noise",
        "phase": "paper",
        "description": "Very fine random speckle noise covers the page, mimicking sensor noise in a digital camera or low-quality scanner.",
        "slow": False,
        "default_params": {"subtle_range": 10, "p": 0.9},
    },
    "WaterMark": {
        "display_name": "Document Stamp / Watermark",
        "phase": "paper",
        "description": "A faint stamp word such as DRAFT or CONFIDENTIAL is overlaid diagonally across the document.",
        "slow": False,
        "default_params": {
            "watermark_word": "DRAFT",
            "watermark_font_size": (60, 100),
            "watermark_rotation": (30, 60),
            "watermark_font_type": 0,  # cv2.FONT_HERSHEY_SIMPLEX
            "p": 0.9,
        },
    },
    # ── Post phase (Capture Conditions) ───────────────────────────────────────
    "Jpeg": {
        "display_name": "JPEG Compression Artefacts",
        "phase": "post",
        "description": "Blocky distortion artefacts appear across the image, typical of saving a scan at low JPEG quality or sending via messaging apps.",
        "slow": False,
        "default_params": {"quality_range": (40, 80), "p": 0.9},
    },
    "Brightness": {
        "display_name": "Exposure Variation",
        "phase": "post",
        "description": "The overall image is made brighter or darker to simulate different lighting conditions when photographing a document.",
        "slow": False,
        "default_params": {"brightness_range": (0.7, 1.3), "numba_jit": 0, "p": 0.9},
    },
    "Gamma": {
        "display_name": "Scanner Exposure Correction",
        "phase": "post",
        "description": "Gamma is adjusted to simulate an over- or under-exposed scan, shifting midtone brightness non-linearly.",
        "slow": False,
        "default_params": {"gamma_range": (0.5, 2.0), "p": 0.9},
    },
    "Dithering": {
        "display_name": "Halftone / Dithered Print",
        "phase": "post",
        "description": "The image is converted to a dot pattern resembling a newspaper photograph or a low-resolution fax printout.",
        "slow": False,
        "default_params": {"numba_jit": 0, "p": 0.9},
    },
    "GlitchEffect": {
        "display_name": "Digital Glitch / Corruption",
        "phase": "post",
        "description": "Horizontal bands of the image are shifted or corrupted, mimicking data-transmission errors or a damaged image file.",
        "slow": False,
        "default_params": {"glitch_number_range": (8, 16), "glitch_size_range": (5, 50), "p": 0.9},
    },
    "Geometric": {
        "display_name": "Skew and Perspective Warp",
        "phase": "post",
        "description": "The document is rotated or warped as if it was photographed at an angle — the most common real-world capture problem.",
        "slow": False,
        "default_params": {"rotate_range": (-10, 10), "p": 0.9},
    },
    "Folding": {
        "display_name": "Page Fold Crease",
        "phase": "post",
        "description": "A fold line crease appears across the page, as if the document was folded in half before being scanned.",
        "slow": False,
        "default_params": {"fold_count": 1, "p": 0.9},
    },
    "BookBinding": {
        "display_name": "Book Spine Curvature",
        "phase": "post",
        "description": "The page curves and darkens near the spine, as seen when scanning a bound book without pressing it flat.",
        "slow": False,
        "default_params": {"p": 0.9},
    },
    # ── Ink phase (additional) ────────────────────────────────────────────────
    "InkMottling": {
        "display_name": "Uneven Ink Absorption",
        "phase": "ink",
        "description": "Ink is absorbed unevenly into the paper fibres, creating a blotchy, mottled texture on printed areas.",
        "slow": False,
        "default_params": {
            "ink_mottling_alpha_range": (0.2, 0.3),
            "ink_mottling_noise_scale_range": (2, 2),
            "ink_mottling_gaussian_kernel_range": (3, 5),
            "p": 0.9,
        },
    },
    "LowInkPeriodicLines": {
        "display_name": "Ink Cartridge Banding",
        "phase": "ink",
        "description": "Faint horizontal streaks appear at regular intervals, caused by an ink cartridge running low and missing lines during printing.",
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
        "display_name": "Random Ink Dropout Streaks",
        "phase": "ink",
        "description": "Faint streaks appear at unpredictable positions, simulating a low or clogged ink cartridge that drops out randomly.",
        "slow": False,
        "default_params": {
            "count_range": (5, 10),
            "use_consistent_lines": True,
            "noise_probability": 0.1,
            "p": 0.9,
        },
    },
    "Hollow": {
        "display_name": "Hollow / Overexposed Characters",
        "phase": "ink",
        "description": "The centres of printed characters lose their ink, leaving hollow outlines — as in overexposed photocopies or worn typewriter ribbons.",
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
        "display_name": "Pen Scribbles",
        "phase": "ink",
        "description": "Random pen or marker scribbles are drawn over the page, as if someone doodled or annotated freely while reading.",
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
        "display_name": "Worn Line Printing",
        "phase": "ink",
        "description": "Horizontal or vertical ruled lines break up and fade, simulating the kind of degradation seen in aged or heavily photocopied forms.",
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
        "display_name": "Staples, Punch Holes and Rings",
        "phase": "ink",
        "description": "Shadows and markings from physical fasteners — staples, hole punches, or ring-binder impressions — appear on the document.",
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
        "display_name": "Subtle Paper Texture",
        "phase": "paper",
        "description": "Very subtle brightness variations are added across the page, giving a lightly textured feel as in matte or slightly rough paper stock.",
        "slow": False,
        "default_params": {
            "texturize_range": (0.8, 0.99),
            "deviation": 0.08,
            "p": 0.9,
        },
    },
    "ColorPaper": {
        "display_name": "Coloured Paper Stock",
        "phase": "paper",
        "description": "The page background is tinted to resemble coloured paper such as yellow legal pads, pink forms, or cream archival paper.",
        "slow": False,
        "default_params": {
            "hue_range": (28, 45),
            "saturation_range": (10, 40),
            "p": 0.9,
        },
    },
    "DirtyScreen": {
        "display_name": "Dust and Smudge on Scanner Glass",
        "phase": "paper",
        "description": "Clustered dust specks and smudge patches appear on the page, left by dirt on the scanner glass or camera lens.",
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
        "display_name": "Coffee and Water Stains",
        "phase": "paper",
        "description": "Irregular stain blobs appear on the paper, simulating liquid spills — coffee rings, water damage, or oil marks.",
        "slow": False,
        "default_params": {
            "stains_type": "random",
            "stains_blend_method": "darken",
            "stains_blend_alpha": 0.5,
            "p": 0.9,
        },
    },
    "NoisyLines": {
        "display_name": "Ruled Lines / Scan Streaks",
        "phase": "paper",
        "description": "Faint irregular lines cross the page, resembling ruled notebook paper, form lines, or artefact streaks from a scanner.",
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
        "display_name": "Security Background Pattern",
        "phase": "paper",
        "description": "A repeating geometric tile pattern is overlaid on the background, like the security tinting found on cheques or official documents.",
        "slow": False,
        "default_params": {
            "imgx": 512,
            "imgy": 512,
            "n_rotation_range": (10, 15),
            "color": "random",
            "alpha_range": (0.25, 0.5),
            "numba_jit": 1,  # 0 causes 'get_call_template' crash in augraphy 8.2.6
            "p": 0.9,
        },
    },
    "DelaunayTessellation": {
        "display_name": "Triangular Mesh Texture",
        "phase": "paper",
        "description": "A triangular mesh pattern is overlaid on the background, giving the page a textured or embossed paper appearance.",
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
        "display_name": "Cell / Mosaic Paper Texture",
        "phase": "paper",
        "description": "A cell-like mosaic pattern is overlaid on the background, resembling handmade or heavily textured paper.",
        "slow": True,
        "default_params": {
            "mult_range": (50, 80),
            "seed": 19829813472,
            "num_cells_range": (500, 1000),
            "noise_type": "random",
            "background_value": (200, 255),
            "numba_jit": 1,  # 0 causes 'get_call_template' crash in augraphy 8.2.6
            "p": 0.9,
        },
    },
    "PageBorder": {
        "display_name": "Scanner Edge Shadow and Curl",
        "phase": "paper",
        "description": "Dark shadows and page curl appear along the document edges, as seen when scanning a page that isn't pressed flat against the glass.",
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
        "display_name": "Camera Focus Blur",
        "phase": "post",
        "description": "Part of the image is blurred as if the camera was focused on a different distance — the out-of-focus area you see when photographing a document with a phone.",
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
        "display_name": "Ghost / Double Impression",
        "phase": "post",
        "description": "A faint shifted copy of the page is overlaid as a ghost image, simulating a double-feed jam through a photocopier or scanner.",
        "slow": False,
        "default_params": {
            "gaussian_kernel_range": (9, 12),
            "offset_direction": "random",
            "offset_range": (18, 25),
            "p": 0.9,
        },
    },
    "Faxify": {
        "display_name": "Fax Transmission Quality",
        "phase": "post",
        "description": "The document looks like it was sent by fax — monochrome, halftoned, with the characteristic grey speckle and low resolution of a thermal fax print.",
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
        "display_name": "Phone Screen Photograph",
        "phase": "post",
        "description": "An LCD pixel grid is overlaid, simulating a photo taken of a document displayed on a screen — common when capturing e-statements or PDFs.",
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
        "description": "A bright lens flare streaks across the image, as seen when a camera or scanner light source appears in the field of view.",
        "slow": True,
        "disabled": True,  # augraphy 8.2.6: numba parallel crash, unconditional segfault
        "default_params": {
            "lens_flare_location": "random",
            "lens_flare_color": "random",
            "lens_flare_size": (0.5, 5),
            "numba_jit": 0,
            "p": 0.9,
        },
    },
    "LightingGradient": {
        "display_name": "Uneven Lighting",
        "phase": "post",
        "description": "One side of the document is brighter than the other, simulating a desk lamp shining from an angle or uneven overhead lighting during capture.",
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
        "display_name": "Scan Interference Pattern",
        "phase": "post",
        "description": "A wave-like interference pattern ripples across the image, caused by a mismatch between the document's fine print pattern and the scanner resolution.",
        "slow": False,
        "default_params": {
            "moire_density": (15, 20),
            "moire_blend_method": "normal",
            "moire_blend_alpha": 0.1,
            "numba_jit": 1,  # 0 causes 'get_call_template' crash in augraphy 8.2.6
            "p": 0.9,
        },
    },
    "ReflectedLight": {
        "display_name": "Glossy Surface Glare",
        "phase": "post",
        "description": "A bright oval glare spot washes out part of the image, as seen when photographing a laminated or glossy document under room lighting.",
        "slow": False,
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
        "display_name": "Dot-Matrix Printer Output",
        "phase": "post",
        "description": "Text areas are rendered as a grid of dots, replicating the look of a dot-matrix or impact printer — common in older receipts and invoices.",
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
            "numba_jit": 1,  # 0 causes 'get_call_template' crash in augraphy 8.2.6
            "p": 0.9,
        },
    },
    "Rescale": {
        "display_name": "Resolution Change (DPI)",
        "phase": "post",
        "description": "The image is resampled to a different resolution, simulating a low-DPI mobile phone photo versus a high-DPI flatbed scan.",
        "slow": False,
        "default_params": {
            "target_dpi": 300,
            "p": 0.9,
        },
    },
    "SectionShift": {
        "display_name": "Scanner Feed Misalignment",
        "phase": "post",
        "description": "Horizontal strips of the page are shifted sideways, simulating a sheet-fed scanner that pulled the paper unevenly during the scan.",
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
        "display_name": "Page Compression Distortion",
        "phase": "post",
        "description": "Rows or columns are squeezed together, creating a stretch or compression distortion as seen when a page is slightly skewed under the scanner lid.",
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
    """Apply a single augmentation by catalogue name, bypassing the AugraphyPipeline.

    Calling augmentations directly (not via AugraphyPipeline) prevents the
    pipeline from compositing the ink layer onto a white paper background
    (overlay_alpha=0.3), which otherwise washes out / lightens every effect.

    Args:
        aug_name: Key in CATALOGUE (e.g. "InkBleed").
        image: PIL Image or numpy array (RGB).
        params: Override default_params. If None, uses CATALOGUE defaults.

    Returns:
        Augmented PIL Image (if input was PIL) or numpy array.

    Raises:
        KeyError: If aug_name is not in CATALOGUE.
        AttributeError: If aug_name is not a class in augraphy.augmentations.
    """
    import numpy as np
    from PIL import Image as PILImage
    import augraphy.augmentations as aug_module

    entry = CATALOGUE[aug_name]
    if entry.get("disabled"):
        raise ValueError(f"Augmentation '{aug_name}' is disabled due to a known crash in augraphy 8.2.6.")

    # Scribbles uses matplotlib.font_manager inside its __call__ but does not
    # import the submodule itself — pre-import it here to avoid AttributeError.
    if aug_name == "Scribbles":
        import matplotlib.font_manager  # noqa: F401

    # Always force p=1.0 so the augmentation is guaranteed to apply
    effective_params = {**entry["default_params"], **(params or {}), "p": 1.0}

    aug_class = getattr(aug_module, aug_name)
    aug_instance = aug_class(**effective_params)

    input_is_pil = isinstance(image, PILImage.Image)
    arr = np.array(image.convert("RGB")) if input_is_pil else image

    # Call the augmentation directly — no pipeline, no paper composite, no overlay
    result = aug_instance(arr)

    if not isinstance(result, np.ndarray):
        result = np.array(result)

    return PILImage.fromarray(result) if input_is_pil else result
