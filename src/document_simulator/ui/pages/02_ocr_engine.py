"""OCR Engine — upload a document image, extract text, visualise bounding boxes."""

import pandas as pd
import streamlit as st

from document_simulator.ui.components.file_uploader import uploaded_file_to_pil
from document_simulator.ui.components.image_display import image_to_bytes, overlay_bboxes
from document_simulator.ui.state.session_state import SessionStateManager

st.set_page_config(page_title="OCR Engine", page_icon="🔍", layout="wide")
st.title("🔍 OCR Engine")

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


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    lang = st.selectbox("Language", ["en", "ch", "fr", "de", "es", "ja", "ko"], index=0)
    use_gpu = st.checkbox("Use GPU", value=False)
    gt_file = st.file_uploader(
        "Ground truth text (optional)", type=["txt"], key="ocr_gt"
    )
    run_btn = st.button("Run OCR", type="primary")

# ── Upload ────────────────────────────────────────────────────────────────────

uploaded = st.file_uploader(
    "Upload a document image",
    type=["png", "jpg", "jpeg", "bmp", "tiff"],
    key="ocr_upload",
)
if uploaded is not None:
    state.set_uploaded_image(uploaded_file_to_pil(uploaded))

# ── Run ───────────────────────────────────────────────────────────────────────

if run_btn:
    src = state.get_uploaded_image()
    if src is None:
        st.warning("Please upload an image first.")
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

    # Annotated image
    annotated = overlay_bboxes(src, result.get("boxes", []), result.get("scores", []))
    st.image(annotated, caption="Detected text regions", use_container_width=True)

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
    st.image(src, caption="Uploaded image", use_container_width=True)
    st.info("Click **Run OCR** in the sidebar to extract text.")
