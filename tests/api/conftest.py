import io
import pytest
from starlette.testclient import TestClient
from PIL import Image


@pytest.fixture
def client():
    from document_simulator.api.app import app
    return TestClient(app)


@pytest.fixture
def tiny_png_bytes():
    buf = io.BytesIO()
    Image.new("RGB", (100, 80), color=(255, 255, 255)).save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


@pytest.fixture
def minimal_pdf_bytes():
    import fitz  # PyMuPDF
    doc = fitz.open()
    doc.new_page(width=595, height=842)  # A4
    buf = io.BytesIO()
    buf.write(doc.tobytes())
    buf.seek(0)
    return buf.read()


@pytest.fixture
def minimal_synthesis_config():
    # NOTE: GeneratorConfig has no 'batch_size' field — use 'n' instead.
    return {
        "respondents": [
            {
                "respondent_id": "default",
                "display_name": "Default",
                "field_types": [
                    {
                        "field_type_id": "standard",
                        "display_name": "Standard",
                        "font_family": "sans-serif",
                        "font_size_range": [10, 14],
                        "font_color": "#000000",
                        "bold": False,
                        "italic": False,
                        "fill_style": "typed",
                        "jitter_x": 0.0,
                        "jitter_y": 0.0,
                        "baseline_wander": 0.0,
                        "char_spacing_jitter": 0.0,
                    }
                ],
            }
        ],
        "zones": [],
        "generator": {
            "image_width": 200,
            "image_height": 200,
            "output_dir": "/tmp/test_output",
            "seed": 42,
            "n": 1,
        },
    }
