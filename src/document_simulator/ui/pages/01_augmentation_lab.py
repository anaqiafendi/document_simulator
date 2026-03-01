"""Augmentation Lab — upload a document image, pick a preset, inspect the result."""

import streamlit as st
from PIL import Image

from document_simulator.augmentation import DocumentAugmenter
from document_simulator.ui.components.file_uploader import uploaded_file_to_pil
from document_simulator.ui.components.image_display import image_to_bytes, show_side_by_side
from document_simulator.ui.state.session_state import SessionStateManager

st.set_page_config(page_title="Augmentation Lab", page_icon="🔬", layout="wide")
st.title("🔬 Augmentation Lab")

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

    run_btn = st.button("Augment Image", type="primary")

# ── Upload area ───────────────────────────────────────────────────────────────

uploaded = st.file_uploader(
    "Upload a document image",
    type=["png", "jpg", "jpeg", "bmp", "tiff"],
    key="aug_upload",
)
if uploaded is not None:
    state.set_uploaded_image(uploaded_file_to_pil(uploaded))

# ── Run ───────────────────────────────────────────────────────────────────────

if run_btn:
    src = state.get_uploaded_image()
    if src is None:
        st.warning("Please upload an image first.")
    else:
        with st.spinner("Augmenting…"):
            aug = _run_augmentation(src, str(preset))
        state.set_aug_image(aug)

# ── Display ───────────────────────────────────────────────────────────────────

orig = state.get_uploaded_image()
aug = state.get_aug_image()

if orig is not None and aug is not None:
    show_side_by_side(orig, aug)

    # Parameter summary
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

    st.download_button(
        "Download augmented image",
        data=image_to_bytes(aug),
        file_name="augmented.png",
        mime="image/png",
    )
elif orig is not None:
    st.image(orig, caption="Uploaded image", use_container_width=True)
    st.info("Click **Augment Image** in the sidebar to apply augmentation.")
