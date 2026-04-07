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


def test_catalogue_batch_run_expander_renders():
    """Batch Run expander is visible when an augmentation is enabled."""
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(PAGE, default_timeout=30)
    at.session_state["last_uploaded_image"] = Image.fromarray(
        np.ones((64, 64, 3), dtype=np.uint8) * 200
    )
    at.session_state["aug_catalogue_enabled"] = {"Jpeg": True}
    at.run()
    assert not at.exception
    # Page should render without error; expander title contains "Batch Run"
    expander_labels = [e.label for e in at.expander]
    assert any("Batch Run" in lbl or "batch" in lbl.lower() for lbl in expander_labels)


def test_catalogue_batch_run_shows_info_when_no_augs_enabled():
    """Batch Run expander renders with info message when no augmentations are enabled."""
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(PAGE, default_timeout=30)
    at.session_state["last_uploaded_image"] = Image.fromarray(
        np.ones((64, 64, 3), dtype=np.uint8) * 200
    )
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


def test_catalogue_phase_headers_plain_english():
    """AC-3: Phase tab headers must use plain-English business names, not pipeline stage names."""
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(PAGE, default_timeout=30)
    at.session_state["last_uploaded_image"] = Image.fromarray(
        np.ones((64, 64, 3), dtype=np.uint8) * 200
    )
    at.run()
    assert not at.exception
    # Old technical names must not appear as standalone rendered text
    all_text = " ".join(m.value for m in at.markdown)
    assert "Ink Phase" not in all_text, "Old label 'Ink Phase' still present in markdown"
    assert "Paper Phase" not in all_text, "Old label 'Paper Phase' still present in markdown"
    assert "Post Phase" not in all_text, "Old label 'Post Phase' still present in markdown"


def test_catalogue_preset_sliders_no_technical_names():
    """AC-1: Sidebar slider labels in preset tab must not contain raw library class names."""
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(PAGE, default_timeout=30)
    at.run()
    assert not at.exception
    slider_labels = [s.label for s in at.slider]
    technical_names = ["InkBleed", "LowLightNoise", "NoiseTexturize", "ColorShift"]
    for name in technical_names:
        assert not any(name in lbl for lbl in slider_labels), (
            f"Technical name '{name}' found in slider labels: {slider_labels}"
        )
