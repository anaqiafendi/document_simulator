"""Integration tests for the Synthetic Document Generator stub page."""

from streamlit.testing.v1 import AppTest

PAGE = "src/document_simulator/ui/pages/00_synthetic_generator.py"
TIMEOUT = 30


def test_stub_page_loads_without_exception():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    assert not at.exception


def test_stub_page_contains_zone_editor_link():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    # The page renders a markdown link to http://localhost:8000
    all_markdown = " ".join(str(e.value) for e in at.markdown)
    assert "localhost:8000" in all_markdown


def test_stub_page_contains_info_message():
    at = AppTest.from_file(PAGE, default_timeout=TIMEOUT)
    at.run()
    # st.info renders as an alert-info element — check at.info list
    assert len(at.info) > 0
