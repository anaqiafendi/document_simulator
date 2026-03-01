"""Unified image I/O utilities."""

import io
from pathlib import Path
from typing import List, Union

import numpy as np
from PIL import Image, UnidentifiedImageError


class ImageHandler:
    """Unified interface for loading and saving images.

    Supports PIL Images, numpy arrays, file paths, and raw bytes.
    """

    @staticmethod
    def load(source: Union[str, Path, Image.Image, np.ndarray, bytes]) -> Image.Image:
        """Load an image from various source types.

        Args:
            source: File path (str/Path), PIL Image, numpy array, or raw bytes.

        Returns:
            PIL Image in RGB mode.

        Raises:
            FileNotFoundError: If *source* is a path that does not exist.
            UnidentifiedImageError: If bytes/path cannot be decoded as an image.
            TypeError: If *source* is an unrecognised type.
        """
        if isinstance(source, (str, Path)):
            path = Path(source)
            if not path.exists():
                raise FileNotFoundError(f"Image file not found: {path}")
            return Image.open(path).convert("RGB")

        if isinstance(source, Image.Image):
            return source.convert("RGB")

        if isinstance(source, np.ndarray):
            return Image.fromarray(source).convert("RGB")

        if isinstance(source, bytes):
            try:
                return Image.open(io.BytesIO(source)).convert("RGB")
            except Exception as exc:
                raise UnidentifiedImageError(
                    "Cannot identify image from bytes"
                ) from exc

        raise TypeError(
            f"Unsupported image source type: {type(source).__name__}. "
            "Expected str, Path, PIL.Image.Image, numpy.ndarray, or bytes."
        )

    @staticmethod
    def save(image: Union[Image.Image, np.ndarray], path: Union[str, Path]) -> None:
        """Save an image to disk.

        Args:
            image: PIL Image or numpy array.
            path: Destination file path (parent directories are created).
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        image.save(path)

    @staticmethod
    def to_numpy(image: Union[Image.Image, np.ndarray]) -> np.ndarray:
        """Convert a PIL Image or numpy array to a uint8 numpy array.

        Args:
            image: Source image.

        Returns:
            numpy array with dtype uint8.
        """
        if isinstance(image, np.ndarray):
            return image
        return np.array(image)

    @staticmethod
    def to_pil(image: Union[Image.Image, np.ndarray]) -> Image.Image:
        """Convert a numpy array or PIL Image to a PIL Image.

        Args:
            image: Source image.

        Returns:
            PIL Image in RGB mode.
        """
        if isinstance(image, Image.Image):
            return image.convert("RGB")
        return Image.fromarray(image).convert("RGB")

    @staticmethod
    def to_grayscale(image: Union[Image.Image, np.ndarray]) -> Image.Image:
        """Convert image to grayscale PIL Image.

        Args:
            image: Source image.

        Returns:
            PIL Image in mode 'L'.
        """
        return ImageHandler.to_pil(image).convert("L")

    @staticmethod
    def load_batch(
        sources: List[Union[str, Path, Image.Image, np.ndarray, bytes]],
    ) -> List[Image.Image]:
        """Load multiple images.

        Args:
            sources: List of image sources accepted by :meth:`load`.

        Returns:
            List of PIL Images.
        """
        return [ImageHandler.load(s) for s in sources]
