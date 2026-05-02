"""Unit tests for synthesis.receipts.overlay (AC-7)."""

from PIL import Image

from document_simulator.synthesis.receipts import (
    draw_overlay,
    render_receipt,
)
from document_simulator.synthesis.receipts.content import make_minimal_receipt


def test_overlay_returns_image_same_size():
    """AC-7: draw_overlay returns a PIL.Image of the same dimensions as the input."""
    image, gt = render_receipt(make_minimal_receipt(seed=42), seed=42)
    overlay = draw_overlay(image, gt, stage="raster")

    assert isinstance(overlay, Image.Image)
    assert overlay.size == image.size
    # The overlay must visibly differ from the source — at minimum some pixels are
    # repainted as polygon outlines.
    assert overlay.tobytes() != image.tobytes()
