"""Render a Receipt to PNG plus per-token raster ground truth.

v0.1: Jinja2 -> WeasyPrint -> walk the rendered box tree to collect glyph rects
for every <span data-token-id="..."> in the template, then rasterize via
PyMuPDF (WeasyPrint 62.x dropped its built-in PNG writer; PDF is its native
output and PyMuPDF is already a project dep).
"""

from __future__ import annotations

from pathlib import Path

import pymupdf
from jinja2 import Environment, FileSystemLoader, select_autoescape
from loguru import logger
from PIL import Image
from weasyprint import HTML

from document_simulator.synthesis.receipts.schema import (
    CoordSnapshot,
    ImageGroundTruth,
    Receipt,
    TokenGroundTruth,
)

_PIPELINE_VERSION = "0.1.0"
_TEMPLATES_DIR = Path(__file__).parent / "templates"
_DEFAULT_TEMPLATE = "thermal_minimal.html.j2"

# WeasyPrint emits CSS pixels (96 dpi). PDF uses points (72 dpi). Rendering the
# PDF at zoom = 96/72 yields image px == CSS px (1:1), so the box-tree
# coordinates map straight to image pixels with no scaling.
_PDF_TO_CSS_ZOOM = 96.0 / 72.0


def _build_jinja_env() -> Environment:
    """Construct the Jinja2 env that loads templates from the package directory."""
    return Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=select_autoescape(enabled_extensions=("html", "j2", "html.j2")),
        keep_trailing_newline=True,
    )


def _walk_token_boxes(
    box,
    rects: dict[str, tuple[float, float, float, float]],
    texts: dict[str, str],
) -> None:
    """Recursively walk the WeasyPrint box tree, collecting per-token rects + text.

    For each ``TextBox`` whose ancestor element carries ``data-token-id``, we
    accumulate (x_min, y_min, x_max, y_max) in CSS pixels and concatenate the
    rendered text. A token may span several glyph runs (e.g. line-wrapped text),
    so we union the rects.

    Args:
        box: A WeasyPrint Box (PageBox / BlockBox / LineBox / InlineBox / TextBox).
        rects: Output dict (mutated): token_id -> (x_min, y_min, x_max, y_max).
        texts: Output dict (mutated): token_id -> concatenated text content.
    """
    if type(box).__name__ == "TextBox":
        element = getattr(box, "element", None)
        if element is not None:
            tid = element.get("data-token-id")
            if tid:
                x = float(box.position_x)
                y = float(box.position_y)
                w = float(box.width)
                h = float(box.height)
                rect = (x, y, x + w, y + h)
                if tid in rects:
                    px_min, py_min, px_max, py_max = rects[tid]
                    rects[tid] = (
                        min(px_min, rect[0]),
                        min(py_min, rect[1]),
                        max(px_max, rect[2]),
                        max(py_max, rect[3]),
                    )
                else:
                    rects[tid] = rect
                text = getattr(box, "text", "") or ""
                texts[tid] = (texts.get(tid, "") + text).strip()

    if hasattr(box, "children"):
        for child in box.children:
            _walk_token_boxes(child, rects, texts)


def _rasterize_pdf_to_pil(pdf_bytes: bytes) -> Image.Image:
    """Convert WeasyPrint PDF bytes to a PIL.Image at 1 CSS-px = 1 image-px."""
    pdf_doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    try:
        page = pdf_doc[0]
        mat = pymupdf.Matrix(_PDF_TO_CSS_ZOOM, _PDF_TO_CSS_ZOOM)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    finally:
        pdf_doc.close()


def render_receipt(
    receipt: Receipt, seed: int = 0, template_name: str = _DEFAULT_TEMPLATE
) -> tuple[Image.Image, ImageGroundTruth]:
    """Render a receipt to PIL.Image and build its ImageGroundTruth.

    Args:
        receipt: Source receipt content.
        seed: Seed that originally generated the receipt; recorded into GT for
            reproducibility. The renderer itself is deterministic given identical
            input HTML, so this value is metadata only.
        template_name: Jinja2 template filename under ``templates/``.

    Returns:
        A (PIL.Image, ImageGroundTruth) pair. Every text token wrapped in the
        template's ``<span data-token-id="...">`` has exactly one CoordSnapshot
        with ``stage="raster"``.
    """
    logger.debug(f"Rendering receipt seed={seed} merchant={receipt.merchant!r}")

    env = _build_jinja_env()
    template = env.get_template(template_name)
    html_str = template.render(receipt=receipt)

    document = HTML(string=html_str).render()
    if not document.pages:
        raise RuntimeError("WeasyPrint produced no pages for receipt render")
    page_box = document.pages[0]._page_box

    # Walk the box tree once to harvest per-token rects + text in CSS px.
    rects: dict[str, tuple[float, float, float, float]] = {}
    texts: dict[str, str] = {}
    _walk_token_boxes(page_box, rects, texts)
    logger.debug(f"Walked {len(rects)} tagged tokens from box tree")

    # Rasterize via PDF -> PIL. CSS px == image px because of zoom = 96/72.
    pdf_bytes = document.write_pdf()
    image = _rasterize_pdf_to_pil(pdf_bytes)

    # Build TokenGroundTruth list. We iterate `rects` in insertion order
    # (dict-preserving) so the output is deterministic for fixed input HTML.
    tokens: list[TokenGroundTruth] = []
    for token_id, (x_min, y_min, x_max, y_max) in rects.items():
        polygon: list[tuple[float, float]] = [
            (x_min, y_min),
            (x_max, y_min),
            (x_max, y_max),
            (x_min, y_max),
        ]
        tokens.append(
            TokenGroundTruth(
                token_id=token_id,
                text=texts.get(token_id, ""),
                coords=[CoordSnapshot(stage="raster", polygon=polygon)],
            )
        )

    gt = ImageGroundTruth(
        image_id=f"{seed:08d}",
        image_path=Path(f"images/{seed:08d}.png"),
        image_size=image.size,
        tokens=tokens,
        receipt=receipt,
        seed=seed,
        pipeline_version=_PIPELINE_VERSION,
    )
    return image, gt
