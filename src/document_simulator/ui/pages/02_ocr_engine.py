"""OCR Engine — upload a document image or PDF, extract text, visualise bounding boxes."""

import pandas as pd
import streamlit as st

from document_simulator.ui.components.file_uploader import (
    uploaded_file_to_pil,
    uploaded_pdf_to_pil_pages,
)
from document_simulator.ui.components.image_display import image_to_bytes, overlay_bboxes
from document_simulator.ui.state.session_state import SessionStateManager

st.set_page_config(page_title="OCR Engine", page_icon="🔍", layout="wide")
st.title("🔍 OCR Engine")
st.info(
    "**How to use:** Upload a document image or PDF, select language and GPU settings "
    "in the sidebar, then click **Run OCR**. Multi-page PDFs show a page selector — "
    "choose which page to process. Optionally upload a plain-text ground truth file "
    "(.txt) to compute CER and WER against the OCR output. "
    "Use this page to test OCR quality on a single document before running bulk evaluation."
)

state = SessionStateManager()


# ── Helpers ───────────────────────────────────────────────────────────────────


@st.cache_resource
def _get_ocr_engine(lang: str, use_gpu: bool):
    """Cache the OCREngine so it is only instantiated once per (lang, gpu) combo."""
    from document_simulator.ocr import OCREngine

    return OCREngine(use_gpu=use_gpu, lang=lang)


def _build_region_df(ocr_result: dict) -> pd.DataFrame:
    """Convert an OCR result dict to a per-region DataFrame."""
    texts = ocr_result.get("text", "").split("\n")
    scores = ocr_result.get("scores", [])
    boxes = ocr_result.get("boxes", [])
    rows = []
    for i, (score, box) in enumerate(zip(scores, boxes)):
        rows.append(
            {
                "#": i + 1,
                "Text": texts[i] if i < len(texts) else "",
                "Confidence": round(float(score), 4),
                "Box (top-left x, y)": f"({int(box[0][0])}, {int(box[0][1])})",
            }
        )
    return pd.DataFrame(rows)


def _init_pdf_state() -> None:
    for key, val in [
        ("ocr_is_pdf", False),
        ("ocr_pdf_pages", []),
        ("ocr_pdf_page_idx", 0),
    ]:
        if key not in st.session_state:
            st.session_state[key] = val


_init_pdf_state()


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    lang = st.selectbox("Language", ["en", "ch", "fr", "de", "es", "ja", "ko"], index=0)
    use_gpu = st.checkbox("Use GPU", value=False)
    gt_file = st.file_uploader(
        "Ground truth text (optional)", type=["txt"], key="ocr_gt"
    )
    run_btn = st.button("Run OCR", type="primary")
    if st.button("Clear engine cache", help="Force re-initialise the OCR engine"):
        st.cache_resource.clear()
        st.rerun()

# ── Upload ────────────────────────────────────────────────────────────────────

uploaded = st.file_uploader(
    "Upload a document image or PDF",
    type=["png", "jpg", "jpeg", "bmp", "tiff", "pdf"],
    key="ocr_upload",
)
if uploaded is not None:
    if uploaded.name.lower().endswith(".pdf"):
        try:
            pages = uploaded_pdf_to_pil_pages(uploaded, dpi=150)
            st.session_state["ocr_is_pdf"] = True
            st.session_state["ocr_pdf_pages"] = pages
            if st.session_state.get("ocr_pdf_page_idx", 0) >= len(pages):
                st.session_state["ocr_pdf_page_idx"] = 0
            state.set_uploaded_image(pages[st.session_state["ocr_pdf_page_idx"]])
            state.set_ocr_result(None)
        except ImportError:
            st.error(
                "PDF support requires PyMuPDF. "
                "Install with: `uv sync --extra synthesis --native-tls`"
            )
    else:
        st.session_state["ocr_is_pdf"] = False
        st.session_state["ocr_pdf_pages"] = []
        state.set_uploaded_image(uploaded_file_to_pil(uploaded))
        state.set_ocr_result(None)

# ── Page selector (PDF only) ───────────────────────────────────────────────────

is_pdf: bool = st.session_state.get("ocr_is_pdf", False)
pdf_pages: list = st.session_state.get("ocr_pdf_pages", [])

if is_pdf and len(pdf_pages) > 1:
    st.info(f"PDF has **{len(pdf_pages)} pages**. Select the page to run OCR on.")
    new_idx = (
        st.slider("Page", min_value=1, max_value=len(pdf_pages), value=1, key="ocr_page_slider") - 1
    )
    if new_idx != st.session_state.get("ocr_pdf_page_idx", 0):
        st.session_state["ocr_pdf_page_idx"] = new_idx
        state.set_uploaded_image(pdf_pages[new_idx])
        state.set_ocr_result(None)
elif is_pdf and len(pdf_pages) == 1:
    st.info("Single-page PDF loaded.")

# ── Run ───────────────────────────────────────────────────────────────────────

if run_btn:
    src = state.get_uploaded_image()
    if src is None:
        st.warning("Please upload a document first.")
    else:
        with st.spinner("Running OCR…"):
            engine = _get_ocr_engine(str(lang), bool(use_gpu))
            result = engine.recognize(src)
            state.set_ocr_result(result)

# ── Display ───────────────────────────────────────────────────────────────────

result = state.get_ocr_result()
src = state.get_uploaded_image()

if result is not None and src is not None:
    from document_simulator.ocr.metrics import (
        aggregate_confidence,
        calculate_cer,
        calculate_wer,
    )

    conf = aggregate_confidence(result.get("scores", []))
    n_regions = len(result.get("boxes", []))

    # Page label for PDF inputs
    page_label = ""
    if is_pdf and pdf_pages:
        idx = st.session_state.get("ocr_pdf_page_idx", 0)
        page_label = f" — page {idx + 1}/{len(pdf_pages)}"

    # Annotated image
    annotated = overlay_bboxes(src, result.get("boxes", []), result.get("scores", []))
    st.image(annotated, caption=f"Detected text regions{page_label}", use_container_width=True)

    # Metric row
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Mean Confidence", f"{conf:.3f}")
    col2.metric("Regions Detected", n_regions)

    if gt_file is not None:
        gt_text = gt_file.read().decode("utf-8", errors="replace")
        cer = calculate_cer(result.get("text", ""), gt_text)
        wer = calculate_wer(result.get("text", ""), gt_text)
        col3.metric("CER vs GT", f"{cer:.3f}")
        col4.metric("WER vs GT", f"{wer:.3f}")

    # Extracted text
    st.subheader("Extracted Text")
    st.text_area(
        "Full extracted text",
        value=result.get("text", ""),
        height=160,
        disabled=True,
        label_visibility="collapsed",
    )

    # Download extracted text
    st.download_button(
        "Download extracted text",
        data=(result.get("text", "") or "").encode(),
        file_name="extracted_text.txt",
        mime="text/plain",
    )

    # Region table
    st.subheader("Region Details")
    df = _build_region_df(result)
    if not df.empty:
        st.dataframe(df, use_container_width=True)

elif src is not None:
    st.image(src, caption="Uploaded document", use_container_width=True)
    st.info("Click **Run OCR** in the sidebar to extract text.")
