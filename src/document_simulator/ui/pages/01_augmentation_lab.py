"""Augmentation Lab — upload a document image or PDF, pick a preset or catalogue mode."""

import io

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


def _thumbnail_source(src: Image.Image, size: int = 256) -> Image.Image:
    """Return a resized copy of *src* suitable for catalogue preview."""
    img = src.copy().convert("RGB")
    img.thumbnail((size, size), Image.LANCZOS)
    return img


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
        # Prepare thumbnail source (256x256)
        thumb_src = _thumbnail_source(src_image)
        thumb_src_bytes = image_to_bytes(thumb_src)

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

                            # Checkbox
                            is_enabled = st.checkbox(
                                "Enable",
                                value=bool(enabled_map.get(aug_name, False)),
                                key=f"aug_enabled_{aug_name}",
                            )
                            # Sync enabled state back
                            enabled_map[aug_name] = is_enabled
                            st.session_state["aug_catalogue_enabled"] = enabled_map

                            if entry.get("slow", False) and is_enabled:
                                st.info("Preview skipped (slow aug). Will run on Generate.")
                                st.image(thumb_src, use_container_width=True)
                            elif is_enabled:
                                # Collect params from sliders
                                params_override: dict = {}
                                with st.expander("Parameters"):
                                    # Per-augmentation sliders
                                    if aug_name == "InkBleed":
                                        low = st.slider(
                                            "Intensity min",
                                            0.0, 1.0,
                                            float(entry["default_params"]["intensity_range"][0]),
                                            0.05,
                                            key=f"aug_p_{aug_name}_int_low",
                                        )
                                        high = st.slider(
                                            "Intensity max",
                                            0.0, 1.0,
                                            float(entry["default_params"]["intensity_range"][1]),
                                            0.05,
                                            key=f"aug_p_{aug_name}_int_high",
                                        )
                                        params_override["intensity_range"] = (low, high)
                                    elif aug_name == "NoiseTexturize":
                                        low = st.slider(
                                            "Sigma min",
                                            1.0, 20.0,
                                            float(entry["default_params"]["sigma_range"][0]),
                                            1.0,
                                            key=f"aug_p_{aug_name}_sig_low",
                                        )
                                        high = st.slider(
                                            "Sigma max",
                                            1.0, 20.0,
                                            float(entry["default_params"]["sigma_range"][1]),
                                            1.0,
                                            key=f"aug_p_{aug_name}_sig_high",
                                        )
                                        params_override["sigma_range"] = (low, high)
                                    elif aug_name == "ColorShift":
                                        offset = st.slider(
                                            "Offset range max",
                                            1, 50,
                                            int(
                                                entry["default_params"][
                                                    "color_shift_offset_x_range"
                                                ][1]
                                            ),
                                            1,
                                            key=f"aug_p_{aug_name}_offset",
                                        )
                                        params_override["color_shift_offset_x_range"] = (
                                            1,
                                            offset,
                                        )
                                        params_override["color_shift_offset_y_range"] = (
                                            1,
                                            offset,
                                        )
                                    elif aug_name == "Brightness":
                                        low = st.slider(
                                            "Brightness min",
                                            0.3, 1.0,
                                            float(
                                                entry["default_params"]["brightness_range"][0]
                                            ),
                                            0.05,
                                            key=f"aug_p_{aug_name}_b_low",
                                        )
                                        high = st.slider(
                                            "Brightness max",
                                            1.0, 2.0,
                                            float(
                                                entry["default_params"]["brightness_range"][1]
                                            ),
                                            0.05,
                                            key=f"aug_p_{aug_name}_b_high",
                                        )
                                        params_override["brightness_range"] = (low, high)
                                        params_override["numba_jit"] = 0  # avoid JIT cold start
                                    elif aug_name == "Jpeg":
                                        low = st.slider(
                                            "Quality min",
                                            10, 95,
                                            int(entry["default_params"]["quality_range"][0]),
                                            5,
                                            key=f"aug_p_{aug_name}_q_low",
                                        )
                                        high = st.slider(
                                            "Quality max",
                                            10, 95,
                                            int(entry["default_params"]["quality_range"][1]),
                                            5,
                                            key=f"aug_p_{aug_name}_q_high",
                                        )
                                        params_override["quality_range"] = (low, high)
                                    elif aug_name == "Dithering":
                                        params_override["numba_jit"] = 0
                                        p_val = st.slider(
                                            "Probability",
                                            0.0, 1.0,
                                            float(entry["default_params"]["p"]),
                                            0.05,
                                            key=f"aug_p_{aug_name}_p",
                                        )
                                        params_override["p"] = p_val
                                    else:
                                        p_val = st.slider(
                                            "Probability",
                                            0.0, 1.0,
                                            float(entry["default_params"].get("p", 0.9)),
                                            0.05,
                                            key=f"aug_p_{aug_name}_p",
                                        )
                                        params_override["p"] = p_val

                                # Build effective params for caching key
                                effective = {**entry["default_params"], **params_override}
                                # Ensure p=1.0 for thumbnail (always show effect)
                                effective["p"] = 1.0
                                params_key = json.dumps(effective, sort_keys=True, default=str)

                                # Generate / retrieve cached thumbnail
                                cache_key = f"{aug_name}::{params_key}"
                                if cache_key not in thumbnails:
                                    try:
                                        thumb_bytes = _cached_apply_single(
                                            thumb_src_bytes, aug_name, params_key
                                        )
                                        thumbnails[cache_key] = thumb_bytes
                                        st.session_state["aug_catalogue_thumbnails"] = thumbnails
                                    except Exception as exc:
                                        st.warning(f"Preview failed: {exc}")
                                        thumb_bytes = thumb_src_bytes
                                else:
                                    thumb_bytes = thumbnails[cache_key]

                                st.image(
                                    Image.open(io.BytesIO(thumb_bytes)),
                                    use_container_width=True,
                                    caption=f"{entry['display_name']} preview",
                                )
                            else:
                                # Disabled — show original thumbnail
                                st.image(
                                    thumb_src,
                                    use_container_width=True,
                                    caption="disabled",
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
                import augraphy.augmentations as aug_module

                aug_objects = []
                for aug_name in enabled_aug_names:
                    entry = CATALOGUE[aug_name]
                    # Build params: use slider values stored in session state keys
                    params = dict(entry["default_params"])
                    # Force p=1.0 for the final run
                    params["p"] = 1.0
                    # Apply numba_jit=0 for applicable augs
                    if aug_name in ("Brightness", "Dithering"):
                        params["numba_jit"] = 0
                    try:
                        aug_cls = getattr(aug_module, aug_name)
                        aug_objects.append(aug_cls(**params))
                    except Exception as exc:
                        st.warning(f"Skipping {aug_name}: {exc}")

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
