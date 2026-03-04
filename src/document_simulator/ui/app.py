"""Document Simulator — Streamlit home page and entry point.

Run with:
    uv run streamlit run src/document_simulator/ui/app.py
or via the installed script:
    document-simulator-ui
"""

import subprocess
import sys

import streamlit as st

from document_simulator.ui.components.file_uploader import uploaded_file_to_pil
from document_simulator.ui.components.image_display import image_to_bytes, show_side_by_side

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="Document Simulator",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Title ─────────────────────────────────────────────────────────────────────
st.title("📄 Document Simulator")
st.caption("Synthetic document generation · Augmentation · OCR · Evaluation · RL Optimisation")
st.divider()

# ── Navigation cards ──────────────────────────────────────────────────────────
col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.markdown("### ✨ Synthetic Generator")
    st.caption("Generate filled documents from a template with auto-annotated JSON pairs.")
    st.page_link("pages/00_synthetic_generator.py", label="Open →")

with col2:
    st.markdown("### 🔬 Augmentation Lab")
    st.caption("Upload a document, choose a preset, see before/after, download.")
    st.page_link("pages/01_augmentation_lab.py", label="Open →")

with col3:
    st.markdown("### 🔍 OCR Engine")
    st.caption("Extract text with bounding boxes and confidence scores.")
    st.page_link("pages/02_ocr_engine.py", label="Open →")

with col4:
    st.markdown("### ⚙️ Batch Processing")
    st.caption("Augment many documents at once and download as ZIP.")
    st.page_link("pages/03_batch_processing.py", label="Open →")

with col5:
    st.markdown("### 📊 Evaluation")
    st.caption("Compare CER / WER / confidence across a dataset.")
    st.page_link("pages/04_evaluation.py", label="Open →")

with col6:
    st.markdown("### 🤖 RL Training")
    st.caption("Learn optimal augmentation parameters with PPO.")
    st.page_link("pages/05_rl_training.py", label="Open →")

st.divider()

# ── Quick-start single-image augmentation ─────────────────────────────────────
st.subheader("Quick Augment")
st.caption("Drop any document image below to augment it immediately with the *medium* preset.")

uploaded = st.file_uploader(
    "Choose a document image",
    type=["png", "jpg", "jpeg", "bmp", "tiff"],
    key="home_upload",
)

quick_btn = st.button("Augment →", type="primary", disabled=uploaded is None)

if quick_btn and uploaded:
    from PIL import Image

    from document_simulator.augmentation import DocumentAugmenter

    with st.spinner("Augmenting…"):
        pil = uploaded_file_to_pil(uploaded)
        aug = DocumentAugmenter(pipeline="medium").augment(pil)
        if not isinstance(aug, Image.Image):
            import numpy as np

            aug = Image.fromarray(np.array(aug))

    show_side_by_side(pil, aug)
    st.download_button(
        "Download augmented image",
        data=image_to_bytes(aug),
        file_name="augmented.png",
        mime="image/png",
    )


def launch() -> None:
    """Entry point for the ``document-simulator-ui`` console script."""
    subprocess.run(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            __file__,
            "--server.headless",
            "true",
        ],
        check=True,
    )
