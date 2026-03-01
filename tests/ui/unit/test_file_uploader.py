"""Unit tests for file_uploader component."""

import io

import numpy as np
import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# is_valid_image_extension
# ---------------------------------------------------------------------------


def test_valid_jpg():
    from document_simulator.ui.components.file_uploader import is_valid_image_extension

    assert is_valid_image_extension("photo.jpg") is True


def test_valid_jpeg():
    from document_simulator.ui.components.file_uploader import is_valid_image_extension

    assert is_valid_image_extension("photo.jpeg") is True


def test_valid_png():
    from document_simulator.ui.components.file_uploader import is_valid_image_extension

    assert is_valid_image_extension("scan.PNG") is True


def test_valid_tiff():
    from document_simulator.ui.components.file_uploader import is_valid_image_extension

    assert is_valid_image_extension("doc.tiff") is True


def test_valid_bmp():
    from document_simulator.ui.components.file_uploader import is_valid_image_extension

    assert is_valid_image_extension("img.bmp") is True


def test_invalid_csv():
    from document_simulator.ui.components.file_uploader import is_valid_image_extension

    assert is_valid_image_extension("data.csv") is False


def test_invalid_zip():
    from document_simulator.ui.components.file_uploader import is_valid_image_extension

    assert is_valid_image_extension("model.zip") is False


def test_invalid_pdf():
    from document_simulator.ui.components.file_uploader import is_valid_image_extension

    assert is_valid_image_extension("document.pdf") is False


# ---------------------------------------------------------------------------
# uploaded_file_to_pil
# ---------------------------------------------------------------------------


def test_uploaded_file_to_pil_returns_pil_image(fake_uploaded_file):
    from document_simulator.ui.components.file_uploader import uploaded_file_to_pil

    result = uploaded_file_to_pil(fake_uploaded_file)
    assert isinstance(result, Image.Image)


def test_uploaded_file_to_pil_returns_rgb(fake_uploaded_file):
    from document_simulator.ui.components.file_uploader import uploaded_file_to_pil

    result = uploaded_file_to_pil(fake_uploaded_file)
    assert result.mode == "RGB"


def test_uploaded_file_to_pil_correct_size(small_image):
    from document_simulator.ui.components.file_uploader import uploaded_file_to_pil

    class _F:
        def getvalue(self):
            buf = io.BytesIO()
            small_image.save(buf, format="PNG")
            return buf.getvalue()

    result = uploaded_file_to_pil(_F())
    assert result.size == small_image.size


# ---------------------------------------------------------------------------
# uploaded_files_to_pil
# ---------------------------------------------------------------------------


def test_uploaded_files_to_pil_returns_list(fake_uploaded_file):
    from document_simulator.ui.components.file_uploader import uploaded_files_to_pil

    results = uploaded_files_to_pil([fake_uploaded_file, fake_uploaded_file])
    assert isinstance(results, list)
    assert len(results) == 2


def test_uploaded_files_to_pil_all_pil_images(fake_uploaded_file):
    from document_simulator.ui.components.file_uploader import uploaded_files_to_pil

    results = uploaded_files_to_pil([fake_uploaded_file] * 3)
    assert all(isinstance(r, Image.Image) for r in results)


def test_uploaded_files_to_pil_empty_list():
    from document_simulator.ui.components.file_uploader import uploaded_files_to_pil

    assert uploaded_files_to_pil([]) == []
