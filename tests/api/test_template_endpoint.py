import base64
from PIL import Image
import io


def test_post_template_png_returns_422(client, tiny_png_bytes):
    """PNG upload is rejected — only PDF templates are supported."""
    r = client.post("/api/template", files={"file": ("test.png", tiny_png_bytes, "image/png")})
    assert r.status_code == 422


def test_post_template_jpg_returns_422(client, tiny_png_bytes):
    """JPEG upload is rejected — only PDF templates are supported."""
    r = client.post("/api/template", files={"file": ("test.jpg", tiny_png_bytes, "image/jpeg")})
    assert r.status_code == 422


def test_post_template_pdf_returns_base64_image(client, minimal_pdf_bytes):
    r = client.post("/api/template", files={"file": ("test.pdf", minimal_pdf_bytes, "application/pdf")})
    data = r.json()
    assert "image_b64" in data
    assert len(data["image_b64"]) > 0
    # must be valid base64 PNG (PDF is rasterised server-side)
    img_bytes = base64.b64decode(data["image_b64"])
    img = Image.open(io.BytesIO(img_bytes))
    assert img.format == "PNG"


def test_post_template_pdf_returns_200(client, minimal_pdf_bytes):
    r = client.post("/api/template", files={"file": ("test.pdf", minimal_pdf_bytes, "application/pdf")})
    assert r.status_code == 200


def test_post_template_pdf_returns_is_pdf_true(client, minimal_pdf_bytes):
    r = client.post("/api/template", files={"file": ("test.pdf", minimal_pdf_bytes, "application/pdf")})
    assert r.json()["is_pdf"] is True


def test_post_template_pdf_renders_at_150_dpi(client, minimal_pdf_bytes):
    r = client.post("/api/template", files={"file": ("test.pdf", minimal_pdf_bytes, "application/pdf")})
    data = r.json()
    assert data["dpi"] == 150
    # A4 at 150 DPI: 595pt/72*150 ≈ 1240px
    assert data["width_px"] > 500


def test_post_template_unsupported_type_returns_422(client):
    r = client.post("/api/template", files={"file": ("test.txt", b"hello", "text/plain")})
    assert r.status_code == 422


def test_post_template_empty_file_returns_422(client):
    r = client.post("/api/template", files={"file": ("test.png", b"", "image/png")})
    assert r.status_code == 422
