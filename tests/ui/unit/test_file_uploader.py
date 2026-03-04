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


# ---------------------------------------------------------------------------
# expand_uploads_to_pil
# ---------------------------------------------------------------------------


def test_expand_uploads_to_pil_mixed(small_image):
    """One image file + one 2-page PDF should yield 3 PIL Images with correct labels."""
    import unittest.mock as mock

    from document_simulator.ui.components.file_uploader import expand_uploads_to_pil

    # Fake image upload
    class _FakeFile:
        def __init__(self, name, data):
            self.name = name
            self._data = data

        def getvalue(self):
            return self._data

    buf = io.BytesIO()
    small_image.save(buf, format="PNG")
    img_file = _FakeFile("photo.png", buf.getvalue())

    page1 = Image.fromarray(np.full((30, 30, 3), 100, dtype=np.uint8))
    page2 = Image.fromarray(np.full((30, 30, 3), 150, dtype=np.uint8))

    # Fake PDF upload whose name ends with .pdf
    pdf_file = _FakeFile("report.pdf", b"%PDF-fake")

    with mock.patch(
        "document_simulator.ui.components.file_uploader.uploaded_pdf_to_pil_pages",
        return_value=[page1, page2],
    ):
        images, labels = expand_uploads_to_pil([img_file, pdf_file])

    assert len(images) == 3
    assert len(labels) == 3
    assert labels[0] == "photo.png"
    assert "page" in labels[1]
    assert "page" in labels[2]
    assert all(isinstance(img, Image.Image) for img in images)
