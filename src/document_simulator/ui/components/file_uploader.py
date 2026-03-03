"""Shared file-upload helpers used by all pages."""

import io
from typing import Any, List, Optional

from PIL import Image

ALLOWED_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"})
ALLOWED_EXTENSIONS_WITH_PDF = ALLOWED_EXTENSIONS | {".pdf"}


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


def uploaded_pdf_to_pil_pages(
    uploaded_file: Any,
    dpi: int = 150,
) -> List[Image.Image]:
    """Render every page of an uploaded PDF to a list of RGB PIL Images.

    Args:
        uploaded_file: Streamlit ``UploadedFile`` for a PDF.
        dpi:           Render resolution (default 150 DPI).

    Returns:
        List of RGB PIL Images, one per page, in page order.

    Raises:
        ImportError: If PyMuPDF is not installed.
    """
    try:
        import fitz
    except ImportError as exc:
        raise ImportError(
            "PyMuPDF is required for PDF support. "
            "Install with: uv sync --extra synthesis"
        ) from exc

    data = uploaded_file.getvalue()
    doc = fitz.open(stream=data, filetype="pdf")
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pages: List[Image.Image] = []
    for page in doc:
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        pages.append(img)
    return pages


def pil_to_pdf_bytes(image: Image.Image, dpi: int = 150) -> bytes:
    """Embed a PIL Image into a single-page PDF and return the PDF bytes.

    The page dimensions are derived from the image size at the given DPI so
    the physical size matches the original document.

    Args:
        image: RGB PIL Image to embed.
        dpi:   Resolution at which the image was rendered (used to compute
               page size in points).

    Returns:
        PDF file as ``bytes``.
    """
    try:
        import fitz
    except ImportError as exc:
        raise ImportError(
            "PyMuPDF is required for PDF output. "
            "Install with: uv sync --extra synthesis"
        ) from exc

    pts_per_px = 72.0 / dpi
    w_pt = image.width * pts_per_px
    h_pt = image.height * pts_per_px

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    img_bytes = buf.getvalue()

    doc = fitz.open()
    page = doc.new_page(width=w_pt, height=h_pt)
    page.insert_image(fitz.Rect(0, 0, w_pt, h_pt), stream=img_bytes)
    return doc.tobytes()
