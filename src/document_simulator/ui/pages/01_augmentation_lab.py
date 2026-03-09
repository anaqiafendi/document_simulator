"""Augmentation Lab — upload a document image or PDF, pick a preset or catalogue mode."""

import io
import time
import zipfile

import numpy as np
import streamlit as st
from PIL import Image

from document_simulator.augmentation import DocumentAugmenter
from document_simulator.augmentation.catalogue import CATALOGUE, apply_single, get_phase_augmentations
from document_simulator.ui.components.file_uploader import (
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
    "**How to use:** Upload a document image (PNG/JPG/BMP/TIFF) or a PDF. "
    "Use the **Preset** tab to apply a preset (light / medium / heavy), or the **Catalogue** "
    "tab to pick individual augmentations and tune their parameters. "
    "Download the result as PNG or PDF."
)

state = SessionStateManager()


# ── Helpers ───────────────────────────────────────────────────────────────────


def _run_augmentation(src: Image.Image, preset: str) -> Image.Image:
    """Augment *src* with the chosen preset; always return a PIL Image."""
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
    ]:
        if key not in st.session_state:
            st.session_state[key] = val


def _thumbnail_source(src: Image.Image, size: int = 512) -> Image.Image:
    """Return a resized copy of *src* suitable for catalogue preview."""
    img = src.copy().convert("RGB")
    img.thumbnail((size, size), Image.LANCZOS)
    return img


def _build_aug_objects(enabled_aug_names: list) -> list:
    """Instantiate augmentation objects from enabled catalogue names using stored slider state."""
    import augraphy.augmentations as aug_module

    aug_objects = []
    for aug_name in enabled_aug_names:
        entry = CATALOGUE[aug_name]
        stored_override = st.session_state.get(f"aug_params_{aug_name}", {})
        params = {**entry["default_params"], **stored_override}
        params["p"] = 1.0
        if aug_name in ("Brightness", "Dithering"):
            params["numba_jit"] = 0
        try:
            aug_cls = getattr(aug_module, aug_name)
            aug_objects.append(aug_cls(**params))
        except Exception as exc:
            st.warning(f"Skipping {aug_name}: {exc}")
    return aug_objects


@st.cache_data(show_spinner=False)
def _cached_apply_single(image_bytes: bytes, aug_name: str, params_key: str) -> bytes:
    """Apply a single augmentation and return PNG bytes. Keyed by image + aug + params."""
    import json

    params = json.loads(params_key)
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    result = apply_single(aug_name, img, params if params else None)
    buf = io.BytesIO()
    result.save(buf, format="PNG")
    return buf.getvalue()


_init_pdf_state()

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
            if st.session_state.get("aug_pdf_page_idx", 0) >= len(pages):
                st.session_state["aug_pdf_page_idx"] = 0
            state.set_uploaded_image(pages[st.session_state["aug_pdf_page_idx"]])
            state.set_aug_image(None)
            st.session_state["aug_catalogue_thumbnails"] = {}
        except ImportError:
            st.error(
                "PDF support requires PyMuPDF. "
                "Install with: `uv sync --extra synthesis --native-tls`"
            )
    else:
        st.session_state["aug_is_pdf"] = False
        st.session_state["aug_pdf_pages"] = []
        state.set_uploaded_image(uploaded_file_to_pil(uploaded))
        state.set_aug_image(None)
        st.session_state["aug_catalogue_thumbnails"] = {}

# ── Sample data ───────────────────────────────────────────────────────────────

_aug_samples = list_sample_files(
    "augmentation_lab", (".pdf", ".png", ".jpg", ".jpeg", ".bmp", ".tiff")
)
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
            state.set_uploaded_image(_aug_pages[0])
            state.set_aug_image(None)
            st.session_state["aug_catalogue_thumbnails"] = {}
            st.rerun()
        except ImportError as e:
            st.error(str(e))

# ── Page selector (PDF only) ───────────────────────────────────────────────────

is_pdf: bool = st.session_state.get("aug_is_pdf", False)
pdf_pages: list = st.session_state.get("aug_pdf_pages", [])

if is_pdf and len(pdf_pages) > 1:
    st.info(f"PDF has **{len(pdf_pages)} pages**. Select the page to augment.")
    new_idx = (
        st.slider("Page", min_value=1, max_value=len(pdf_pages), value=1, key="aug_page_slider")
        - 1
    )
    if new_idx != st.session_state.get("aug_pdf_page_idx", 0):
        st.session_state["aug_pdf_page_idx"] = new_idx
        state.set_uploaded_image(pdf_pages[new_idx])
        state.set_aug_image(None)
elif is_pdf and len(pdf_pages) == 1:
    st.info("Single-page PDF loaded.")

# ── Main tabs ─────────────────────────────────────────────────────────────────

tab_preset, tab_catalogue = st.tabs(["Preset", "Catalogue"])

# ════════════════════════════════════════════════════════════════════════════════
# TAB 1 — PRESET  (existing code, unchanged)
# ════════════════════════════════════════════════════════════════════════════════

with tab_preset:
    # ── Sidebar ───────────────────────────────────────────────────────────────
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

        run_btn = st.button("Augment", type="primary", key="aug_run_preset")

    # ── Run ───────────────────────────────────────────────────────────────────
    if run_btn:
        src = state.get_uploaded_image()
        if src is None:
            st.warning("Please upload a document first.")
        else:
            with st.spinner("Augmenting…"):
                aug = _run_augmentation(src, str(preset))
            state.set_aug_image(aug)

    # ── Display ───────────────────────────────────────────────────────────────
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

        # Download buttons
        dl_col1, dl_col2 = st.columns([1, 1])
        with dl_col1:
            st.download_button(
                "⬇ Download as PNG",
                data=image_to_bytes(aug),
                file_name="augmented.png",
                mime="image/png",
            )
        with dl_col2:
            if is_pdf:
                try:
                    dpi = st.session_state.get("aug_pdf_dpi", 150)
                    pdf_out = pil_to_pdf_bytes(aug, dpi=dpi)
                    st.download_button(
                        "⬇ Download as PDF",
                        data=pdf_out,
                        file_name="augmented.pdf",
                        mime="application/pdf",
                    )
                except ImportError:
                    st.caption("PDF download requires PyMuPDF.")

    elif orig is not None:
        page_label = ""
        if is_pdf and pdf_pages:
            idx = st.session_state.get("aug_pdf_page_idx", 0)
            page_label = f" (page {idx + 1}/{len(pdf_pages)})"
        st.image(orig, caption=f"Uploaded document{page_label}", use_container_width=True)
        st.info("Click **Augment** in the sidebar to apply augmentation.")


# ════════════════════════════════════════════════════════════════════════════════
# TAB 2 — CATALOGUE
# ════════════════════════════════════════════════════════════════════════════════

with tab_catalogue:
    src_image = state.get_uploaded_image()

    if src_image is None:
        st.info("Upload a document image above to use the catalogue.")
    else:
        # Use full-resolution source for all catalogue previews
        src_bytes = image_to_bytes(src_image)

        # Ensure catalogue thumbnails dict exists
        if "aug_catalogue_thumbnails" not in st.session_state:
            st.session_state["aug_catalogue_thumbnails"] = {}
        if "aug_catalogue_enabled" not in st.session_state:
            st.session_state["aug_catalogue_enabled"] = {}

        thumbnails: dict = st.session_state["aug_catalogue_thumbnails"]
        enabled_map: dict = st.session_state["aug_catalogue_enabled"]

        # ── Phase tabs ────────────────────────────────────────────────────────
        phase_tab_ink, phase_tab_paper, phase_tab_post = st.tabs(
            ["Ink Phase", "Paper Phase", "Post Phase"]
        )

        def _render_phase_cards(phase_tab, phase_name: str) -> None:
            """Render all augmentation cards for a given phase inside the given tab."""
            import json

            phase_augs = get_phase_augmentations(phase_name)
            aug_names = list(phase_augs.keys())

            with phase_tab:
                if not aug_names:
                    st.write("No augmentations in this phase.")
                    return

                # 4-column grid
                cols = st.columns(4)
                for i, aug_name in enumerate(aug_names):
                    entry = phase_augs[aug_name]
                    col = cols[i % 4]

                    with col:
                        with st.container(border=True):
                            st.markdown(f"**{entry['display_name']}**")
                            st.caption(entry["description"])

                            # Checkbox — controls pipeline inclusion only, not preview
                            is_enabled = st.checkbox(
                                "Include in pipeline",
                                value=bool(enabled_map.get(aug_name, False)),
                                key=f"aug_enabled_{aug_name}",
                            )
                            enabled_map[aug_name] = is_enabled
                            st.session_state["aug_catalogue_enabled"] = enabled_map

                            # Always show augmented preview for every card
                            params_override: dict = {}
                            with st.expander("Parameters"):
                                dp = entry["default_params"]
                                if aug_name == "InkBleed":
                                    low, high = st.slider("Intensity", 0.0, 1.0, (float(dp["intensity_range"][0]), float(dp["intensity_range"][1])), 0.05, key=f"aug_p_{aug_name}_intensity")
                                    params_override["intensity_range"] = (low, high)
                                elif aug_name == "BleedThrough":
                                    low, high = st.slider("Intensity", 0.01, 0.9, (float(dp.get("intensity_range", (0.1, 0.3))[0]), float(dp.get("intensity_range", (0.1, 0.3))[1])), 0.01, key=f"aug_p_{aug_name}_intensity")
                                    params_override["intensity_range"] = (low, high)
                                elif aug_name == "Markup":
                                    mtype = st.selectbox("Type", ["strikethrough", "crossed", "highlight", "underline"], index=["strikethrough", "crossed", "highlight", "underline"].index(dp.get("markup_type", "strikethrough")), key=f"aug_p_{aug_name}_type")
                                    params_override["markup_type"] = mtype
                                    n_low, n_high = st.slider("Lines", 1, 20, (int(dp.get("num_lines_range", (2, 4))[0]), int(dp.get("num_lines_range", (2, 4))[1])), 1, key=f"aug_p_{aug_name}_lines")
                                    params_override["num_lines_range"] = (n_low, n_high)
                                elif aug_name == "InkShifter":
                                    sc_low, sc_high = st.slider("Shift scale", 1, 100, (int(dp.get("text_shift_scale_range", (18, 27))[0]), int(dp.get("text_shift_scale_range", (18, 27))[1])), 1, key=f"aug_p_{aug_name}_scale")
                                    params_override["text_shift_scale_range"] = (sc_low, sc_high)
                                elif aug_name == "Letterpress":
                                    ns_low, ns_high = st.slider("Sample points", 50, 1000, (int(dp.get("n_samples", (100, 300))[0]), int(dp.get("n_samples", (100, 300))[1])), 10, key=f"aug_p_{aug_name}_samples")
                                    nc_low, nc_high = st.slider("Clusters", 100, 1000, (int(dp.get("n_clusters", (300, 500))[0]), int(dp.get("n_clusters", (300, 500))[1])), 10, key=f"aug_p_{aug_name}_clusters")
                                    params_override["n_samples"] = (ns_low, ns_high)
                                    params_override["n_clusters"] = (nc_low, nc_high)
                                elif aug_name == "ShadowCast":
                                    side = st.selectbox("Shadow side", ["left", "right", "top", "bottom"], index=["left", "right", "top", "bottom"].index(dp.get("shadow_side", "left")), key=f"aug_p_{aug_name}_side")
                                    op_low, op_high = st.slider("Opacity", 0.1, 1.0, (float(dp.get("shadow_opacity_range", (0.5, 0.8))[0]), float(dp.get("shadow_opacity_range", (0.5, 0.8))[1])), 0.05, key=f"aug_p_{aug_name}_opacity")
                                    params_override["shadow_side"] = side
                                    params_override["shadow_opacity_range"] = (op_low, op_high)
                                elif aug_name == "NoiseTexturize":
                                    s_low, s_high = st.slider("Sigma", 1.0, 20.0, (float(dp["sigma_range"][0]), float(dp["sigma_range"][1])), 1.0, key=f"aug_p_{aug_name}_sigma")
                                    t_low, t_high = st.slider("Turbulence", 1.0, 10.0, (float(dp.get("turbulence_range", (2, 5))[0]), float(dp.get("turbulence_range", (2, 5))[1])), 0.5, key=f"aug_p_{aug_name}_turbulence")
                                    params_override["sigma_range"] = (s_low, s_high)
                                    params_override["turbulence_range"] = (t_low, t_high)
                                elif aug_name == "ColorShift":
                                    offset_low, offset_high = st.slider("Offset (px)", 1, 50, (1, int(dp["color_shift_offset_x_range"][1])), 1, key=f"aug_p_{aug_name}_offset")
                                    iters_low, iters_high = st.slider("Iterations", 1, 8, (1, int(dp.get("color_shift_iterations", (2, 3))[1])), 1, key=f"aug_p_{aug_name}_iters")
                                    params_override["color_shift_offset_x_range"] = (offset_low, offset_high)
                                    params_override["color_shift_offset_y_range"] = (offset_low, offset_high)
                                    params_override["color_shift_iterations"] = (iters_low, iters_high)
                                elif aug_name == "DirtyDrum":
                                    w_low, w_high = st.slider("Line width", 1, 8, (int(dp.get("line_width_range", (1, 4))[0]), int(dp.get("line_width_range", (1, 4))[1])), 1, key=f"aug_p_{aug_name}_width")
                                    conc = st.slider("Concentration", 0.01, 0.5, float(dp.get("line_concentration", 0.1)), 0.01, key=f"aug_p_{aug_name}_conc")
                                    params_override["line_width_range"] = (w_low, w_high)
                                    params_override["line_concentration"] = conc
                                elif aug_name == "DirtyRollers":
                                    w_low, w_high = st.slider("Line width", 1, 12, (int(dp.get("line_width_range", (2, 6))[0]), int(dp.get("line_width_range", (2, 6))[1])), 1, key=f"aug_p_{aug_name}_width")
                                    params_override["line_width_range"] = (w_low, w_high)
                                elif aug_name == "SubtleNoise":
                                    rng = st.slider("Noise range", 1, 30, int(dp.get("subtle_range", 10)), 1, key=f"aug_p_{aug_name}_range")
                                    params_override["subtle_range"] = rng
                                elif aug_name == "WaterMark":
                                    word = st.text_input("Watermark text", value=dp.get("watermark_word", "DRAFT"), key=f"aug_p_{aug_name}_word")
                                    fsize_low, fsize_high = st.slider("Font size", 10, 300, (int(dp.get("watermark_font_size", (60, 100))[0]), int(dp.get("watermark_font_size", (60, 100))[1])), 5, key=f"aug_p_{aug_name}_fsize")
                                    rot_low, rot_high = st.slider("Rotation (°)", 0, 360, (int(dp.get("watermark_rotation", (30, 60))[0]), int(dp.get("watermark_rotation", (30, 60))[1])), 5, key=f"aug_p_{aug_name}_rot")
                                    params_override["watermark_word"] = word
                                    params_override["watermark_font_size"] = (fsize_low, fsize_high)
                                    params_override["watermark_rotation"] = (rot_low, rot_high)
                                    params_override["watermark_font_type"] = 0
                                elif aug_name == "Brightness":
                                    low, high = st.slider("Brightness", 0.3, 2.0, (float(dp["brightness_range"][0]), float(dp["brightness_range"][1])), 0.05, key=f"aug_p_{aug_name}_brightness")
                                    params_override["brightness_range"] = (low, high)
                                    params_override["numba_jit"] = 0
                                elif aug_name == "Gamma":
                                    low, high = st.slider("Gamma", 0.1, 4.0, (float(dp.get("gamma_range", (0.5, 2.0))[0]), float(dp.get("gamma_range", (0.5, 2.0))[1])), 0.1, key=f"aug_p_{aug_name}_gamma")
                                    params_override["gamma_range"] = (low, high)
                                elif aug_name == "Jpeg":
                                    low, high = st.slider("Quality", 10, 95, (int(dp["quality_range"][0]), int(dp["quality_range"][1])), 5, key=f"aug_p_{aug_name}_quality")
                                    params_override["quality_range"] = (low, high)
                                elif aug_name == "Dithering":
                                    params_override["numba_jit"] = 0
                                elif aug_name == "GlitchEffect":
                                    g_low, g_high = st.slider("Glitch count", 2, 50, (int(dp.get("glitch_number_range", (8, 16))[0]), int(dp.get("glitch_number_range", (8, 16))[1])), 1, key=f"aug_p_{aug_name}_count")
                                    s_low, s_high = st.slider("Glitch size", 2, 100, (int(dp.get("glitch_size_range", (5, 50))[0]), int(dp.get("glitch_size_range", (5, 50))[1])), 1, key=f"aug_p_{aug_name}_size")
                                    params_override["glitch_number_range"] = (g_low, g_high)
                                    params_override["glitch_size_range"] = (s_low, s_high)
                                elif aug_name == "Geometric":
                                    r_min, r_max = st.slider("Rotation (°)", -45, 45, (int(dp.get("rotate_range", (-10, 10))[0]), int(dp.get("rotate_range", (-10, 10))[1])), 1, key=f"aug_p_{aug_name}_rotate")
                                    params_override["rotate_range"] = (r_min, r_max)
                                elif aug_name == "Folding":
                                    fc = st.slider("Fold count", 1, 4, int(dp.get("fold_count", 1)), 1, key=f"aug_p_{aug_name}_fc")
                                    params_override["fold_count"] = fc
                                elif aug_name == "BookBinding":
                                    cdir = st.selectbox("Curling direction", ["random", "up", "down"], index=0, key=f"aug_p_{aug_name}_cdir")
                                    params_override["curling_direction"] = cdir
                                # ── New ink-phase augmentations ─────────────
                                elif aug_name == "InkMottling":
                                    a_low, a_high = st.slider("Alpha", 0.05, 1.0, (float(dp.get("ink_mottling_alpha_range", (0.2, 0.3))[0]), float(dp.get("ink_mottling_alpha_range", (0.2, 0.3))[1])), 0.05, key=f"aug_p_{aug_name}_alpha")
                                    params_override["ink_mottling_alpha_range"] = (a_low, a_high)
                                elif aug_name == "LowInkPeriodicLines":
                                    c_low, c_high = st.slider("Count", 1, 20, (int(dp.get("count_range", (2, 5))[0]), int(dp.get("count_range", (2, 5))[1])), 1, key=f"aug_p_{aug_name}_count")
                                    per_low, per_high = st.slider("Period (px)", 5, 100, (int(dp.get("period_range", (10, 30))[0]), int(dp.get("period_range", (10, 30))[1])), 5, key=f"aug_p_{aug_name}_period")
                                    params_override["count_range"] = (c_low, c_high)
                                    params_override["period_range"] = (per_low, per_high)
                                elif aug_name == "LowInkRandomLines":
                                    c_low, c_high = st.slider("Count", 1, 30, (int(dp.get("count_range", (5, 10))[0]), int(dp.get("count_range", (5, 10))[1])), 1, key=f"aug_p_{aug_name}_count")
                                    params_override["count_range"] = (c_low, c_high)
                                elif aug_name == "Hollow":
                                    k_low, k_high = st.slider("Median kernel", 11, 201, (int(dp.get("hollow_median_kernel_value_range", (71, 101))[0]), int(dp.get("hollow_median_kernel_value_range", (71, 101))[1])), 10, key=f"aug_p_{aug_name}_kernel")
                                    params_override["hollow_median_kernel_value_range"] = (k_low, k_high)
                                elif aug_name == "Scribbles":
                                    s_type = st.selectbox("Scribble type", ["random", "lines", "circles", "text"], index=0, key=f"aug_p_{aug_name}_type")
                                    t_low, t_high = st.slider("Thickness", 1, 10, (int(dp.get("scribbles_thickness_range", (1, 3))[0]), int(dp.get("scribbles_thickness_range", (1, 3))[1])), 1, key=f"aug_p_{aug_name}_thickness")
                                    params_override["scribbles_type"] = s_type
                                    params_override["scribbles_thickness_range"] = (t_low, t_high)
                                elif aug_name == "LinesDegradation":
                                    g_low, g_high = st.slider("Gradient", 0, 255, (int(dp.get("line_gradient_range", (32, 255))[0]), int(dp.get("line_gradient_range", (32, 255))[1])), 8, key=f"aug_p_{aug_name}_gradient")
                                    params_override["line_gradient_range"] = (g_low, g_high)
                                elif aug_name == "BindingsAndFasteners":
                                    effect = st.selectbox("Effect type", ["random", "punch_holes", "binding_holes", "staple", "clip"], index=0, key=f"aug_p_{aug_name}_effect")
                                    params_override["effect_type"] = effect
                                    params_override["use_figshare_library"] = 0
                                # ── New paper-phase augmentations ────────────
                                elif aug_name == "BrightnessTexturize":
                                    t_low, t_high = st.slider("Texturize range", 0.5, 1.0, (float(dp.get("texturize_range", (0.8, 0.99))[0]), float(dp.get("texturize_range", (0.8, 0.99))[1])), 0.01, key=f"aug_p_{aug_name}_texturize")
                                    dev = st.slider("Deviation", 0.01, 0.3, float(dp.get("deviation", 0.08)), 0.01, key=f"aug_p_{aug_name}_dev")
                                    params_override["texturize_range"] = (t_low, t_high)
                                    params_override["deviation"] = dev
                                elif aug_name == "ColorPaper":
                                    h_low, h_high = st.slider("Hue", 0, 179, (int(dp.get("hue_range", (28, 45))[0]), int(dp.get("hue_range", (28, 45))[1])), 1, key=f"aug_p_{aug_name}_hue")
                                    s_low, s_high = st.slider("Saturation", 0, 100, (int(dp.get("saturation_range", (10, 40))[0]), int(dp.get("saturation_range", (10, 40))[1])), 5, key=f"aug_p_{aug_name}_sat")
                                    params_override["hue_range"] = (h_low, h_high)
                                    params_override["saturation_range"] = (s_low, s_high)
                                elif aug_name == "PaperFactory":
                                    enable_color = st.checkbox("Enable texture colour", value=bool(dp.get("texture_enable_color", 0)), key=f"aug_p_{aug_name}_color")
                                    blend_method = st.selectbox("Blend method", ["overlay", "normal", "multiply"], index=0, key=f"aug_p_{aug_name}_blend")
                                    params_override["texture_enable_color"] = int(enable_color)
                                    params_override["texture_color_blend_method"] = blend_method
                                    params_override["generate_texture"] = 1
                                elif aug_name == "DirtyScreen":
                                    nc_low, nc_high = st.slider("Clusters", 10, 200, (int(dp.get("n_clusters", (50, 100))[0]), int(dp.get("n_clusters", (50, 100))[1])), 10, key=f"aug_p_{aug_name}_clusters")
                                    params_override["n_clusters"] = (nc_low, nc_high)
                                elif aug_name == "Stains":
                                    s_type = st.selectbox("Stain type", ["random", "watermark", "light_stain", "dark_stain"], index=0, key=f"aug_p_{aug_name}_type")
                                    blend = st.selectbox("Blend method", ["darken", "normal", "overlay"], index=0, key=f"aug_p_{aug_name}_blend")
                                    alpha = st.slider("Blend alpha", 0.1, 1.0, float(dp.get("stains_blend_alpha", 0.5)), 0.05, key=f"aug_p_{aug_name}_alpha")
                                    params_override["stains_type"] = s_type
                                    params_override["stains_blend_method"] = blend
                                    params_override["stains_blend_alpha"] = alpha
                                elif aug_name == "NoisyLines":
                                    n_low, n_high = st.slider("Lines", 1, 50, (int(dp.get("noisy_lines_number_range", (5, 20))[0]), int(dp.get("noisy_lines_number_range", (5, 20))[1])), 1, key=f"aug_p_{aug_name}_lines")
                                    params_override["noisy_lines_number_range"] = (n_low, n_high)
                                elif aug_name == "PatternGenerator":
                                    a_low, a_high = st.slider("Alpha", 0.05, 1.0, (float(dp.get("alpha_range", (0.25, 0.5))[0]), float(dp.get("alpha_range", (0.25, 0.5))[1])), 0.05, key=f"aug_p_{aug_name}_alpha")
                                    params_override["alpha_range"] = (a_low, a_high)
                                    params_override["numba_jit"] = 0
                                elif aug_name == "DelaunayTessellation":
                                    np_low, np_high = st.slider("Points", 100, 1000, (int(dp.get("n_points_range", (500, 800))[0]), int(dp.get("n_points_range", (500, 800))[1])), 50, key=f"aug_p_{aug_name}_points")
                                    params_override["n_points_range"] = (np_low, np_high)
                                    params_override["n_horizontal_points_range"] = (np_low, np_high)
                                    params_override["n_vertical_points_range"] = (np_low, np_high)
                                elif aug_name == "VoronoiTessellation":
                                    m_low, m_high = st.slider("Multiplier", 10, 150, (int(dp.get("mult_range", (50, 80))[0]), int(dp.get("mult_range", (50, 80))[1])), 5, key=f"aug_p_{aug_name}_mult")
                                    params_override["mult_range"] = (m_low, m_high)
                                    params_override["numba_jit"] = 0
                                elif aug_name == "PageBorder":
                                    rot_low, rot_high = st.slider("Rotation (°)", -10, 10, (int(dp.get("page_rotation_angle_range", (-3, 3))[0]), int(dp.get("page_rotation_angle_range", (-3, 3))[1])), 1, key=f"aug_p_{aug_name}_rot")
                                    params_override["page_rotation_angle_range"] = (rot_low, rot_high)
                                    params_override["numba_jit"] = 0
                                # ── New post-phase augmentations ─────────────
                                elif aug_name == "DepthSimulatedBlur":
                                    maj_low, maj_high = st.slider("Major axis length", 50, 300, (int(dp.get("blur_major_axes_length_range", (120, 200))[0]), int(dp.get("blur_major_axes_length_range", (120, 200))[1])), 10, key=f"aug_p_{aug_name}_maj")
                                    it_low, it_high = st.slider("Iterations", 2, 20, (int(dp.get("blur_iteration_range", (8, 10))[0]), int(dp.get("blur_iteration_range", (8, 10))[1])), 1, key=f"aug_p_{aug_name}_iters")
                                    params_override["blur_major_axes_length_range"] = (maj_low, maj_high)
                                    params_override["blur_minor_axes_length_range"] = (maj_low, maj_high)
                                    params_override["blur_iteration_range"] = (it_low, it_high)
                                elif aug_name == "DoubleExposure":
                                    off_low, off_high = st.slider("Offset (px)", 5, 50, (int(dp.get("offset_range", (18, 25))[0]), int(dp.get("offset_range", (18, 25))[1])), 1, key=f"aug_p_{aug_name}_offset")
                                    params_override["offset_range"] = (off_low, off_high)
                                elif aug_name == "Faxify":
                                    s_low, s_high = st.slider("Scale", 0.5, 2.0, (float(dp.get("scale_range", (1.0, 1.25))[0]), float(dp.get("scale_range", (1.0, 1.25))[1])), 0.05, key=f"aug_p_{aug_name}_scale")
                                    params_override["scale_range"] = (s_low, s_high)
                                    params_override["numba_jit"] = 0
                                elif aug_name == "LCDScreenPattern":
                                    ptype = st.selectbox("Pattern type", ["random", "horizontal_lines", "vertical_lines", "dots"], index=0, key=f"aug_p_{aug_name}_type")
                                    alpha = st.slider("Overlay alpha", 0.05, 0.8, float(dp.get("pattern_overlay_alpha", 0.3)), 0.05, key=f"aug_p_{aug_name}_alpha")
                                    params_override["pattern_type"] = ptype
                                    params_override["pattern_overlay_alpha"] = alpha
                                elif aug_name == "LensFlare":
                                    params_override["numba_jit"] = 0
                                elif aug_name == "LightingGradient":
                                    mode = st.selectbox("Mode", ["gaussian", "linear"], index=0, key=f"aug_p_{aug_name}_mode")
                                    b_low, b_high = st.slider("Brightness range", 0, 255, (int(dp.get("min_brightness", 0)), int(dp.get("max_brightness", 255))), 5, key=f"aug_p_{aug_name}_brightness")
                                    params_override["mode"] = mode
                                    params_override["min_brightness"] = b_low
                                    params_override["max_brightness"] = b_high
                                    params_override["numba_jit"] = 0
                                elif aug_name == "Moire":
                                    d_low, d_high = st.slider("Density", 5, 50, (int(dp.get("moire_density", (15, 20))[0]), int(dp.get("moire_density", (15, 20))[1])), 1, key=f"aug_p_{aug_name}_density")
                                    blend_alpha = st.slider("Blend alpha", 0.01, 0.5, float(dp.get("moire_blend_alpha", 0.1)), 0.01, key=f"aug_p_{aug_name}_alpha")
                                    params_override["moire_density"] = (d_low, d_high)
                                    params_override["moire_blend_alpha"] = blend_alpha
                                    params_override["numba_jit"] = 0
                                elif aug_name == "ReflectedLight":
                                    smooth = st.slider("Smoothness", 0.1, 1.0, float(dp.get("reflected_light_smoothness", 0.8)), 0.05, key=f"aug_p_{aug_name}_smooth")
                                    params_override["reflected_light_smoothness"] = smooth
                                elif aug_name == "DotMatrix":
                                    dw_low, dw_high = st.slider("Dot size", 1, 40, (int(dp.get("dot_matrix_dot_width_range", (3, 19))[0]), int(dp.get("dot_matrix_dot_width_range", (3, 19))[1])), 1, key=f"aug_p_{aug_name}_dotsize")
                                    params_override["dot_matrix_dot_width_range"] = (dw_low, dw_high)
                                    params_override["dot_matrix_dot_height_range"] = (dw_low, dw_high)
                                    params_override["numba_jit"] = 0
                                elif aug_name == "Rescale":
                                    dpi = st.slider("Target DPI", 72, 600, int(dp.get("target_dpi", 300)), 12, key=f"aug_p_{aug_name}_dpi")
                                    params_override["target_dpi"] = dpi
                                elif aug_name == "SectionShift":
                                    n_low, n_high = st.slider("Sections", 2, 15, (int(dp.get("section_shift_number_range", (3, 5))[0]), int(dp.get("section_shift_number_range", (3, 5))[1])), 1, key=f"aug_p_{aug_name}_sections")
                                    x_low, x_high = st.slider("X shift (px)", -30, 30, (int(dp.get("section_shift_x_range", (-10, 10))[0]), int(dp.get("section_shift_x_range", (-10, 10))[1])), 1, key=f"aug_p_{aug_name}_xshift")
                                    params_override["section_shift_number_range"] = (n_low, n_high)
                                    params_override["section_shift_x_range"] = (x_low, x_high)
                                elif aug_name == "Squish":
                                    direc = st.selectbox("Direction", ["random", "horizontal", "vertical"], index=0, key=f"aug_p_{aug_name}_dir")
                                    sq_low, sq_high = st.slider("Distance (px)", 1, 20, (int(dp.get("squish_distance_range", (5, 7))[0]), int(dp.get("squish_distance_range", (5, 7))[1])), 1, key=f"aug_p_{aug_name}_distance")
                                    params_override["squish_direction"] = direc
                                    params_override["squish_distance_range"] = (sq_low, sq_high)
                                else:
                                    p_val = st.slider("Probability", 0.0, 1.0, float(dp.get("p", 0.9)), 0.05, key=f"aug_p_{aug_name}_p")
                                    params_override["p"] = p_val

                            # Persist slider values so Generate button picks them up
                            st.session_state[f"aug_params_{aug_name}"] = params_override

                            # Build effective params for caching key (p=1.0 to always show effect)
                            effective = {**entry["default_params"], **params_override}
                            effective["p"] = 1.0
                            params_key = json.dumps(effective, sort_keys=True, default=str)

                            # Generate / retrieve cached preview at full resolution
                            # Skip apply_single for slow entries to avoid long waits or crashes
                            cache_key = f"{aug_name}::{params_key}"
                            if entry.get("slow", False):
                                preview_bytes = src_bytes
                            elif cache_key not in thumbnails:
                                try:
                                    preview_bytes = _cached_apply_single(
                                        src_bytes, aug_name, params_key
                                    )
                                    thumbnails[cache_key] = preview_bytes
                                    st.session_state["aug_catalogue_thumbnails"] = thumbnails
                                except Exception as exc:
                                    st.warning(f"Preview failed: {exc}")
                                    preview_bytes = src_bytes
                            else:
                                preview_bytes = thumbnails[cache_key]

                            st.image(
                                Image.open(io.BytesIO(preview_bytes)),
                                use_container_width=True,
                                caption=entry["display_name"],
                            )

        _render_phase_cards(phase_tab_ink, "ink")
        _render_phase_cards(phase_tab_paper, "paper")
        _render_phase_cards(phase_tab_post, "post")

        # ── Generate button ───────────────────────────────────────────────────
        st.divider()

        enabled_aug_names = [
            name for name, en in enabled_map.items() if en
        ]

        if enabled_aug_names:
            st.markdown(
                f"**Selected augmentations ({len(enabled_aug_names)}):** "
                + ", ".join(enabled_aug_names)
            )
        else:
            st.caption("Enable augmentations above to compose a custom pipeline.")

        gen_btn = st.button(
            "Generate (catalogue)",
            type="primary",
            key="aug_run_catalogue",
            disabled=len(enabled_aug_names) == 0,
        )

        if gen_btn:
            if src_image is None:
                st.warning("Please upload a document first.")
            elif not enabled_aug_names:
                st.warning("Enable at least one augmentation.")
            else:
                aug_objects = _build_aug_objects(enabled_aug_names)
                if aug_objects:
                    with st.spinner("Generating with custom catalogue pipeline…"):
                        try:
                            augmenter = DocumentAugmenter(custom_augmentations=aug_objects)
                            cat_result = augmenter.augment(src_image)
                            if not isinstance(cat_result, Image.Image):
                                cat_result = Image.fromarray(np.array(cat_result))
                            st.session_state["aug_catalogue_result"] = cat_result
                        except Exception as exc:
                            st.error(f"Augmentation failed: {exc}")

        cat_result = st.session_state.get("aug_catalogue_result")
        if cat_result is not None:
            show_side_by_side(
                src_image,
                cat_result,
                labels=("Original", "Catalogue result"),
            )
            st.download_button(
                "⬇ Download catalogue result as PNG",
                data=image_to_bytes(cat_result),
                file_name="catalogue_augmented.png",
                mime="image/png",
                key="aug_cat_dl",
            )

        # ── Batch Run ─────────────────────────────────────────────────────────
        st.divider()
        with st.expander(
            "Batch Run with this pipeline"
            + (f" ({len(enabled_aug_names)} augmentation(s))" if enabled_aug_names else ""),
            expanded=False,
        ):
            if not enabled_aug_names:
                st.info("Enable at least one augmentation above to use batch run.")
            else:
                st.caption(
                    "Upload N input documents (images or PDFs). The catalogue pipeline above "
                    "is applied to produce M augmented outputs, sampling randomly from your inputs."
                )

                batch_uploads = st.file_uploader(
                    "Input templates (images or PDFs)",
                    type=["png", "jpg", "jpeg", "bmp", "tiff", "pdf"],
                    accept_multiple_files=True,
                    key="aug_cat_batch_uploads",
                )

                if batch_uploads:
                    batch_images = []
                    for f in batch_uploads:
                        if f.name.lower().endswith(".pdf"):
                            try:
                                pages = uploaded_pdf_to_pil_pages(f, dpi=150)
                                batch_images.extend(pages)
                            except ImportError:
                                st.warning(
                                    f"PDF support requires PyMuPDF. "
                                    "Install with: `uv sync --extra synthesis --native-tls`"
                                )
                        else:
                            batch_images.append(uploaded_file_to_pil(f))
                    st.caption(f"{len(batch_images)} template page(s) loaded from {len(batch_uploads)} file(s).")

                    total = st.number_input(
                        "How many outputs (M) do you want generated?",
                        min_value=1, max_value=1000, value=20,
                        key="aug_cat_batch_total",
                    )
                    eff_mode = "random_sample"
                    eff_copies = 1
                    eff_total = int(total)
                    st.caption(
                        f"→ {eff_total} output(s) sampled randomly from "
                        f"{len(batch_images)} template page(s)"
                    )

                    seed_raw = st.number_input(
                        "Random seed (0 = unseeded)",
                        min_value=0, value=0,
                        key="aug_cat_batch_seed",
                    )
                    eff_seed = int(seed_raw) if seed_raw > 0 else None

                    if eff_total > 50:
                        st.warning(
                            f"Generating {eff_total} images may take a while. "
                            "Consider starting with a smaller number."
                        )

                    if st.button(
                        f"Run Batch ({eff_total} outputs)",
                        type="primary",
                        key="aug_cat_batch_run",
                    ):
                        aug_objects = _build_aug_objects(enabled_aug_names)
                        if aug_objects:
                            from document_simulator.augmentation.batch import BatchAugmenter

                            augmenter = DocumentAugmenter(custom_augmentations=aug_objects)
                            ba = BatchAugmenter(augmenter=augmenter, num_workers=1)
                            t0 = time.time()
                            with st.spinner(f"Generating {eff_total} outputs…"):
                                results = ba.augment_multi_template(
                                    sources=batch_images,
                                    mode=eff_mode,
                                    copies_per_template=eff_copies,
                                    total_outputs=eff_total,
                                    seed=eff_seed,
                                    parallel=False,
                                )
                            elapsed = time.time() - t0
                            st.session_state["aug_cat_batch_results"] = results
                            st.session_state["aug_cat_batch_elapsed"] = elapsed

                    batch_results: list = st.session_state.get("aug_cat_batch_results", [])
                    if batch_results:
                        elapsed = st.session_state.get("aug_cat_batch_elapsed", 0.0)
                        st.success(
                            f"Generated {len(batch_results)} outputs in {elapsed:.1f}s"
                        )
                        st.metric("Outputs generated", len(batch_results))

                        # Thumbnail preview — up to 8
                        preview = batch_results[:8]
                        grid_cols = st.columns(min(4, len(preview)))
                        for i, (aug_img, stem) in enumerate(preview):
                            with grid_cols[i % 4]:
                                st.image(aug_img, caption=stem, use_container_width=True)
                        if len(batch_results) > 8:
                            st.caption(
                                f"Showing 8 of {len(batch_results)}. "
                                "Download ZIP for all outputs."
                            )

                        # Build and offer ZIP download
                        zip_buf = io.BytesIO()
                        with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
                            stem_counts: dict = {}
                            for aug_img, stem in batch_results:
                                count = stem_counts.get(stem, 0)
                                stem_counts[stem] = count + 1
                                fname = f"{stem}_{count:03d}.png"
                                img_buf = io.BytesIO()
                                aug_img.save(img_buf, format="PNG")
                                zf.writestr(fname, img_buf.getvalue())
                        zip_buf.seek(0)
                        st.download_button(
                            "⬇ Download all as ZIP",
                            data=zip_buf.getvalue(),
                            file_name="batch_catalogue.zip",
                            mime="application/zip",
                            key="aug_cat_batch_dl",
                        )
