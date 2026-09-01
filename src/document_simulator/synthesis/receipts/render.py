"""Render a Receipt to PNG plus per-token raster ground truth.

v0.1: Jinja2 -> WeasyPrint -> walk the rendered box tree to collect glyph rects
for every <span data-token-id="..."> in the template, then rasterize via
PyMuPDF (WeasyPrint 62.x dropped its built-in PNG writer; PDF is its native
output and PyMuPDF is already a project dep).

v0.4 adds the composable renderer: ``composable.html.j2`` is driven entirely by
``receipt.sections`` (typed blocks) and ``receipt.style`` (the eight taxonomy
axes), so a new layout is a new *spec*, not a new template file. Alongside that:

* ``style`` joins ``receipt`` in the template context;
* ``base_url`` is passed to WeasyPrint so bundled ``@font-face`` files resolve;
* the box-tree walker also harvests ``data-semantic`` into
  ``TokenGroundTruth.semantic_role``;
* ``image_id`` is keyed on seed *and* spec identity, so a batch sweeping many
  specs at one seed no longer overwrites ``images/00000042.png``.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import pymupdf
from jinja2 import Environment, FileSystemLoader, select_autoescape
from loguru import logger
from PIL import Image
from weasyprint import HTML

from document_simulator.synthesis.receipts.layout.spec import ReceiptStyle
from document_simulator.synthesis.receipts.schema import (
    CoordSnapshot,
    ImageGroundTruth,
    Receipt,
    TokenGroundTruth,
)

_PIPELINE_VERSION = "0.1.0"
_TEMPLATES_DIR = Path(__file__).parent / "templates"
_FONTS_DIR = Path(__file__).resolve().parents[2] / "fonts"
_DEFAULT_TEMPLATE = "thermal_minimal.html.j2"

#: The v0.4 data-driven template. Exported so batch/api can name it without
#: hard-coding the filename.
COMPOSABLE_TEMPLATE = "composable.html.j2"

# --- Page geometry ---------------------------------------------------------
# FDD decision #8: `@page { size: 80mm auto }` silently degrades to A4 in
# WeasyPrint 62.3, and this module only reads `document.pages[0]` -- so content
# that spills onto page 2 vanishes from the raster *and* from the ground truth.
# A composable receipt has a variable number of blocks, so the page is fixed at
# a height with room for the longest layout the sampler can produce (~40 stacked
# blocks at 10pt). Callers can override via `render_receipt(page_height=...)`.
_DEFAULT_PAGE_WIDTH = "80mm"
_DEFAULT_PAGE_HEIGHT = "420mm"

# WeasyPrint emits CSS pixels (96 dpi). PDF uses points (72 dpi). Rendering the
# PDF at zoom = 96/72 yields image px == CSS px (1:1), so the box-tree
# coordinates map straight to image pixels with no scaling.
_PDF_TO_CSS_ZOOM = 96.0 / 72.0

# --- Fonts -----------------------------------------------------------------
# The corpus taxonomy names three receipt faces (MERCHANT_COPY, FAKE_RECEIPT,
# RECEIPTIONAL_RECEIPT). None of the three is redistributable, and none is
# bundled in `src/document_simulator/fonts/`. Each is therefore mapped to a
# bundled *substitute* chosen to keep the axis visually discriminative (mono /
# sans / serif), and `_resolve_font()` logs a warning naming the substitution.
# Replace the right-hand side here if the real faces are ever vendored in.
_BUNDLED_FONT_FILES: dict[str, str] = {
    "SourceCodePro": "SourceCodePro[wght].ttf",
    "NotoSans": "NotoSans[wdth,wght].ttf",
    "Merriweather": "Merriweather[opsz,wdth,wght].ttf",
    "Caveat": "Caveat[wght].ttf",
    "IndieFlower": "IndieFlower-Regular.ttf",
}

#: font_type -> (bundled family or None, generic CSS fallback keyword).
_FONT_TYPE_SUBSTITUTES: dict[str, tuple[str | None, str]] = {
    "MERCHANT_COPY": ("SourceCodePro", "monospace"),
    "FAKE_RECEIPT": ("NotoSans", "sans-serif"),
    "RECEIPTIONAL_RECEIPT": ("Merriweather", "serif"),
    "UNSET": (None, "monospace"),
}

_GENERIC_STACKS: dict[str, str] = {
    "monospace": '"Menlo", "Consolas", ui-monospace, monospace',
    "sans-serif": '"Helvetica Neue", "Arial", sans-serif',
    "serif": '"Times New Roman", "Georgia", serif',
}

#: Characters allowed in an image_id. Everything else is folded to "-" so the
#: id stays safe as a filename on every platform we target.
_ID_SAFE_RE = re.compile(r"[^A-Za-z0-9._-]")


def _build_jinja_env() -> Environment:
    """Construct the Jinja2 env that loads templates from the package directory."""
    return Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=select_autoescape(enabled_extensions=("html", "j2", "html.j2")),
        keep_trailing_newline=True,
    )


def _resolve_font(font_type: str) -> tuple[list[dict[str, str]], str]:
    """Map a taxonomy ``font_type`` to @font-face descriptors plus a CSS stack.

    Args:
        font_type: Taxonomy value (MERCHANT_COPY / FAKE_RECEIPT /
            RECEIPTIONAL_RECEIPT / UNSET). Unknown values fall back to UNSET.

    Returns:
        ``(font_faces, font_stack)`` where ``font_faces`` is a list of
        ``{"family": ..., "uri": ...}`` dicts to emit as ``@font-face`` rules and
        ``font_stack`` is the CSS ``font-family`` value. The stack always ends in
        a generic keyword, so a missing font file degrades rather than failing.
    """
    family, generic = _FONT_TYPE_SUBSTITUTES.get(font_type, _FONT_TYPE_SUBSTITUTES["UNSET"])
    generic_stack = _GENERIC_STACKS[generic]

    if family is None:
        return [], generic_stack

    font_path = _FONTS_DIR / _BUNDLED_FONT_FILES[family]
    if not font_path.is_file():
        logger.warning(
            f"font_type={font_type!r} maps to bundled face {family!r} but "
            f"{font_path} is missing; falling back to {generic!r} stack"
        )
        return [], generic_stack

    return [{"family": family, "uri": font_path.as_uri()}], f'"{family}", {generic_stack}'


def _spec_key(receipt: Receipt, spec_id: str | None) -> str | None:
    """Derive the spec-identity component of an image_id, or None if unspecced.

    ``None`` is returned only for a receipt carrying neither a style nor any
    sections -- i.e. one rendered through a v0.1/v0.2 hand-written template. That
    case keeps the historical bare ``%08d`` id so existing on-disk datasets and
    tests stay valid.

    Args:
        receipt: Receipt being rendered.
        spec_id: Caller-supplied identity (e.g. ``LayoutSpec.spec_id``), which
            wins over the derived hash so a batch can group by its own spec.

    Returns:
        A filesystem-safe key, or None when the receipt carries no spec.
    """
    if spec_id is not None:
        return _ID_SAFE_RE.sub("-", spec_id)[:32] or None

    if receipt.style is None and not receipt.sections:
        return None

    # Layout identity only: the style axes plus the block skeleton. Deliberately
    # excludes item text/amounts so the same layout hashes alike across seeds.
    payload = json.dumps(
        {
            "style": receipt.style.model_dump() if receipt.style is not None else None,
            "blocks": [
                {
                    "type": block.type.value,
                    "alignment": block.alignment,
                    "bottom_divider": block.bottom_divider,
                    "show_quantity": block.show_quantity,
                    "money_roles": [row.role.value for row in block.money_rows],
                }
                for block in receipt.sections
            ],
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode()).hexdigest()[:12]


def _make_image_id(receipt: Receipt, seed: int, spec_id: str | None) -> str:
    """Build the collision-free image_id for one rendered sample.

    Historically this was ``f"{seed:08d}"``, which meant a batch sweeping N specs
    at a single seed wrote all N samples to ``images/00000042.png`` -- the last
    writer won and the manifest grew N duplicate lines. The id now carries the
    spec identity as a suffix.

    Args:
        receipt: Receipt being rendered.
        seed: Generating seed.
        spec_id: Optional caller-supplied spec identity.

    Returns:
        ``"{seed:08d}"`` when the receipt has no spec (unchanged from v0.1), else
        ``"{seed:08d}_{spec_key}"``.
    """
    key = _spec_key(receipt, spec_id)
    if key is None:
        return f"{seed:08d}"
    return f"{seed:08d}_{key}"


def _walk_token_boxes(
    box: Any,
    rects: dict[str, tuple[float, float, float, float]],
    texts: dict[str, str],
    roles: dict[str, str] | None = None,
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
        roles: Optional output dict (mutated): token_id -> ``data-semantic``
            value. Templates that omit the attribute simply contribute nothing,
            which is why this stays optional rather than required.
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
                if roles is not None:
                    semantic = element.get("data-semantic")
                    if semantic and tid not in roles:
                        roles[tid] = semantic

    if hasattr(box, "children"):
        for child in box.children:
            _walk_token_boxes(child, rects, texts, roles)


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


def build_html(
    receipt: Receipt,
    template_name: str = _DEFAULT_TEMPLATE,
    *,
    page_width: str = _DEFAULT_PAGE_WIDTH,
    page_height: str = _DEFAULT_PAGE_HEIGHT,
) -> str:
    """Render the Jinja template to an HTML string, without rasterizing.

    Split out of :func:`render_receipt` so tests (and any future HTML-only
    consumer) can inspect the markup and the paginated document directly --
    notably to assert that a many-block receipt still fits on one page.

    Args:
        receipt: Source receipt content.
        template_name: Jinja2 template filename under ``templates/``.
        page_width: CSS length for the ``@page`` width.
        page_height: CSS length for the ``@page`` height.

    Returns:
        The rendered HTML document as a string.
    """
    style = receipt.style if receipt.style is not None else ReceiptStyle()
    font_faces, font_stack = _resolve_font(style.font_type)

    env = _build_jinja_env()
    template = env.get_template(template_name)
    return template.render(
        receipt=receipt,
        style=style,
        font_faces=font_faces,
        font_stack=font_stack,
        page_width=page_width,
        page_height=page_height,
    )


def render_receipt(
    receipt: Receipt,
    seed: int = 0,
    template_name: str = _DEFAULT_TEMPLATE,
    *,
    spec_id: str | None = None,
    page_width: str = _DEFAULT_PAGE_WIDTH,
    page_height: str = _DEFAULT_PAGE_HEIGHT,
    base_url: str | None = None,
) -> tuple[Image.Image, ImageGroundTruth]:
    """Render a receipt to PIL.Image and build its ImageGroundTruth.

    Args:
        receipt: Source receipt content.
        seed: Seed that originally generated the receipt; recorded into GT for
            reproducibility. The renderer itself is deterministic given identical
            input HTML, so this value is metadata only.
        template_name: Jinja2 template filename under ``templates/``.
        spec_id: Optional layout-spec identity (e.g. ``LayoutSpec.spec_id``) that
            is folded into ``image_id``. When omitted the identity is derived
            from ``receipt.style`` + the block skeleton; when the receipt has
            neither, ``image_id`` keeps the historical bare ``%08d`` form.
        page_width: CSS length for the ``@page`` width (composable template only).
        page_height: CSS length for the ``@page`` height (composable template
            only). Fixed rather than ``auto`` -- see FDD decision #8.
        base_url: Base URL WeasyPrint resolves relative ``url()`` references
            against. Defaults to the packaged templates directory so bundled
            ``@font-face`` files and relative logo paths load.

    Returns:
        A (PIL.Image, ImageGroundTruth) pair. Every text token wrapped in the
        template's ``<span data-token-id="...">`` has exactly one CoordSnapshot
        with ``stage="raster"``, and carries the ``data-semantic`` role when the
        template supplies one.
    """
    logger.debug(f"Rendering receipt seed={seed} merchant={receipt.merchant!r}")

    html_str = build_html(
        receipt,
        template_name,
        page_width=page_width,
        page_height=page_height,
    )

    document = HTML(
        string=html_str,
        base_url=base_url if base_url is not None else str(_TEMPLATES_DIR),
    ).render()
    if not document.pages:
        raise RuntimeError("WeasyPrint produced no pages for receipt render")
    if len(document.pages) > 1:
        # Only page 1 is rasterized and walked, so anything on page 2+ is lost
        # from both the image and the ground truth. Loud, because silent token
        # loss corrupts the dataset rather than merely degrading it.
        logger.warning(
            f"Receipt overflowed onto {len(document.pages)} pages "
            f"(template={template_name}, page_height={page_height}); "
            "tokens beyond page 1 are dropped -- increase page_height"
        )
    page_box = document.pages[0]._page_box

    # Walk the box tree once to harvest per-token rects + text in CSS px.
    rects: dict[str, tuple[float, float, float, float]] = {}
    texts: dict[str, str] = {}
    roles: dict[str, str] = {}
    _walk_token_boxes(page_box, rects, texts, roles)
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
                semantic_role=roles.get(token_id),
                coords=[CoordSnapshot(stage="raster", polygon=polygon)],
            )
        )

    image_id = _make_image_id(receipt, seed, spec_id)
    gt = ImageGroundTruth(
        image_id=image_id,
        image_path=Path(f"images/{image_id}.png"),
        image_size=image.size,
        tokens=tokens,
        receipt=receipt,
        seed=seed,
        pipeline_version=_PIPELINE_VERSION,
    )
    return image, gt
