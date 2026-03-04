"""Shared file-upload helpers used by all pages."""

import io
import tempfile
import zipfile
from pathlib import Path
from typing import Any, List, Optional

from PIL import Image

# Resolved relative to the Streamlit working directory (project root)
_SAMPLES_ROOT = Path("data/samples")

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


def list_sample_files(
    subdir: str,
    extensions: tuple[str, ...] = (".pdf",),
) -> List[Path]:
    """Return sorted sample files under ``data/samples/<subdir>/``.

    Args:
        subdir: Subdirectory name (e.g. ``"ocr_engine"``).
        extensions: File extensions to include (lowercase, with leading dot).

    Returns:
        Sorted list of :class:`~pathlib.Path` objects, empty if the folder
        does not exist or contains no matching files.
    """
    folder = _SAMPLES_ROOT / subdir
    if not folder.exists():
        return []
    return sorted(p for p in folder.iterdir() if p.suffix.lower() in extensions)


def load_path_as_pil_pages(path: Path, dpi: int = 150) -> List[Image.Image]:
    """Load an image or PDF from a filesystem path into a list of PIL Images.

    PDFs are rendered page-by-page at *dpi*. Images return a single-element list.

    Args:
        path: Filesystem path to a PDF or raster image.
        dpi:  Render resolution for PDFs (default 150).

    Returns:
        List of RGB PIL Images (one per page for PDFs, one for images).

    Raises:
        ImportError: If PyMuPDF is not installed and *path* is a PDF.
    """
    if path.suffix.lower() == ".pdf":
        try:
            import fitz
        except ImportError as exc:
            raise ImportError(
                "PyMuPDF is required for PDF sample loading. "
                "Install with: uv sync --extra synthesis"
            ) from exc
        doc = fitz.open(str(path))
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pages: List[Image.Image] = []
        for page in doc:
            pix = page.get_pixmap(matrix=mat)
            pages.append(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))
        return pages
    else:
        return [Image.open(path).convert("RGB")]


def extract_zip_to_tempdir(uploaded_zip: Any) -> tempfile.TemporaryDirectory:
    """Extract an uploaded ZIP into a fresh :class:`tempfile.TemporaryDirectory`.

    The caller **must** keep a reference to the returned object (e.g. in
    ``st.session_state``) for as long as the extracted files are needed.
    Python garbage-collects ``TemporaryDirectory`` objects, which deletes the
    extracted files.

    Args:
        uploaded_zip: Streamlit ``UploadedFile`` for a ``.zip`` file.

    Returns:
        :class:`tempfile.TemporaryDirectory` — use ``.name`` for the path.
    """
    tmp = tempfile.TemporaryDirectory()
    data = uploaded_zip.getvalue()
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        zf.extractall(tmp.name)
    return tmp


def expand_uploads_to_pil(
    uploaded_files: List[Any],
    dpi: int = 150,
) -> tuple[list[Image.Image], list[str]]:
    """Expand a mixed list of uploaded images and PDFs into (images, labels).

    PDF files are expanded page-by-page. Labels identify the source
    file (and page number for PDFs) for display and ZIP filenames.

    Args:
        uploaded_files: List of Streamlit UploadedFile objects (images or PDFs).
        dpi: Render resolution for PDF pages (default 150 DPI).

    Returns:
        images: Flat list of PIL Images.
        labels: One display name per image (e.g. "report.pdf — page 2").
    """
    images: list[Image.Image] = []
    labels: list[str] = []
    for f in uploaded_files:
        if f.name.lower().endswith(".pdf"):
            pages = uploaded_pdf_to_pil_pages(f, dpi=dpi)
            for i, page in enumerate(pages):
                images.append(page)
                labels.append(f"{f.name} — page {i + 1}")
        else:
            images.append(uploaded_file_to_pil(f))
            labels.append(f.name)
    return images, labels


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
