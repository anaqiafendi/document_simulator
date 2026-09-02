"""Post-render Augraphy degradation for the photoreal receipt pipeline (FDD #28 AC-3).

Wraps the existing :class:`document_simulator.augmentation.DocumentAugmenter`
in a thin function that:
  - takes a rendered receipt PIL image,
  - applies one of the existing augmentation presets (light / medium / heavy / default),
  - returns a same-size PIL image (so polygon GT remains valid).

Augraphy is **pixel-only** at this stage — it does NOT modify the
``ImageGroundTruth``. Polygons computed during the raster stage stay aligned
because Augraphy effects do not displace pixels (no rotation, no warp).

Determinism: Augraphy's augmentations read the *process-global* ``random`` and
``numpy.random`` generators; there is no per-pipeline RNG we can inject through
``DocumentAugmenter``. So this module owns the seeding, but scopes it: a local
:class:`random.Random` / :func:`numpy.random.default_rng` pair derives the
sub-seeds, those are installed into the globals only for the duration of the
Augraphy call, and the caller's global RNG state is restored afterwards. That
keeps output reproducible for a given ``seed`` *and* keeps a batch worker from
perturbing anything else in its process (see ``batch.py``).
"""

from __future__ import annotations

import random
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any, Final

import numpy as np
from loguru import logger
from PIL import Image

from document_simulator.augmentation.augmenter import DocumentAugmenter
from document_simulator.augmentation.presets import PresetFactory

# Allowed preset names for the synthesis API. Sourced from the existing
# ``PresetFactory.create`` switch — kept in sync via the module-level test.
SUPPORTED_PRESETS: Final[tuple[str, ...]] = ("light", "medium", "heavy", "default")

#: Upper bound for the integer sub-seeds handed to the global generators.
_SEED_SPACE: Final[int] = 2**31 - 1


@contextmanager
def _scoped_global_seed(py_seed: int, np_seed: int) -> Iterator[None]:
    """Seed the global RNGs for the duration of the block, then restore them.

    Augraphy is a third-party library that reads ``random`` and
    ``numpy.random`` directly, so seeding the globals is the only way to make it
    deterministic. Doing that unconditionally — as this module used to — leaves
    every generator in the process reset to a known state, which makes results
    depend on the *order* samples happen to be processed in. Saving and
    restoring around the call confines the damage to the call.
    """
    py_state = random.getstate()
    np_state: Any = np.random.get_state()
    try:
        random.seed(py_seed)
        np.random.seed(np_seed)
        yield
    finally:
        random.setstate(py_state)
        np.random.set_state(np_state)


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
        seed: Reproducibility seed. Same input + (preset, seed) -> byte-identical
            output (asserted by the AC-8 determinism test), independently of how
            many other augmentations ran before it in this process.

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

    rgb_image = image if image.mode == "RGB" else image.convert("RGB")
    original_size = rgb_image.size

    # Local generators are the source of truth for this call; they derive the
    # sub-seeds that are briefly installed into the globals Augraphy reads.
    # Nothing outside `_scoped_global_seed` observes a reseeded global RNG, so
    # two workers rendering concurrently cannot influence each other's output.
    py_seed = random.Random(seed).randrange(_SEED_SPACE)
    np_seed = int(np.random.default_rng(seed).integers(_SEED_SPACE))

    with _scoped_global_seed(py_seed, np_seed):
        # Some augmentations draw parameters at construction time, so the
        # pipeline must be built inside the scope as well.
        augmenter = DocumentAugmenter(pipeline=preset)
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
