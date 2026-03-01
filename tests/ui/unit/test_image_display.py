"""Unit tests for image_display component."""

import io

import numpy as np
import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# _confidence_colour
# ---------------------------------------------------------------------------


def test_confidence_colour_high_is_green():
    from document_simulator.ui.components.image_display import _confidence_colour

    r, g, b = _confidence_colour(0.99)
    assert g > r, "high confidence should be more green than red"


def test_confidence_colour_low_is_red():
    from document_simulator.ui.components.image_display import _confidence_colour

    r, g, b = _confidence_colour(0.01)
    assert r > g, "low confidence should be more red than green"


def test_confidence_colour_mid():
    from document_simulator.ui.components.image_display import _confidence_colour

    r, g, b = _confidence_colour(0.5)
    assert abs(r - g) < 10, "mid confidence should be roughly equal red/green"


def test_confidence_colour_clamps_above_one():
    from document_simulator.ui.components.image_display import _confidence_colour

    r, g, b = _confidence_colour(2.0)
    assert r == 0 and g == 255


def test_confidence_colour_clamps_below_zero():
    from document_simulator.ui.components.image_display import _confidence_colour

    r, g, b = _confidence_colour(-1.0)
    assert r == 255 and g == 0


# ---------------------------------------------------------------------------
# overlay_bboxes
# ---------------------------------------------------------------------------


def test_overlay_bboxes_returns_pil_image(blank_image):
    from document_simulator.ui.components.image_display import overlay_bboxes

    result = overlay_bboxes(blank_image, [[[10, 5], [80, 5], [80, 25], [10, 25]]], [0.95])
    assert isinstance(result, Image.Image)


def test_overlay_bboxes_same_size(blank_image):
    from document_simulator.ui.components.image_display import overlay_bboxes

    result = overlay_bboxes(blank_image, [[[10, 5], [80, 5], [80, 25], [10, 25]]], [0.9])
    assert result.size == blank_image.size


def test_overlay_bboxes_empty_inputs(blank_image):
    from document_simulator.ui.components.image_display import overlay_bboxes

    result = overlay_bboxes(blank_image, [], [])
    assert isinstance(result, Image.Image)
    assert result.size == blank_image.size


def test_overlay_bboxes_does_not_mutate_original(blank_image):
    from document_simulator.ui.components.image_display import overlay_bboxes

    original_bytes = blank_image.tobytes()
    overlay_bboxes(blank_image, [[[10, 5], [80, 5], [80, 25], [10, 25]]], [0.9])
    assert blank_image.tobytes() == original_bytes


def test_overlay_bboxes_multiple_boxes(blank_image):
    from document_simulator.ui.components.image_display import overlay_bboxes

    boxes = [
        [[10, 5], [80, 5], [80, 25], [10, 25]],
        [[90, 5], [180, 5], [180, 25], [90, 25]],
    ]
    result = overlay_bboxes(blank_image, boxes, [0.9, 0.6])
    assert isinstance(result, Image.Image)


# ---------------------------------------------------------------------------
# image_to_bytes
# ---------------------------------------------------------------------------


def test_image_to_bytes_returns_bytes(blank_image):
    from document_simulator.ui.components.image_display import image_to_bytes

    result = image_to_bytes(blank_image)
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_image_to_bytes_accepts_numpy():
    from document_simulator.ui.components.image_display import image_to_bytes

    arr = np.full((50, 50, 3), 200, dtype=np.uint8)
    result = image_to_bytes(arr)
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_image_to_bytes_is_valid_png(blank_image):
    from document_simulator.ui.components.image_display import image_to_bytes

    data = image_to_bytes(blank_image)
    # PNG magic bytes
    assert data[:8] == b"\x89PNG\r\n\x1a\n"


def test_image_to_bytes_jpeg_format(blank_image):
    from document_simulator.ui.components.image_display import image_to_bytes

    data = image_to_bytes(blank_image, fmt="JPEG")
    # JPEG magic bytes
    assert data[:2] == b"\xff\xd8"
