"""Integration tests for the Augmentation Lab page."""

import io

import numpy as np
import pytest
from PIL import Image
from streamlit.testing.v1 import AppTest


PAGE = "src/document_simulator/ui/pages/01_augmentation_lab.py"
TIMEOUT = 30


def test_augmentation_lab_loads_without_error():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    assert not at.exception


def test_augmentation_lab_has_preset_radio():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    radio_labels = [r.label for r in at.radio]
    assert any("preset" in l.lower() or "pipeline" in l.lower() for l in radio_labels)


def test_augmentation_lab_preset_options():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    radio = next(r for r in at.radio if "preset" in r.label.lower() or "pipeline" in r.label.lower())
    option_values = [str(o) for o in radio.options]
    assert "light" in option_values
    assert "medium" in option_values
    assert "heavy" in option_values


def test_augmentation_lab_has_augment_button():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    labels = [b.label for b in at.button]
    assert any("augment" in l.lower() for l in labels)


def test_augmentation_lab_has_advanced_expander():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    expander_labels = [e.label for e in at.expander]
    assert any("advanced" in l.lower() or "parameter" in l.lower() for l in expander_labels)


def test_augmentation_lab_has_sliders():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    assert len(at.slider) >= 10  # 12 augmentation param sliders


def test_augmentation_lab_warning_when_no_image():
    """Clicking Augment without an image should show a warning."""
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    augment_btn = next(b for b in at.button if "augment" in b.label.lower())
    augment_btn.click().run()
    assert len(at.warning) > 0


def test_augmentation_lab_stores_aug_image_after_run():
    """After clicking Augment, the augmented image should be stored in session state."""
    from unittest.mock import MagicMock, patch

    fake_aug = Image.fromarray(np.full((50, 50, 3), 128, dtype=np.uint8))
    mock_augmenter = MagicMock()
    mock_augmenter.augment.return_value = fake_aug

    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    with patch("document_simulator.augmentation.DocumentAugmenter", return_value=mock_augmenter):
        at.run()
        at.session_state["last_uploaded_image"] = fake_aug
        augment_btn = next(b for b in at.button if "augment" in b.label.lower())
        augment_btn.click().run()

    # AppTest SafeSessionState doesn't support .get(); use `in` operator
    assert "last_aug_image" in at.session_state
