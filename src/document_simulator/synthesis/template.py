"""TemplateLoader — produces a PIL Image from various template sources."""

from __future__ import annotations

from pathlib import Path

from PIL import Image


class TemplateLoader:
    """Load or create document template images."""

    @staticmethod
    def blank(width: int = 794, height: int = 1123) -> Image.Image:
        """Return a white RGB canvas of the requested size."""
        return Image.new("RGB", (width, height), color=(255, 255, 255))

    @staticmethod
    def from_image(path: str) -> Image.Image:
        """Load an image file and convert to RGB."""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Template image not found: {path}")
        return Image.open(p).convert("RGB")

    @staticmethod
    def from_pdf(path: str, page_number: int = 0, dpi: int = 150) -> Image.Image:
        """Render a PDF page to a PIL Image using PyMuPDF."""
        try:
            import fitz  # PyMuPDF
        except ImportError as exc:
            raise ImportError(
                "PyMuPDF is required for PDF templates. "
                "Install with: uv sync --extra synthesis"
            ) from exc
        doc = fitz.open(path)
        page = doc[page_number]
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pixmap = page.get_pixmap(matrix=mat)
        return Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)

    @classmethod
    def load(cls, source: str, **kwargs) -> Image.Image:
        """Dispatch to the appropriate loader based on *source*.

        - ``"blank"`` → white canvas (pass ``width`` and ``height`` kwargs)
        - ``"*.pdf"`` → PDF page renderer (pass ``page_number``, ``dpi`` kwargs)
        - anything else → treat as an image file path
        """
        if source == "blank":
            return cls.blank(
                width=kwargs.get("width", 794),
                height=kwargs.get("height", 1123),
            )
        if source.lower().endswith(".pdf"):
            return cls.from_pdf(
                source,
                page_number=kwargs.get("page_number", 0),
                dpi=kwargs.get("dpi", 150),
            )
        return cls.from_image(source)
