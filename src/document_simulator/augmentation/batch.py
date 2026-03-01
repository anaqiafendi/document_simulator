"""Batch document augmentation with optional multiprocessing."""

from multiprocessing import Pool
from pathlib import Path
from typing import List, Optional, Union

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
