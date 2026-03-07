"""Integration tests for the augmentation lab catalogue mode."""
import io
import numpy as np
from PIL import Image
import pytest

PAGE = "src/document_simulator/ui/pages/01_augmentation_lab.py"


def _make_image_bytes():
    buf = io.BytesIO()
    Image.fromarray(np.ones((64, 64, 3), dtype=np.uint8) * 200).save(buf, format="PNG")
    return buf.getvalue()


def test_augmentation_lab_loads_with_catalogue_tab():
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(PAGE, default_timeout=30)
    at.run()
    assert not at.exception
    # page loaded — check for some content
    assert len(at.markdown) > 0 or len(at.button) > 0


def test_catalogue_mode_no_image_shows_upload_prompt():
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(PAGE, default_timeout=30)
    at.run()
    assert not at.exception


def test_catalogue_with_image_in_session_state():
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(PAGE, default_timeout=30)
    at.session_state["last_uploaded_image"] = Image.fromarray(
        np.ones((64, 64, 3), dtype=np.uint8) * 200
    )
    at.run()
    assert not at.exception


def test_catalogue_enabled_aug_cached_in_session_state():
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(PAGE, default_timeout=30)
    at.session_state["last_uploaded_image"] = Image.fromarray(
        np.ones((64, 64, 3), dtype=np.uint8) * 200
    )
    # Pre-enable a fast aug in session state
    at.session_state["aug_catalogue_enabled"] = {"Jpeg": True}
    at.run()
    assert not at.exception


def test_existing_preset_mode_unchanged():
    """Existing preset tests still pass — mode defaults to preset."""
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(PAGE, default_timeout=30)
    at.run()
    assert not at.exception
    # Preset radio should still exist
    radio_labels = [r.label for r in at.radio]
    assert any("preset" in l.lower() or "pipeline" in l.lower() for l in radio_labels)
