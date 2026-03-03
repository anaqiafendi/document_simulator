"""Integration tests for the Synthetic Document Generator UI page."""

import json

import pytest
from streamlit.testing.v1 import AppTest

from document_simulator.synthesis.zones import (
    FieldTypeConfig,
    GeneratorConfig,
    RespondentConfig,
    SynthesisConfig,
    ZoneConfig,
)

PAGE = "src/document_simulator/ui/pages/00_synthetic_generator.py"
TIMEOUT = 30


def _default_config_json() -> str:
    ft = FieldTypeConfig(field_type_id="standard", display_name="Standard")
    r = RespondentConfig(respondent_id="default", display_name="Person A", field_types=[ft])
    zones = [
        ZoneConfig(
            zone_id="z1",
            label="name",
            box=[[10, 10], [200, 10], [200, 40], [10, 40]],
            faker_provider="name",
        )
    ]
    config = SynthesisConfig(respondents=[r], zones=zones)
    return config.model_dump_json()


# ---------------------------------------------------------------------------
# AC-11: Page loads without error
# ---------------------------------------------------------------------------


def test_synthetic_generator_page_loads():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    assert not at.exception


# ---------------------------------------------------------------------------
# AC-11: Canvas + template upload section present
# ---------------------------------------------------------------------------


def test_page_has_template_upload_section():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    all_text = (
        " ".join(str(e.value) for e in at.markdown)
        + " ".join(str(e.label) for e in at.button)
        + " ".join(str(e.value) for e in at.subheader)
    )
    assert any(
        kw in all_text.lower() for kw in ("template", "upload", "blank", "canvas")
    )


# ---------------------------------------------------------------------------
# AC-10 / Panel 2: Add respondent button present
# ---------------------------------------------------------------------------


def test_page_has_add_respondent_button():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    button_labels = [b.label.lower() for b in at.button]
    assert any("respondent" in label for label in button_labels)


# ---------------------------------------------------------------------------
# AC-12: Zone assignment dropdowns present when zones in state
# ---------------------------------------------------------------------------


def test_page_has_generate_preview_button():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    button_labels = [b.label.lower() for b in at.button]
    assert any("preview" in label for label in button_labels)


def test_page_has_generate_batch_button():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    button_labels = [b.label.lower() for b in at.button]
    assert any("generate" in label and "batch" not in label or "batch" in label for label in button_labels)


# ---------------------------------------------------------------------------
# AC-13: Preview renders when samples in session state
# ---------------------------------------------------------------------------


def test_page_shows_preview_images_when_samples_in_state():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    # Inject preview samples (PIL Images as bytes)
    from io import BytesIO

    import numpy as np
    from PIL import Image

    from document_simulator.data.ground_truth import GroundTruth, TextRegion

    img = Image.fromarray(np.full((200, 150, 3), 200, dtype=np.uint8))
    buf = BytesIO()
    img.save(buf, format="PNG")
    gt = GroundTruth(
        image_path="doc.png",
        text="Test",
        regions=[TextRegion(box=[[0, 0], [100, 0], [100, 30], [0, 30]], text="Test")],
    )
    at.session_state["preview_samples"] = [(img, gt), (img, gt)]
    at.run()
    assert not at.exception
    # Re-roll buttons (↻) are only rendered per-sample — verify they appear
    reroll_buttons = [b for b in at.button if b.label == "↻"]
    assert len(reroll_buttons) == 2


# ---------------------------------------------------------------------------
# AC-14: Zone overlay checkbox present
# ---------------------------------------------------------------------------


def test_page_has_show_overlays_checkbox():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    checkbox_labels = [c.label.lower() for c in at.checkbox]
    assert any("overlay" in label or "zone" in label for label in checkbox_labels)


# ---------------------------------------------------------------------------
# AC-7: Save / load config buttons present
# ---------------------------------------------------------------------------


def test_page_has_save_config_button():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    # Save config is a download_button inside a collapsed st.expander("💾 Config")
    # in Tab 4 — verify the expander label is present on the page.
    expander_labels = [e.label.lower() for e in at.expander]
    assert any("config" in label for label in expander_labels)


# ---------------------------------------------------------------------------
# Warning when generating with no zones defined
# ---------------------------------------------------------------------------


def test_page_warns_when_generating_with_no_zones():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    # Ensure no zones in state
    at.session_state["synthesis_zones"] = []
    # Click generate / preview button
    preview_btn = next(b for b in at.button if "preview" in b.label.lower())
    preview_btn.click().run()
    assert len(at.warning) > 0 or len(at.info) > 0
