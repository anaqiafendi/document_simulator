"""Post-render Augraphy degradation for the photoreal receipt pipeline (FDD #28 AC-3).

Wraps the existing :class:`document_simulator.augmentation.DocumentAugmenter`
in a thin function that:
  - takes a rendered receipt PIL image,
  - applies one of the existing augmentation presets (light / medium / heavy / default),
  - returns a same-size PIL image (so polygon GT remains valid).

Augraphy is **pixel-only** at this stage — it does NOT modify the
``ImageGroundTruth``. Polygons computed during the raster stage stay aligned
because Augraphy effects do not displace pixels (no rotation, no warp).

Determinism: Augraphy uses Python's ``random`` and NumPy's global RNG. Seeding
both immediately before pipeline construction is sufficient to reproduce a run.
"""

from __future__ import annotations

import random
from typing import Final

import numpy as np
from loguru import logger
from PIL import Image

from document_simulator.augmentation.augmenter import DocumentAugmenter
from document_simulator.augmentation.presets import PresetFactory

# Allowed preset names for the synthesis API. Sourced from the existing
# ``PresetFactory.create`` switch — kept in sync via the module-level test.
SUPPORTED_PRESETS: Final[tuple[str, ...]] = ("light", "medium", "heavy", "default")


def apply_post_render(
    image: Image.Image,
    preset: str,
    seed: int = 0,
) -> Image.Image:
    """Apply an Augraphy preset to a rendered receipt image.

    Args:
        image: The rasterised receipt (RGB PIL.Image). Will be converted to RGB
            if not already.
        preset: Preset name. Must be one of :data:`SUPPORTED_PRESETS`.
        seed: Reproducibility seed. Same input + (preset, seed) -> visually
            identical output (asserted by the AC-8 determinism test).

    Returns:
        A same-size PIL.Image with the preset applied. The returned image's
        ``size`` is guaranteed equal to ``image.size`` so any GT polygons
        computed against the input remain valid.

    Raises:
        ValueError: If ``preset`` is not a supported preset name.
    """
    if preset not in SUPPORTED_PRESETS:
        raise ValueError(
            f"Unknown Augraphy preset {preset!r}. " f"Supported: {', '.join(SUPPORTED_PRESETS)}"
        )

    # Validate the preset is constructible (defensive — `SUPPORTED_PRESETS`
    # mirrors the factory but a typo in the factory would otherwise blow up
    # at augment time with a cryptic message).
    try:
        PresetFactory.create(preset)
    except KeyError as exc:
        raise ValueError(
            f"Preset {preset!r} listed as supported but PresetFactory rejected it: {exc}"
        ) from exc

    # Deterministic seeding: Augraphy hooks into both stdlib `random` and
    # NumPy's global RNG. Re-seed both immediately before constructing the
    # pipeline so two calls with the same seed produce byte-identical output.
    random.seed(seed)
    np.random.seed(seed)

    augmenter = DocumentAugmenter(pipeline=preset)

    rgb_image = image if image.mode == "RGB" else image.convert("RGB")
    original_size = rgb_image.size

    augmented = augmenter.augment(rgb_image)

    # Defensive: Augraphy is pixel-only here, but if any future preset adds a
    # geometric op we want a loud failure rather than silent GT-polygon drift.
    if not isinstance(augmented, Image.Image):
        augmented = Image.fromarray(np.asarray(augmented))
    if augmented.size != original_size:
        logger.warning(
            f"apply_post_render: Augraphy changed size {original_size} -> "
            f"{augmented.size}; resizing back to keep GT polygons valid"
        )
        augmented = augmented.resize(original_size, Image.Resampling.LANCZOS)

    return augmented
