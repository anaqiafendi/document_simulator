"""Shared file-upload helpers used by all pages."""

import io
from typing import Any, List, Optional

from PIL import Image

ALLOWED_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"})


def is_valid_image_extension(filename: str) -> bool:
    """Return True if *filename* ends with a supported image extension."""
    lower = filename.lower()
    return any(lower.endswith(ext) for ext in ALLOWED_EXTENSIONS)


def uploaded_file_to_pil(uploaded_file: Any) -> Image.Image:
    """Convert a Streamlit ``UploadedFile`` to an RGB ``PIL.Image``.

    Args:
        uploaded_file: Object exposing ``getvalue() -> bytes`` (Streamlit's
                       ``UploadedFile`` or any duck-typed equivalent).

    Returns:
        PIL Image in ``"RGB"`` mode.
    """
    data = uploaded_file.getvalue()
    img = Image.open(io.BytesIO(data))
    return img.convert("RGB")


def uploaded_files_to_pil(uploaded_files: List[Any]) -> List[Image.Image]:
    """Convert a list of Streamlit ``UploadedFile`` objects to PIL Images.

    Args:
        uploaded_files: Iterable of Streamlit upload objects.

    Returns:
        List of RGB PIL Images in the same order.
    """
    return [uploaded_file_to_pil(f) for f in uploaded_files]
