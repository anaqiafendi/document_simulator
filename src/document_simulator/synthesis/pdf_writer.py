"""PDFZoneWriter — writes zone text natively into a PDF using PyMuPDF.

Instead of rasterising text onto a PIL image, this module inserts text as
real PDF text objects, preserving vector content, searchability, and
copy-paste fidelity of the original document.

Coordinate mapping
------------------
Zone boxes are stored in *image* pixel coordinates (origin top-left).
PyMuPDF's page coordinate system also has origin top-left (y increases
downward), with units in PDF points (1 pt = 1/72 inch).  The conversion
factor is simply ``72 / dpi`` in both axes.

Font handling
-------------
Custom fonts must be registered with ``page.insert_font()`` **before** calling
``page.insert_text()`` — passing ``fontfile`` directly to ``insert_text`` is
silently ignored by PyMuPDF and falls back to Helvetica.  Each unique font
family is registered once per page using a stable fontname key, then
referenced by that key in every subsequent ``insert_text`` call.
"""

from __future__ import annotations


def _hex_to_rgb_float(hex_color: str) -> tuple[float, float, float]:
    """Convert ``'#RRGGBB'`` to a (r, g, b) tuple with values in [0, 1]."""
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return (0.0, 0.0, 0.0)
    return (
        int(h[0:2], 16) / 255.0,
        int(h[2:4], 16) / 255.0,
        int(h[4:6], 16) / 255.0,
    )


# Stable PDF fontname keys used when registering bundled TTFs.
# Must be short ASCII identifiers (no spaces, no brackets).
_FAMILY_TO_PDFNAME: dict[str, str] = {
    "handwriting": "Caveat",
    "handwriting-alt": "IndieFlower",
    "monospace": "SourceCodePro",
    "serif": "Merriweather",
    "sans-serif": "NotoSans",
}


class PDFZoneWriter:
    """Write zone text directly into a PDF as native text objects.

    Usage::

        with open("template.pdf", "rb") as f:
            original_pdf = f.read()

        pdf_out = PDFZoneWriter.write(
            pdf_bytes=original_pdf,
            rendered_regions=[
                {
                    "box": [[10, 20], [200, 20], [200, 50], [10, 50]],
                    "text": "Jane Doe",
                    "font_family": "handwriting",
                    "font_size": 14,
                    "font_color": "#0000CC",
                },
            ],
            dpi=150,
        )
        with open("filled.pdf", "wb") as f:
            f.write(pdf_out)
    """

    @staticmethod
    def write(
        pdf_bytes: bytes | None,
        rendered_regions: list[dict],
        dpi: int = 150,
        page_number: int = 0,
        canvas_size: tuple[int, int] | None = None,
    ) -> bytes:
        """Insert text from *rendered_regions* into a PDF and return the result.

        Args:
            pdf_bytes:        Original PDF bytes to overlay text onto.
                              Pass ``None`` to create a new blank PDF (requires
                              *canvas_size* to set page dimensions).
            rendered_regions: List of region dicts.  Each must contain:
                              ``box``, ``text``, ``font_family``, ``font_size``,
                              ``font_color``.
            dpi:              Dots-per-inch used when rasterising the template
                              (needed for pixel → point coordinate conversion).
            page_number:      Which PDF page to insert text on.
            canvas_size:      ``(width_px, height_px)`` of the raster canvas.
                              Only used when *pdf_bytes* is ``None`` to size the
                              new blank page.

        Returns:
            Modified (or newly created) PDF as ``bytes``.
        """
        try:
            import fitz  # PyMuPDF
        except ImportError as exc:
            raise ImportError(
                "PyMuPDF is required for PDF output. "
                "Install with: uv sync --extra synthesis"
            ) from exc

        from document_simulator.synthesis.fonts import _CATALOG, _FONTS_DIR

        pts_per_px = 72.0 / dpi

        if pdf_bytes is not None:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            page = doc[page_number]
        else:
            doc = fitz.open()
            if canvas_size is not None:
                w_pt = canvas_size[0] * pts_per_px
                h_pt = canvas_size[1] * pts_per_px
            else:
                w_pt, h_pt = 595.0, 842.0
            page = doc.new_page(width=w_pt, height=h_pt)

        # ----------------------------------------------------------------
        # Pre-register every font family that appears in the regions.
        # page.insert_font() returns an xref; we store the PDF fontname key
        # used to reference it in insert_text() calls below.
        # ----------------------------------------------------------------
        registered: dict[str, str] = {}  # font_family -> PDF fontname key

        needed_families = {r.get("font_family", "sans-serif") for r in rendered_regions}
        for family in needed_families:
            pdf_fontname = _FAMILY_TO_PDFNAME.get(family, "NotoSans")
            ttf_filename = _CATALOG.get(family, _CATALOG.get("sans-serif", ""))
            ttf_path = (_FONTS_DIR / ttf_filename) if ttf_filename else None

            if ttf_path is not None and ttf_path.exists():
                try:
                    page.insert_font(fontname=pdf_fontname, fontfile=str(ttf_path))
                    registered[family] = pdf_fontname
                except Exception:
                    registered[family] = "helv"  # fallback to built-in
            else:
                registered[family] = "helv"

        # ----------------------------------------------------------------
        # Insert text for each region using the pre-registered font.
        # ----------------------------------------------------------------
        for region in rendered_regions:
            text = region.get("text", "").strip()
            if not text:
                continue

            box = region["box"]
            font_family = region.get("font_family", "sans-serif")
            font_size = int(region.get("font_size", 12))
            font_color = region.get("font_color", "#000000")

            # Pixel → PDF points.  box[0] is top-left of the zone;
            # insert_text places the baseline, so shift down by ~80% of
            # font size (typical ascender-to-em ratio for most typefaces).
            x_pt = float(box[0][0]) * pts_per_px
            y_pt = float(box[0][1]) * pts_per_px + font_size * 0.80

            color = _hex_to_rgb_float(font_color)
            fontname = registered.get(font_family, "helv")

            try:
                page.insert_text(
                    (x_pt, y_pt),
                    text,
                    fontname=fontname,
                    fontsize=font_size,
                    color=color,
                    overlay=True,
                )
            except Exception:
                # Last resort — skip rather than crash
                pass

        return doc.tobytes()
