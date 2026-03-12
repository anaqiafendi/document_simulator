"""Batch document augmentation with optional multiprocessing."""

import random
import re
from multiprocessing import Pool
from pathlib import Path
from typing import List, Literal, Optional, Tuple, Union

from PIL import Image
from tqdm import tqdm

from document_simulator.augmentation.augmenter import DocumentAugmenter
from document_simulator.utils.image_io import ImageHandler


def _augment_one(args):
    """Top-level (picklable) helper for multiprocessing.

    Args:
        args: Tuple of (augmenter, image).

    Returns:
        Augmented PIL Image.
    """
    augmenter, image = args
    return augmenter.augment(image)


class BatchAugmenter:
    """Augment multiple document images, optionally in parallel.

    Args:
        augmenter: A :class:`~document_simulator.augmentation.DocumentAugmenter`
            instance (or preset name string) to use for each image.
        num_workers: Number of worker processes for parallel processing.
            Set to 1 to disable multiprocessing.
        show_progress: Whether to display a progress bar.
    """

    def __init__(
        self,
        augmenter: Union[DocumentAugmenter, str] = "default",
        num_workers: int = 4,
        show_progress: bool = False,
    ):
        if isinstance(augmenter, str):
            self.augmenter = DocumentAugmenter(pipeline=augmenter)
        else:
            self.augmenter = augmenter
        self.num_workers = max(1, num_workers)
        self.show_progress = show_progress

    def augment_batch(
        self,
        images: List[Union[Image.Image, str, Path]],
        parallel: bool = True,
    ) -> List[Image.Image]:
        """Augment a list of images.

        Args:
            images: List of PIL Images or file paths.
            parallel: Whether to use multiprocessing (ignored if num_workers=1).

        Returns:
            List of augmented PIL Images in the same order as *images*.
        """
        # Load any paths to PIL Images first
        loaded = [
            ImageHandler.load(img) if not isinstance(img, Image.Image) else img
            for img in images
        ]

        if parallel and self.num_workers > 1:
            args = [(self.augmenter, img) for img in loaded]
            with Pool(processes=self.num_workers) as pool:
                results = list(
                    tqdm(
                        pool.imap(_augment_one, args),
                        total=len(args),
                        disable=not self.show_progress,
                        desc="Augmenting",
                    )
                )
        else:
            results = [
                self.augmenter.augment(img)
                for img in tqdm(
                    loaded,
                    disable=not self.show_progress,
                    desc="Augmenting",
                )
            ]

        return results

    @staticmethod
    def _safe_stem(index: int) -> str:
        """Generate a safe filename stem for a source at *index*."""
        return f"template_{index:03d}"

    def augment_multi_template(
        self,
        sources: List[Image.Image],
        mode: Literal["per_template", "random_sample"] = "per_template",
        copies_per_template: int = 1,
        total_outputs: int = 10,
        seed: Optional[int] = None,
        parallel: bool = True,
    ) -> List[Tuple[Image.Image, str]]:
        """Augment multiple source templates to produce M total outputs.

        Two modes are supported:

        - ``per_template``: For each source, generate *copies_per_template* augmented copies.
          Total output count = ``len(sources) * copies_per_template``.
        - ``random_sample``: Sample *total_outputs* sources randomly (with replacement) and
          produce one augmented copy of each sampled source.

        Args:
            sources: List of PIL Images to use as templates. Must be non-empty.
            mode: ``"per_template"`` (N×M) or ``"random_sample"`` (M-total).
            copies_per_template: Number of augmented copies per source in ``per_template`` mode.
                Must be >= 1.
            total_outputs: Total number of outputs in ``random_sample`` mode. Must be >= 1.
            seed: Random seed for reproducible sampling in ``random_sample`` mode.
                ``None`` means unseeded (non-deterministic).
            parallel: Whether to use multiprocessing (passed to :meth:`augment_batch`).

        Returns:
            List of ``(augmented_image, source_stem)`` tuples where *source_stem* is a safe
            filename stem derived from the source index (e.g. ``"template_000"``).

        Raises:
            ValueError: If *sources* is empty, *mode* is unrecognised, *copies_per_template* < 1,
                or *total_outputs* < 1.
        """
        if not sources:
            raise ValueError("sources must be a non-empty list of PIL Images.")
        if mode not in ("per_template", "random_sample"):
            raise ValueError(
                f"mode must be 'per_template' or 'random_sample', got {mode!r}."
            )
        if mode == "per_template" and copies_per_template < 1:
            raise ValueError(
                f"copies_per_template must be >= 1, got {copies_per_template}."
            )
        if mode == "random_sample" and total_outputs < 1:
            raise ValueError(f"total_outputs must be >= 1, got {total_outputs}.")

        # Build the flat list of (source_image, source_stem) pairs to augment
        pairs: List[Tuple[Image.Image, str]] = []

        if mode == "per_template":
            for idx, img in enumerate(sources):
                stem = self._safe_stem(idx)
                for _ in range(copies_per_template):
                    pairs.append((img, stem))
        else:  # random_sample
            rng = random.Random(seed)
            population = list(range(len(sources)))
            indices = rng.choices(population, k=total_outputs)
            for i in indices:
                pairs.append((sources[i], self._safe_stem(i)))

        # Augment all selected images
        images_to_aug = [img for img, _ in pairs]
        stems = [stem for _, stem in pairs]
        augmented = self.augment_batch(images_to_aug, parallel=parallel)

        return list(zip(augmented, stems))

    def augment_directory(
        self,
        input_dir: Path,
        output_dir: Path,
        image_extensions: Optional[List[str]] = None,
        parallel: bool = True,
    ) -> List[Path]:
        """Augment all images in *input_dir* and save to *output_dir*.

        Args:
            input_dir: Directory containing source images.
            output_dir: Directory to write augmented images (created if absent).
            image_extensions: Extensions to consider as images.
                Defaults to ``['.jpg', '.jpeg', '.png', '.tiff', '.bmp']``.
            parallel: Whether to use multiprocessing.

        Returns:
            List of output file paths.
        """
        extensions = set(image_extensions or [".jpg", ".jpeg", ".png", ".tiff", ".bmp"])
        input_dir = Path(input_dir)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        input_paths = [
            p for p in sorted(input_dir.iterdir())
            if p.suffix.lower() in extensions
        ]

        if not input_paths:
            return []

        augmented = self.augment_batch(input_paths, parallel=parallel)

        output_paths = []
        for src_path, aug_img in zip(input_paths, augmented):
            dest = output_dir / src_path.name
            ImageHandler.save(aug_img, dest)
            output_paths.append(dest)

        return output_paths
