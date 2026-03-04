"""Unit tests for TemplateLoader (template.py)."""

import io
import tempfile
from pathlib import Path

import pytest
from PIL import Image

from document_simulator.synthesis.template import TemplateLoader


def test_template_loader_blank_page():
    img = TemplateLoader.blank(width=400, height=300)
    assert isinstance(img, Image.Image)
    assert img.size == (400, 300)
    assert img.mode == "RGB"


def test_template_loader_blank_page_is_white():
    img = TemplateLoader.blank(width=100, height=100)
    pixel = img.getpixel((50, 50))
    assert pixel == (255, 255, 255)


def test_template_loader_from_image_file(tmp_path):
    src = Image.new("RGB", (200, 150), color=(200, 200, 200))
    path = tmp_path / "doc.png"
    src.save(path)
    loaded = TemplateLoader.from_image(str(path))
    assert isinstance(loaded, Image.Image)
    assert loaded.size == (200, 150)


def test_template_loader_from_image_converts_to_rgb(tmp_path):
    src = Image.new("L", (100, 80), color=128)
    path = tmp_path / "grey.png"
    src.save(path)
    loaded = TemplateLoader.from_image(str(path))
    assert loaded.mode == "RGB"


def test_template_loader_from_image_invalid_path_raises():
    with pytest.raises((FileNotFoundError, OSError)):
        TemplateLoader.from_image("/nonexistent/path/doc.png")


def test_template_loader_load_dispatches_blank():
    img = TemplateLoader.load("blank", width=300, height=200)
    assert img.size == (300, 200)


def test_template_loader_load_dispatches_image(tmp_path):
    src = Image.new("RGB", (150, 100), color=(10, 20, 30))
    path = tmp_path / "test.png"
    src.save(path)
    img = TemplateLoader.load(str(path))
    assert img.size == (150, 100)
