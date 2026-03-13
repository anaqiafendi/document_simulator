"""Tests for the OCR router endpoints."""

import io
import pytest
from PIL import Image, ImageDraw, ImageFont


@pytest.fixture
def simple_text_png_bytes():
    """A small white PNG with black text — recognisable by OCR."""
    img = Image.new("RGB", (200, 60), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), "Hello World", fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


@pytest.fixture
def blank_png_bytes():
    buf = io.BytesIO()
    Image.new("RGB", (100, 100), color=(255, 255, 255)).save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


def test_recognize_returns_200(client, blank_png_bytes):
    r = client.post(
        "/api/ocr/recognize",
        files={"file": ("test.png", blank_png_bytes, "image/png")},
        data={"lang": "en", "use_gpu": False},
    )
    assert r.status_code == 200, r.text


def test_recognize_response_shape(client, blank_png_bytes):
    r = client.post(
        "/api/ocr/recognize",
        files={"file": ("test.png", blank_png_bytes, "image/png")},
        data={"lang": "en", "use_gpu": False},
    )
    assert r.status_code == 200
    body = r.json()
    for key in ("text", "boxes", "scores", "mean_confidence", "n_regions", "annotated_b64"):
        assert key in body, f"Missing key: {key}"


def test_recognize_mean_confidence_is_float(client, blank_png_bytes):
    r = client.post(
        "/api/ocr/recognize",
        files={"file": ("test.png", blank_png_bytes, "image/png")},
        data={"lang": "en"},
    )
    assert r.status_code == 200
    conf = r.json()["mean_confidence"]
    assert isinstance(conf, float)
    assert 0.0 <= conf <= 1.0


def test_recognize_missing_file_returns_422(client):
    r = client.post("/api/ocr/recognize", data={"lang": "en"})
    assert r.status_code == 422


def test_recognize_annotated_b64_is_nonempty(client, blank_png_bytes):
    r = client.post(
        "/api/ocr/recognize",
        files={"file": ("test.png", blank_png_bytes, "image/png")},
        data={"lang": "en"},
    )
    assert r.status_code == 200
    assert len(r.json()["annotated_b64"]) > 100
