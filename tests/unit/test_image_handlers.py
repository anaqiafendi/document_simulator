"""Unit tests for ImageHandler."""

import io
from pathlib import Path

import numpy as np
import pytest
from PIL import Image, UnidentifiedImageError

from document_simulator.utils.image_io import ImageHandler


@pytest.fixture
def rgb_pil():
    return Image.new("RGB", (64, 64), color=(128, 64, 32))


@pytest.fixture
def rgb_numpy(rgb_pil):
    return np.array(rgb_pil)


@pytest.fixture
def image_bytes(rgb_pil, tmp_path):
    buf = io.BytesIO()
    rgb_pil.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def image_file(rgb_pil, tmp_path):
    p = tmp_path / "test.png"
    rgb_pil.save(p)
    return p


# ---------------------------------------------------------------------------
# load()
# ---------------------------------------------------------------------------

def test_load_from_path(image_file):
    img = ImageHandler.load(image_file)
    assert isinstance(img, Image.Image)
    assert img.size == (64, 64)


def test_load_from_string_path(image_file):
    img = ImageHandler.load(str(image_file))
    assert isinstance(img, Image.Image)


def test_load_from_pil(rgb_pil):
    img = ImageHandler.load(rgb_pil)
    assert isinstance(img, Image.Image)


def test_load_from_numpy(rgb_numpy):
    img = ImageHandler.load(rgb_numpy)
    assert isinstance(img, Image.Image)


def test_load_from_bytes(image_bytes):
    img = ImageHandler.load(image_bytes)
    assert isinstance(img, Image.Image)
    assert img.size == (64, 64)


def test_load_invalid_path():
    with pytest.raises(FileNotFoundError):
        ImageHandler.load("/nonexistent/image.jpg")


def test_load_corrupt_bytes():
    with pytest.raises((UnidentifiedImageError, Exception)):
        ImageHandler.load(b"not an image at all!!")


def test_load_unsupported_type():
    with pytest.raises(TypeError):
        ImageHandler.load(12345)


def test_load_returns_rgb(rgb_pil):
    gray = rgb_pil.convert("L")
    result = ImageHandler.load(gray)
    assert result.mode == "RGB"


# ---------------------------------------------------------------------------
# save()
# ---------------------------------------------------------------------------

def test_save_pil_image(rgb_pil, tmp_path):
    dest = tmp_path / "out.png"
    ImageHandler.save(rgb_pil, dest)
    assert dest.exists()


def test_save_numpy_array(rgb_numpy, tmp_path):
    dest = tmp_path / "out.png"
    ImageHandler.save(rgb_numpy, dest)
    assert dest.exists()


def test_save_creates_parent_dirs(rgb_pil, tmp_path):
    dest = tmp_path / "nested" / "dir" / "out.png"
    ImageHandler.save(rgb_pil, dest)
    assert dest.exists()


# ---------------------------------------------------------------------------
# to_numpy() / to_pil()
# ---------------------------------------------------------------------------

def test_to_numpy_from_pil(rgb_pil):
    arr = ImageHandler.to_numpy(rgb_pil)
    assert isinstance(arr, np.ndarray)
    assert arr.shape == (64, 64, 3)


def test_to_numpy_from_numpy(rgb_numpy):
    arr = ImageHandler.to_numpy(rgb_numpy)
    assert arr is rgb_numpy  # should be identity


def test_to_pil_from_numpy(rgb_numpy):
    img = ImageHandler.to_pil(rgb_numpy)
    assert isinstance(img, Image.Image)
    assert img.mode == "RGB"


def test_to_pil_from_pil(rgb_pil):
    img = ImageHandler.to_pil(rgb_pil)
    assert isinstance(img, Image.Image)


# ---------------------------------------------------------------------------
# to_grayscale()
# ---------------------------------------------------------------------------

def test_convert_rgb_to_grayscale(rgb_pil):
    gray = ImageHandler.to_grayscale(rgb_pil)
    assert gray.mode == "L"


# ---------------------------------------------------------------------------
# Format preservation
# ---------------------------------------------------------------------------

def test_load_batch(rgb_pil, image_file):
    results = ImageHandler.load_batch([rgb_pil, image_file])
    assert len(results) == 2
    for r in results:
        assert isinstance(r, Image.Image)
