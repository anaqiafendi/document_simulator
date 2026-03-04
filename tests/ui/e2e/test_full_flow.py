"""End-to-end tests: home page and cross-page navigation."""

import pytest
from streamlit.testing.v1 import AppTest


HOME = "src/document_simulator/ui/app.py"
TIMEOUT = 30


def test_home_page_loads():
    at = AppTest.from_file(HOME, default_timeout=TIMEOUT)
    at.run()
    assert not at.exception


def test_home_page_has_title():
    at = AppTest.from_file(HOME, default_timeout=TIMEOUT)
    at.run()
    titles = [t.value for t in at.title]
    assert any("document" in t.lower() or "simulator" in t.lower() for t in titles)


def test_home_page_has_quick_augment_button():
    at = AppTest.from_file(HOME, default_timeout=TIMEOUT)
    at.run()
    labels = [b.label for b in at.button]
    assert any("augment" in l.lower() for l in labels)


def test_home_page_quick_augment_disabled_without_upload():
    at = AppTest.from_file(HOME, default_timeout=TIMEOUT)
    at.run()
    augment_btn = next(b for b in at.button if "augment" in b.label.lower())
    assert augment_btn.disabled


def test_home_page_has_page_links():
    at = AppTest.from_file(HOME, default_timeout=TIMEOUT)
    at.run()
    # page_link widgets or markdown links
    assert len(at.markdown) > 0 or len(at.button) >= 1


def test_home_page_has_upload_section():
    """The home page should mention uploading in its text content."""
    at = AppTest.from_file(HOME, default_timeout=TIMEOUT)
    at.run()
    # st.file_uploader label appears as a caption/markdown element
    all_text = " ".join(
        m.value for m in at.caption
    ) + " ".join(
        m.value for m in at.markdown
    )
    assert "upload" in all_text.lower() or "image" in all_text.lower() or "drop" in all_text.lower()


def test_home_page_no_exception_on_rerun():
    at = AppTest.from_file(HOME, default_timeout=TIMEOUT)
    at.run()
    at.run()  # second run should also be clean
    assert not at.exception
