"""Image display helpers: side-by-side view, bounding-box overlay, bytes encoding."""

import io
from typing import List, Optional, Tuple, Union

import numpy as np
import streamlit as st
from PIL import Image, ImageDraw, ImageFont


def _confidence_colour(score: float) -> Tuple[int, int, int]:
    """Map a confidence score in [0, 1] to an (R, G, B) colour.

    - High confidence → green
    - Low confidence  → red
    """
    score = float(np.clip(score, 0.0, 1.0))
    r = int((1.0 - score) * 255)
    g = int(score * 255)
    return r, g, 0


def overlay_bboxes(
    image: Image.Image,
    boxes: List,
    scores: List[float],
    line_width: int = 2,
    show_scores: bool = True,
) -> Image.Image:
    """Draw quadrilateral bounding boxes on *image* with confidence-coded colours.

    Args:
        image:      Source PIL Image (will not be modified).
        boxes:      List of quadrilaterals, each ``[[x,y], [x,y], [x,y], [x,y]]``.
        scores:     Confidence score per box, in the same order as *boxes*.
        line_width: Stroke width for the polygon outline.
        show_scores: If True, draw the score as a small label near each box.

    Returns:
        A new PIL Image (RGB) with boxes drawn on top.
    """
    out = image.convert("RGB").copy()
    draw = ImageDraw.Draw(out)

    for box, score in zip(boxes, scores):
        colour = _confidence_colour(float(score))
        pts = [(int(p[0]), int(p[1])) for p in box]
        draw.polygon(pts, outline=colour)
        if show_scores and pts:
            x0, y0 = pts[0]
            draw.text((x0, max(0, y0 - 12)), f"{score:.2f}", fill=colour)

    return out


def image_to_bytes(
    image: Union[Image.Image, np.ndarray],
    fmt: str = "PNG",
) -> bytes:
    """Encode a PIL Image or numpy array to bytes (for ``st.download_button``).

    Args:
        image: PIL Image or uint8 numpy array (H×W×C or H×W).
        fmt:   Image format string, e.g. ``"PNG"`` or ``"JPEG"``.

    Returns:
        Raw image bytes.
    """
    if isinstance(image, np.ndarray):
        image = Image.fromarray(image.astype(np.uint8))
    buf = io.BytesIO()
    image.save(buf, format=fmt)
    return buf.getvalue()


def show_side_by_side(
    original: Image.Image,
    augmented: Image.Image,
    labels: Tuple[str, str] = ("Original", "Augmented"),
) -> None:
    """Render two images side-by-side in equal-width Streamlit columns.

    Args:
        original:  Left image.
        augmented: Right image.
        labels:    Caption tuple ``(left_label, right_label)``.
    """
    col1, col2 = st.columns(2)
    with col1:
        st.image(original, caption=labels[0], use_container_width=True)
    with col2:
        st.image(augmented, caption=labels[1], use_container_width=True)
