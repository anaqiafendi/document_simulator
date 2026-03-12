"""Tests for the augmentation router endpoints."""

import io
import pytest
from PIL import Image


@pytest.fixture
def tiny_png_bytes():
    buf = io.BytesIO()
    Image.new("RGB", (60, 80), color=(200, 200, 200)).save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


def test_presets_returns_200(client):
    r = client.get("/api/augmentation/presets")
    assert r.status_code == 200


def test_presets_contains_expected_names(client):
    r = client.get("/api/augmentation/presets")
    presets = r.json()["presets"]
    for name in ("light", "medium", "heavy", "default"):
        assert name in presets


def test_augment_returns_image_b64(client, tiny_png_bytes):
    r = client.post(
        "/api/augmentation/augment",
        files={"file": ("test.png", tiny_png_bytes, "image/png")},
        data={"preset": "light"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "augmented_b64" in body
    assert "original_b64" in body
    assert len(body["augmented_b64"]) > 100


def test_augment_returns_metadata(client, tiny_png_bytes):
    r = client.post(
        "/api/augmentation/augment",
        files={"file": ("doc.png", tiny_png_bytes, "image/png")},
        data={"preset": "medium"},
    )
    assert r.status_code == 200
    meta = r.json()["metadata"]
    assert meta["preset"] == "medium"
    assert meta["width"] == 60
    assert meta["height"] == 80


def test_augment_invalid_preset_returns_422(client, tiny_png_bytes):
    r = client.post(
        "/api/augmentation/augment",
        files={"file": ("doc.png", tiny_png_bytes, "image/png")},
        data={"preset": "nonexistent_preset"},
    )
    assert r.status_code == 422


def test_augment_missing_file_returns_422(client):
    r = client.post("/api/augmentation/augment", data={"preset": "light"})
    assert r.status_code == 422
