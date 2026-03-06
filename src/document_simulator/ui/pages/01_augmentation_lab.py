"""Augmentation Lab — upload a document image or PDF, pick a preset, inspect the result."""

import io

import streamlit as st
from PIL import Image

from document_simulator.augmentation import DocumentAugmenter
from document_simulator.ui.components.file_uploader import (
    image_format_from_name,
    list_sample_files,
    load_path_as_pil_pages,
    pil_to_pdf_bytes,
    uploaded_file_to_pil,
    uploaded_pdf_to_pil_pages,
)
from document_simulator.ui.components.image_display import image_to_bytes, show_side_by_side
from document_simulator.ui.state.session_state import SessionStateManager

st.set_page_config(page_title="Augmentation Lab", page_icon="🔬", layout="wide")
st.title("🔬 Augmentation Lab")
st.info(
    "**How to use:** Upload a document image (PNG/JPG/BMP/TIFF) or a PDF, select an "
    "augmentation preset (**light / medium / heavy**) in the sidebar, then click **Augment**. "
    "Multi-page PDFs show a page selector — choose a page before augmenting. "
    "Download the result as PNG or PDF. "
    "Use this page to inspect what augmentation looks like before running a full batch."
)

state = SessionStateManager()


# ── Helpers ───────────────────────────────────────────────────────────────────


def _run_augmentation(src: Image.Image, preset: str) -> Image.Image:
    """Augment *src* with the chosen preset; always return a PIL Image."""
    import numpy as np

    augmenter = DocumentAugmenter(pipeline=preset)
    result = augmenter.augment(src)
    if not isinstance(result, Image.Image):
        result = Image.fromarray(np.array(result))
    return result


def _init_pdf_state() -> None:
    for key, val in [
        ("aug_is_pdf", False),
        ("aug_pdf_pages", []),
        ("aug_pdf_page_idx", 0),
        ("aug_pdf_dpi", 150),
        ("aug_original_filename", "augmented.png"),
    ]:
        if key not in st.session_state:
            st.session_state[key] = val


_init_pdf_state()


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    preset = st.radio(
        "Pipeline preset",
        options=["light", "medium", "heavy"],
        index=1,
        key="aug_preset",
    )

    with st.expander("Advanced parameters (12-dim action)"):
        st.caption(
            "These sliders display the parameter ranges for the selected preset. "
            "Check **Use custom sliders** to override the preset."
        )
        ink_bleed_p = st.slider("InkBleed probability", 0.0, 1.0, 0.5, 0.01)
        ink_bleed_intens = st.slider("InkBleed intensity max", 0.0, 1.0, 0.5, 0.01)
        fading_p = st.slider("Fading (LowLightNoise) probability", 0.0, 1.0, 0.3, 0.01)
        fading_val = st.slider("Fading value max", 0.0, 1.0, 0.5, 0.01)
        markup_p = st.slider("Markup probability", 0.0, 1.0, 0.3, 0.01)
        noise_p = st.slider("NoiseTexturize probability", 0.0, 1.0, 0.5, 0.01)
        noise_sigma = st.slider("NoiseTexturize sigma max", 0.0, 20.0, 5.0, 0.5)
        color_shift_p = st.slider("ColorShift probability", 0.0, 1.0, 0.3, 0.01)
        brightness_p = st.slider("Brightness probability", 0.0, 1.0, 0.5, 0.01)
        brightness_spr = st.slider("Brightness spread", 0.0, 0.4, 0.2, 0.01)
        gamma_p = st.slider("Gamma probability", 0.0, 1.0, 0.3, 0.01)
        jpeg_p = st.slider("Jpeg probability", 0.0, 1.0, 0.4, 0.01)

    run_btn = st.button("Augment", type="primary")

# ── Upload area ───────────────────────────────────────────────────────────────

uploaded = st.file_uploader(
    "Upload a document image or PDF",
    type=["png", "jpg", "jpeg", "bmp", "tiff", "pdf"],
    key="aug_upload",
)

if uploaded is not None:
    if uploaded.name.lower().endswith(".pdf"):
        try:
            pages = uploaded_pdf_to_pil_pages(uploaded, dpi=150)
            st.session_state["aug_is_pdf"] = True
            st.session_state["aug_pdf_pages"] = pages
            st.session_state["aug_pdf_dpi"] = 150
            st.session_state["aug_original_filename"] = uploaded.name
            # Reset page index only when a new file is loaded
            if st.session_state.get("aug_pdf_page_idx", 0) >= len(pages):
                st.session_state["aug_pdf_page_idx"] = 0
            state.set_uploaded_image(pages[st.session_state["aug_pdf_page_idx"]])
            state.set_aug_image(None)
        except ImportError:
            st.error(
                "PDF support requires PyMuPDF. "
                "Install with: `uv sync --extra synthesis --native-tls`"
            )
    else:
        st.session_state["aug_is_pdf"] = False
        st.session_state["aug_pdf_pages"] = []
        st.session_state["aug_original_filename"] = uploaded.name
        state.set_uploaded_image(uploaded_file_to_pil(uploaded))
        state.set_aug_image(None)

# ── Sample data ───────────────────────────────────────────────────────────────

_aug_samples = list_sample_files("augmentation_lab", (".pdf", ".png", ".jpg", ".jpeg", ".bmp", ".tiff"))
if _aug_samples:
    st.divider()
    _aug_sample_names = [p.name for p in _aug_samples]
    _aug_col1, _aug_col2 = st.columns([3, 1])
    _aug_selected = _aug_col1.selectbox(
        "Or choose a sample document",
        options=["— select —"] + _aug_sample_names,
        key="aug_sample_select",
    )
    if _aug_col2.button("Load sample", key="aug_load_sample") and _aug_selected != "— select —":
        _aug_path = _aug_samples[_aug_sample_names.index(_aug_selected)]
        try:
            _aug_pages = load_path_as_pil_pages(_aug_path)
            if _aug_path.suffix.lower() == ".pdf":
                st.session_state["aug_is_pdf"] = True
                st.session_state["aug_pdf_pages"] = _aug_pages
                st.session_state["aug_pdf_page_idx"] = 0
                st.session_state["aug_pdf_dpi"] = 150
            else:
                st.session_state["aug_is_pdf"] = False
                st.session_state["aug_pdf_pages"] = []
            st.session_state["aug_original_filename"] = _aug_path.name
            state.set_uploaded_image(_aug_pages[0])
            state.set_aug_image(None)
            st.rerun()
        except ImportError as e:
            st.error(str(e))

# ── Page selector (PDF only) ───────────────────────────────────────────────────

is_pdf: bool = st.session_state.get("aug_is_pdf", False)
pdf_pages: list = st.session_state.get("aug_pdf_pages", [])

if is_pdf and len(pdf_pages) > 1:
    st.info(f"PDF has **{len(pdf_pages)} pages**. Select the page to augment.")
    new_idx = (
        st.slider("Page", min_value=1, max_value=len(pdf_pages), value=1, key="aug_page_slider") - 1
    )
    if new_idx != st.session_state.get("aug_pdf_page_idx", 0):
        st.session_state["aug_pdf_page_idx"] = new_idx
        state.set_uploaded_image(pdf_pages[new_idx])
        state.set_aug_image(None)
elif is_pdf and len(pdf_pages) == 1:
    st.info("Single-page PDF loaded.")

# ── Run ───────────────────────────────────────────────────────────────────────

if run_btn:
    src = state.get_uploaded_image()
    if src is None:
        st.warning("Please upload a document first.")
    else:
        with st.spinner("Augmenting…"):
            aug = _run_augmentation(src, str(preset))
        state.set_aug_image(aug)

# ── Display ───────────────────────────────────────────────────────────────────

orig = state.get_uploaded_image()
aug = state.get_aug_image()

if orig is not None and aug is not None:
    page_label = ""
    if is_pdf and pdf_pages:
        idx = st.session_state.get("aug_pdf_page_idx", 0)
        page_label = f" — page {idx + 1}/{len(pdf_pages)}"

    show_side_by_side(
        orig,
        aug,
        labels=(f"Original{page_label}", f"Augmented{page_label}"),
    )

    with st.expander("Parameters applied"):
        st.json(
            {
                "preset": preset,
                "ink_bleed_p": ink_bleed_p,
                "ink_bleed_intensity_max": ink_bleed_intens,
                "fading_p": fading_p,
                "fading_value_max": fading_val,
                "markup_p": markup_p,
                "noise_p": noise_p,
                "noise_sigma_max": noise_sigma,
                "color_shift_p": color_shift_p,
                "brightness_p": brightness_p,
                "brightness_spread": brightness_spr,
                "gamma_p": gamma_p,
                "jpeg_p": jpeg_p,
            }
        )

    # Download — always use the same format as the original upload
    original_name = st.session_state.get("aug_original_filename", "augmented.png")
    stem = original_name.rsplit(".", 1)[0] if "." in original_name else original_name
    if is_pdf:
        dpi = st.session_state.get("aug_pdf_dpi", 150)
        st.download_button(
            "⬇ Download as PDF",
            data=pil_to_pdf_bytes(aug, dpi=dpi),
            file_name=f"{stem}_augmented.pdf",
            mime="application/pdf",
        )
    else:
        pil_fmt, mime = image_format_from_name(original_name)
        ext = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else "png"
        st.download_button(
            f"⬇ Download as {pil_fmt}",
            data=image_to_bytes(aug, fmt=pil_fmt),
            file_name=f"{stem}_augmented.{ext}",
            mime=mime,
        )

elif orig is not None:
    page_label = ""
    if is_pdf and pdf_pages:
        idx = st.session_state.get("aug_pdf_page_idx", 0)
        page_label = f" (page {idx + 1}/{len(pdf_pages)})"
    st.image(orig, caption=f"Uploaded document{page_label}", use_container_width=True)
    st.info("Click **Augment** in the sidebar to apply augmentation.")
