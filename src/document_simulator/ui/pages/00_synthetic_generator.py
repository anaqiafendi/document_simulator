"""Synthetic Document Generator — Streamlit UI page.

4-tab wizard:
  Tab 1 — Template (blank or upload)
  Tab 2 — Respondents & Field Types
  Tab 3 — Zones (click-to-place with streamlit-image-coordinates)
  Tab 4 — Preview & Generate
"""

from __future__ import annotations

import hashlib
import io
import json
import zipfile
from pathlib import Path

import pandas as pd
import streamlit as st
from PIL import Image

from document_simulator.ui.pages.synthetic_generator_helpers import (
    _dataframe_to_zones,
    _stable_zones_hash,
    _zones_to_dataframe,
)

from document_simulator.synthesis.generator import SyntheticDocumentGenerator
from document_simulator.ui.components.file_uploader import list_sample_files, load_path_as_pil_pages
from document_simulator.synthesis.zones import (
    FieldTypeConfig,
    GeneratorConfig,
    RespondentConfig,
    SynthesisConfig,
    ZoneConfig,
)
from document_simulator.ui.components.image_display import image_to_bytes

# ---------------------------------------------------------------------------
# Optional canvas component
# ---------------------------------------------------------------------------
try:
    from streamlit_drawable_canvas import st_canvas

    _CANVAS_AVAILABLE = True
except ImportError:
    _CANVAS_AVAILABLE = False

# ---------------------------------------------------------------------------
# Optional click-to-place coordinates component
# ---------------------------------------------------------------------------
try:
    from streamlit_image_coordinates import streamlit_image_coordinates

    _COORDS_AVAILABLE = True
except ImportError:
    _COORDS_AVAILABLE = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_INK_PRESETS: list[tuple[str, str]] = [
    ("Black", "#000000"),
    ("Blue ink", "#0000CC"),
    ("Dark blue", "#00008B"),
    ("Red stamp", "#CC0000"),
    ("Pencil grey", "#888888"),
]

_FILL_STYLES = ["typed", "form-fill", "handwritten-font", "stamp"]
_FONT_FAMILIES = ["sans-serif", "serif", "monospace", "handwriting"]
_FAKER_PROVIDERS = [
    "name",
    "first_name",
    "last_name",
    "full_name",
    "initials",
    "address",
    "date",
    "phone_number",
    "ssn",
    "pricetag",
    "company",
    "custom",
]

_DEFAULT_FIELD_TYPE = {
    "field_type_id": "standard",
    "display_name": "Standard text",
    "font_family": "sans-serif",
    "font_size_range": [10, 14],
    "font_color": "#000000",
    "bold": False,
    "italic": False,
    "fill_style": "typed",
    "jitter_x": 0.05,
    "jitter_y": 0.02,
    "baseline_wander": 0.0,
    "char_spacing_jitter": 0.0,
}

_DISPLAY_W = 700  # max display width for template image in zone tab

# Distinct colours assigned to respondents in order of creation
_RESPONDENT_PALETTE = [
    "#2196F3",  # blue
    "#4CAF50",  # green
    "#FF9800",  # orange
    "#9C27B0",  # purple
    "#F44336",  # red
    "#00BCD4",  # cyan
    "#FF5722",  # deep-orange
    "#607D8B",  # blue-grey
]


# ---------------------------------------------------------------------------
# Session state helpers
# ---------------------------------------------------------------------------


def _init_state() -> None:
    defaults: dict = {
        "synthesis_respondents": [
            {
                "respondent_id": "person_1",
                "display_name": "Person 1",
                "field_types": [dict(_DEFAULT_FIELD_TYPE)],
            }
        ],
        "synthesis_zones": [],
        "synthesis_template_image": None,
        "synthesis_template_pdf_bytes": None,  # original PDF bytes for write-back
        "preview_samples": [],
        "preview_sample_pdfs": [],  # parallel list of PDF bytes (or None)
        "show_zone_overlays": False,
        "zone_first_click": None,
        "zone_click_counter": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _build_synthesis_config() -> SynthesisConfig:
    respondents = [
        RespondentConfig(
            respondent_id=r["respondent_id"],
            display_name=r["display_name"],
            field_types=[FieldTypeConfig(**ft) for ft in r["field_types"]],
        )
        for r in st.session_state["synthesis_respondents"]
    ]
    zones = [
        ZoneConfig(
            zone_id=z["zone_id"],
            label=z["label"],
            box=z["box"],
            respondent_id=z["respondent_id"],
            field_type_id=z["field_type_id"],
            faker_provider=z["faker_provider"],
            custom_values=z.get("custom_values", []),
            alignment=z.get("alignment", "left"),
        )
        for z in st.session_state["synthesis_zones"]
    ]
    return SynthesisConfig(respondents=respondents, zones=zones)


# ---------------------------------------------------------------------------
# Tab 1 — Template
# ---------------------------------------------------------------------------


def _tab_template() -> None:
    st.markdown("### Choose your template")

    # Build dropdown options: Blank page first, then any sample files
    _tmpl_samples = list_sample_files(
        "synthetic_generator", (".pdf", ".png", ".jpg", ".jpeg")
    )
    _tmpl_options = ["Blank page"] + [p.name for p in _tmpl_samples]
    selected_template = st.selectbox(
        "Template",
        options=_tmpl_options,
        index=0,
        key="template_select",
    )

    # Blank page size controls — only shown when Blank page is selected
    blank_w = 794
    blank_h = 1123
    if selected_template == "Blank page":
        _bw_col, _bh_col = st.columns(2)
        blank_w = _bw_col.number_input("Width (px)", value=794, min_value=100, key="blank_w")
        blank_h = _bh_col.number_input("Height (px)", value=1123, min_value=100, key="blank_h")

    st.markdown("**Or upload your own template**")
    uploaded = st.file_uploader(
        "PDF or image (PNG/JPG)",
        type=["png", "jpg", "jpeg", "pdf"],
        key="template_upload",
    )

    # Resolve template image — priority: file upload > sample dropdown > blank
    if uploaded is not None:
        if uploaded.name.lower().endswith(".pdf"):
            try:
                import fitz

                data = uploaded.read()
                st.session_state["synthesis_template_pdf_bytes"] = data
                doc = fitz.open(stream=data, filetype="pdf")
                page = doc[0]
                mat = fitz.Matrix(150 / 72, 150 / 72)
                pix = page.get_pixmap(matrix=mat)
                img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            except ImportError:
                st.warning("PyMuPDF not installed. Install with: uv sync --extra synthesis")
                img = Image.new("RGB", (int(blank_w), int(blank_h)), (255, 255, 255))
                st.session_state["synthesis_template_pdf_bytes"] = None
        else:
            img = Image.open(io.BytesIO(uploaded.read())).convert("RGB")
            st.session_state["synthesis_template_pdf_bytes"] = None
        st.session_state["synthesis_template_image"] = img

    elif selected_template != "Blank page":
        # Load from samples directory
        _tmpl_path = _tmpl_samples[_tmpl_options.index(selected_template) - 1]
        try:
            _tmpl_pages = load_path_as_pil_pages(_tmpl_path)
            img = _tmpl_pages[0]
            if _tmpl_path.suffix.lower() == ".pdf":
                st.session_state["synthesis_template_pdf_bytes"] = _tmpl_path.read_bytes()
            else:
                st.session_state["synthesis_template_pdf_bytes"] = None
            st.session_state["synthesis_template_image"] = img
        except ImportError as e:
            st.error(str(e))

    else:
        # Blank page
        st.session_state["synthesis_template_image"] = Image.new(
            "RGB", (int(blank_w), int(blank_h)), (255, 255, 255)
        )
        st.session_state["synthesis_template_pdf_bytes"] = None

    # Thumbnail preview + output mode indicator
    template_img: Image.Image = st.session_state["synthesis_template_image"]
    if template_img is not None:
        st.markdown("---")
        has_pdf = st.session_state.get("synthesis_template_pdf_bytes") is not None
        if has_pdf:
            st.success(
                "📄 **PDF template loaded** — generated documents will be exported as PDF "
                "with text written as native PDF objects (searchable, copy-pasteable)."
            )
        else:
            st.info(
                "🖼️ **Blank / image template** — generated documents will be exported as PDF "
                "(new blank PDF created to match canvas dimensions)."
            )
        st.markdown(f"**Preview** — {template_img.width} × {template_img.height} px")
        thumb_w = min(template_img.width, 400)
        st.image(template_img, width=thumb_w)


# ---------------------------------------------------------------------------
# Tab 2 — Respondents
# ---------------------------------------------------------------------------


def _tab_respondents() -> None:
    respondents: list[dict] = st.session_state["synthesis_respondents"]

    if st.button("+ Add respondent", key="add_respondent"):
        idx = len(respondents) + 1
        respondents.append(
            {
                "respondent_id": f"person_{idx}",
                "display_name": f"Person {idx}",
                "field_types": [dict(_DEFAULT_FIELD_TYPE)],
            }
        )
        st.session_state["synthesis_respondents"] = respondents
        st.rerun()

    if not respondents:
        st.info("No respondents yet. Click '+ Add respondent' to get started.")
        return

    colour_map = _respondent_colour_map(respondents)
    tab_labels = [r["display_name"] for r in respondents]
    resp_tabs = st.tabs(tab_labels)

    to_remove_r: list[int] = []
    for ri, (resp, resp_tab) in enumerate(zip(respondents, resp_tabs)):
        with resp_tab:
            resp_colour = colour_map.get(resp["respondent_id"], _RESPONDENT_PALETTE[0])

            # Respondent name with colour badge
            name_col, badge_col = st.columns([5, 1])
            resp_label_key = f"resp_name_{ri}"
            new_name = name_col.text_input(
                "Respondent name",
                value=resp["display_name"],
                key=resp_label_key,
            )
            resp["display_name"] = new_name
            resp["respondent_id"] = new_name.lower().replace(" ", "_")
            badge_col.markdown(
                f'<div style="height:38px;display:flex;align-items:center;">'
                f'<span style="display:inline-block;width:24px;height:24px;'
                f"background:{resp_colour};border-radius:4px;border:1px solid #888;"
                f'"></span></div>',
                unsafe_allow_html=True,
            )

            st.markdown("---")
            st.markdown("**Field types** — ink colours used within this respondent's zones")

            # Compact row header
            hcols = st.columns([1, 3, 2, 2, 1])
            hcols[0].markdown("**Colour**")
            hcols[1].markdown("**Name**")
            hcols[2].markdown("**Size**")
            hcols[3].markdown("**Style**")
            hcols[4].markdown("")

            ft_edit_key = f"ft_editing_{ri}"
            if ft_edit_key not in st.session_state:
                st.session_state[ft_edit_key] = None

            to_remove_ft: list[int] = []
            for fti, ft in enumerate(resp["field_types"]):
                row = st.columns([1, 3, 2, 2, 1])
                color_hex = ft.get("font_color", "#000000")
                row[0].markdown(
                    f'<span style="display:inline-block;width:18px;height:18px;'
                    f"background:{color_hex};border:1px solid #888;border-radius:3px;"
                    f'vertical-align:middle;"></span>',
                    unsafe_allow_html=True,
                )
                row[1].markdown(ft["display_name"])
                size_r = ft.get("font_size_range", [10, 14])
                row[2].markdown(f"{size_r[0]}–{size_r[1]} pt")
                row[3].markdown(ft.get("fill_style", "typed"))
                if row[4].button("Edit", key=f"ft_edit_btn_{ri}_{fti}"):
                    current = st.session_state[ft_edit_key]
                    st.session_state[ft_edit_key] = fti if current != fti else None
                    st.rerun()

                # Inline editor (toggled by Edit button)
                if st.session_state.get(ft_edit_key) == fti:
                    with st.expander(f"Edit: {ft['display_name']}", expanded=True):
                        ft_label_key = f"ft_name_{ri}_{fti}"
                        ft["display_name"] = st.text_input(
                            "Field type name",
                            value=ft["display_name"],
                            key=ft_label_key,
                        )
                        ft["field_type_id"] = ft["display_name"].lower().replace(" ", "_")

                        # Ink colour presets
                        color_key = f"ft_color_{ri}_{fti}"
                        preset_cols = st.columns(len(_INK_PRESETS))
                        for pi, (preset_label, hex_val) in enumerate(_INK_PRESETS):
                            with preset_cols[pi]:
                                st.markdown(
                                    f'<div style="display:flex;align-items:center;gap:4px;">'
                                    f'<span style="display:inline-block;width:12px;height:12px;'
                                    f"background:{hex_val};border:1px solid #888;border-radius:2px;"
                                    f'"></span></div>',
                                    unsafe_allow_html=True,
                                )
                                if st.button(preset_label, key=f"preset_{ri}_{fti}_{pi}"):
                                    ft["font_color"] = hex_val
                                    st.session_state[color_key] = hex_val

                        ft["font_color"] = st.color_picker(
                            "Ink colour", value=ft["font_color"], key=color_key
                        )
                        ft["font_family"] = st.selectbox(
                            "Font family",
                            _FONT_FAMILIES,
                            index=_FONT_FAMILIES.index(ft.get("font_family", "sans-serif")),
                            key=f"ft_family_{ri}_{fti}",
                        )
                        size_range = st.slider(
                            "Font size range (pt)",
                            min_value=6,
                            max_value=72,
                            value=tuple(ft["font_size_range"]),
                            key=f"ft_size_{ri}_{fti}",
                        )
                        ft["font_size_range"] = list(size_range)
                        ft["fill_style"] = st.radio(
                            "Fill style",
                            _FILL_STYLES,
                            index=_FILL_STYLES.index(ft.get("fill_style", "typed")),
                            horizontal=True,
                            key=f"ft_fill_{ri}_{fti}",
                        )

                        with st.expander("Advanced ▸", expanded=False):
                            c1, c2 = st.columns(2)
                            ft["bold"] = c1.checkbox(
                                "Bold",
                                value=ft.get("bold", False),
                                key=f"ft_bold_{ri}_{fti}",
                            )
                            ft["italic"] = c2.checkbox(
                                "Italic",
                                value=ft.get("italic", False),
                                key=f"ft_italic_{ri}_{fti}",
                            )
                            ft["jitter_x"] = st.slider(
                                "Jitter X",
                                0.0,
                                0.5,
                                ft.get("jitter_x", 0.05),
                                key=f"ft_jx_{ri}_{fti}",
                            )
                            ft["jitter_y"] = st.slider(
                                "Jitter Y",
                                0.0,
                                0.3,
                                ft.get("jitter_y", 0.02),
                                key=f"ft_jy_{ri}_{fti}",
                            )

                        if len(resp["field_types"]) > 1 and st.button(
                            "🗑 Remove field type", key=f"rm_ft_{ri}_{fti}"
                        ):
                            to_remove_ft.append(fti)
                            st.session_state[ft_edit_key] = None

            for fti in reversed(to_remove_ft):
                resp["field_types"].pop(fti)

            if st.button("+ Add field type", key=f"add_ft_{ri}"):
                resp["field_types"].append(
                    {
                        "field_type_id": f"type_{len(resp['field_types']) + 1}",
                        "display_name": "New field type",
                        "font_family": "sans-serif",
                        "font_size_range": [10, 14],
                        "font_color": "#000000",
                        "bold": False,
                        "italic": False,
                        "fill_style": "typed",
                        "jitter_x": 0.05,
                        "jitter_y": 0.02,
                        "baseline_wander": 0.0,
                        "char_spacing_jitter": 0.0,
                    }
                )

            if len(respondents) > 1:
                st.markdown("---")
                if st.button("🗑 Remove respondent", key=f"rm_resp_{ri}"):
                    to_remove_r.append(ri)

    for ri in reversed(to_remove_r):
        respondents.pop(ri)
    st.session_state["synthesis_respondents"] = respondents


# ---------------------------------------------------------------------------
# Tab 3 — Zones (click-to-place)
# ---------------------------------------------------------------------------


def _respondent_colour_map(respondents: list[dict]) -> dict[str, str]:
    """Return {respondent_id: hex_colour} using the palette in order of definition."""
    return {
        r["respondent_id"]: _RESPONDENT_PALETTE[i % len(_RESPONDENT_PALETTE)]
        for i, r in enumerate(respondents)
    }


def _draw_zones_on_image(
    template_img: Image.Image,
    zones: list[dict],
    respondents: list[dict],
) -> Image.Image:
    """Overlay zone rectangles coloured by respondent, with a label above each box."""
    from PIL import ImageDraw, ImageFont

    if not zones:
        return template_img

    colour_map = _respondent_colour_map(respondents)
    resp_name_map = {r["respondent_id"]: r["display_name"] for r in respondents}
    ft_name_map: dict[str, dict[str, str]] = {
        r["respondent_id"]: {ft["field_type_id"]: ft["display_name"] for ft in r["field_types"]}
        for r in respondents
    }

    out = template_img.convert("RGB").copy()
    draw = ImageDraw.Draw(out)

    # Small readable font for labels (9 pt; falls back to PIL default if needed)
    try:
        from document_simulator.synthesis.fonts import FontResolver

        label_font = FontResolver.resolve("sans-serif", size=max(9, template_img.width // 80))
    except Exception:
        label_font = ImageFont.load_default()

    for zone in zones:
        resp_id = zone.get("respondent_id", "")
        ft_id = zone.get("field_type_id", "")
        hex_colour = colour_map.get(resp_id, "#2196F3")

        # Parse hex → RGB tuple
        h = hex_colour.lstrip("#")
        rgb = tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))

        pts = [(int(p[0]), int(p[1])) for p in zone["box"]]

        # Draw box outline (2-px stroke via polygon)
        draw.polygon(pts, outline=rgb)
        # A second slightly-inset outline for a thicker look
        draw.line(pts + [pts[0]], fill=rgb, width=2)

        # Label: "RespondentName / FieldType"
        resp_name = resp_name_map.get(resp_id, resp_id)
        ft_display = ft_name_map.get(resp_id, {}).get(ft_id, ft_id)
        label = f"{resp_name} / {ft_display}"

        x0, y0 = pts[0]
        label_y = max(0, y0 - 14)

        # Small filled background pill for readability
        try:
            bbox = draw.textbbox((x0, label_y), label, font=label_font)
            pad = 2
            draw.rectangle(
                [bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad],
                fill=rgb,
            )
            draw.text((x0, label_y), label, font=label_font, fill=(255, 255, 255))
        except AttributeError:
            # PIL < 9.2 doesn't have textbbox
            draw.text((x0, label_y), label, font=label_font, fill=rgb)

    return out


def _draw_first_click_marker(img: Image.Image, px: int, py: int) -> Image.Image:
    """Draw a red crosshair + circle at the first-click anchor position."""
    from PIL import ImageDraw

    img = img.copy()
    draw = ImageDraw.Draw(img)
    r = max(6, img.width // 60)
    arm = r * 3
    draw.ellipse([px - r, py - r, px + r, py + r], outline="#FF3333", width=3)
    draw.line([px - arm, py, px + arm, py], fill="#FF3333", width=2)
    draw.line([px, py - arm, px, py + arm], fill="#FF3333", width=2)
    return img


# ---------------------------------------------------------------------------
# Cached overlay drawing — avoids PIL redraw when zones/template unchanged
# ---------------------------------------------------------------------------


@st.cache_data(
    hash_funcs={Image.Image: lambda img: hashlib.md5(img.tobytes()).hexdigest()},
    max_entries=8,
)
def _draw_zones_on_image_cached(
    template_img: Image.Image,
    zones_hash: str,  # included in cache key — invalidates when zones/respondents change
    _zones: list[dict],  # leading _ = not auto-hashed; zones_hash covers this
    _respondents: list[dict],  # leading _ = not auto-hashed; zones_hash covers this
) -> Image.Image:
    """Cached PIL overlay draw. Only re-executes when template or zones change."""
    return _draw_zones_on_image(template_img, _zones, _respondents)


# ---------------------------------------------------------------------------
# Tab 3 — Zones (fragment-isolated for fast reruns)
# ---------------------------------------------------------------------------


@st.fragment
def _zone_tab_fragment() -> None:
    respondents: list[dict] = st.session_state["synthesis_respondents"]
    template_img: Image.Image | None = st.session_state["synthesis_template_image"]
    zones: list[dict] = st.session_state["synthesis_zones"]

    if template_img is None:
        st.info("Go to the **Template** tab first to set a template image.")
        return

    resp_id_to_name = {r["respondent_id"]: r["display_name"] for r in respondents}
    resp_name_to_id = {r["display_name"]: r["respondent_id"] for r in respondents}
    resp_options_map = {r["respondent_id"]: r for r in respondents}

    # Uniform scale — image preserves aspect ratio when displayed at display_w
    display_w = min(template_img.width, _DISPLAY_W)
    scale = template_img.width / display_w

    first_click: dict | None = st.session_state.get("zone_first_click")
    click_counter: int = st.session_state.get("zone_click_counter", 0)

    # Build preview: zone overlays + optional first-click marker (cached)
    zones_hash = _stable_zones_hash(zones, respondents)
    preview_img = _draw_zones_on_image_cached(template_img, zones_hash, zones, respondents).copy()
    if first_click is not None:
        preview_img = _draw_first_click_marker(preview_img, first_click["x"], first_click["y"])

    # CSS border around the clickable zone canvas (iframe for coords component,
    # img tag for the st.image fallback)
    st.markdown(
        """
        <style>
        /* Outline the zone canvas so users know it is clickable */
        div[data-testid="column"]:first-of-type iframe,
        div[data-testid="column"]:first-of-type img {
            outline: 2px dashed #4A90D9;
            outline-offset: 3px;
            border-radius: 4px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    col_img, col_list = st.columns([3, 2])

    # ---- Left: image ----
    with col_img:
        if _COORDS_AVAILABLE:
            # Instruction line
            if first_click is None:
                st.caption("Click on the image to set the **top-left** corner of a new zone.")
            else:
                info_col, cancel_col = st.columns([4, 1])
                info_col.caption(
                    f"Corner 1 at ({first_click['x']}, {first_click['y']} px) — "
                    "now click the **bottom-right** corner."
                )
                if cancel_col.button("✕ Cancel", key="cancel_zone_click"):
                    # Rotate key so the stale coords are discarded on next render
                    st.session_state["zone_first_click"] = None
                    st.session_state["zone_click_counter"] = click_counter + 1
                    st.rerun(scope="fragment")

            # Rotating key forces a fresh widget (coords=None) after each consumed click,
            # preventing the infinite-rerun loop where stale coords re-trigger immediately.
            coords = streamlit_image_coordinates(
                preview_img, width=display_w, key=f"zone_click_{click_counter}"
            )

            if coords is not None:
                raw_x = int(coords["x"] * scale)
                raw_y = int(coords["y"] * scale)
                # Advance counter before rerun so the next render sees a fresh widget
                st.session_state["zone_click_counter"] = click_counter + 1

                if first_click is None:
                    st.session_state["zone_first_click"] = {"x": raw_x, "y": raw_y}
                    st.rerun(scope="fragment")
                else:
                    x1 = float(min(first_click["x"], raw_x))
                    y1 = float(min(first_click["y"], raw_y))
                    x2 = float(max(first_click["x"], raw_x))
                    y2 = float(max(first_click["y"], raw_y))
                    if x2 > x1 and y2 > y1:
                        idx = len(zones) + 1
                        default_resp = respondents[0] if respondents else None
                        zones.append(
                            {
                                "zone_id": f"z_{idx}",
                                "label": f"zone_{idx}",
                                "box": [[x1, y1], [x2, y1], [x2, y2], [x1, y2]],
                                "respondent_id": default_resp["respondent_id"]
                                if default_resp
                                else "default",
                                "field_type_id": default_resp["field_types"][0]["field_type_id"]
                                if default_resp
                                else "standard",
                                "faker_provider": "name",
                                "custom_values": [],
                                "alignment": "left",
                            }
                        )
                        st.session_state["synthesis_zones"] = zones
                    st.session_state["zone_first_click"] = None
                    st.rerun(scope="fragment")

        else:
            # Fallback: manual entry via form (clear_on_submit avoids stale field values)
            st.image(
                preview_img,
                caption=f"Template — {template_img.width} × {template_img.height} px",
                width=display_w,
            )
            st.caption(
                "Tip: run `uv sync --extra synthesis --native-tls` to enable click-to-place."
            )
            with st.form("add_zone_form", clear_on_submit=True):
                st.markdown("**Add a zone**")
                new_label = st.text_input("Label", placeholder=f"zone_{len(zones) + 1}")
                c1, c2 = st.columns(2)
                new_x = c1.number_input("Left (px)", value=10, min_value=0)
                new_y = c2.number_input("Top (px)", value=20, min_value=0)
                new_w = c1.number_input("Width (px)", value=200, min_value=1)
                new_h = c2.number_input("Height (px)", value=30, min_value=1)
                if st.form_submit_button("+ Add zone"):
                    x1, y1 = float(new_x), float(new_y)
                    x2, y2 = x1 + float(new_w), y1 + float(new_h)
                    idx = len(zones) + 1
                    zones.append(
                        {
                            "zone_id": f"z_{idx}",
                            "label": new_label.strip() or f"zone_{idx}",
                            "box": [[x1, y1], [x2, y1], [x2, y2], [x1, y2]],
                            "respondent_id": respondents[0]["respondent_id"]
                            if respondents
                            else "default",
                            "field_type_id": respondents[0]["field_types"][0]["field_type_id"]
                            if respondents
                            else "standard",
                            "faker_provider": "name",
                            "custom_values": [],
                            "alignment": "left",
                        }
                    )
                    st.session_state["synthesis_zones"] = zones
                    st.rerun(scope="fragment")

    # ---- Right: zone list (single st.data_editor — O(1) widget calls) ----
    with col_list:
        n = len(zones)
        hdr_col, clear_col = st.columns([3, 1])
        hdr_col.markdown(f"**{n} zone{'s' if n != 1 else ''}**")
        if n > 0 and clear_col.button("Clear all", key="clear_all_zones"):
            st.session_state["synthesis_zones"] = []
            st.session_state["zone_first_click"] = None
            st.rerun(scope="fragment")

        if not zones:
            st.caption("No zones yet.")
        else:
            resp_names = list(resp_name_to_id.keys())
            df = _zones_to_dataframe(zones, resp_id_to_name)
            edited = st.data_editor(
                df,
                num_rows="dynamic",
                use_container_width=True,
                key="zones_table",
                column_config={
                    "label": st.column_config.TextColumn("Label"),
                    "respondent": st.column_config.SelectboxColumn(
                        "Respondent",
                        options=resp_names or ["default"],
                    ),
                    "field_type": st.column_config.TextColumn("Field type"),
                    "data_source": st.column_config.SelectboxColumn(
                        "Data source",
                        options=_FAKER_PROVIDERS,
                    ),
                    "x1": st.column_config.NumberColumn("x1", disabled=True, format="%d"),
                    "y1": st.column_config.NumberColumn("y1", disabled=True, format="%d"),
                    "x2": st.column_config.NumberColumn("x2", disabled=True, format="%d"),
                    "y2": st.column_config.NumberColumn("y2", disabled=True, format="%d"),
                },
            )
            updated_zones = _dataframe_to_zones(edited, zones, resp_name_to_id)
            if updated_zones != zones:
                st.session_state["synthesis_zones"] = updated_zones
                st.rerun(scope="fragment")


# ---------------------------------------------------------------------------
# Tab 4 — Preview & Generate
# ---------------------------------------------------------------------------


def _tab_preview_generate() -> None:
    zones = st.session_state["synthesis_zones"]

    # Config save/load in collapsed expander
    with st.expander("💾 Config", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            config_json = _build_synthesis_config().model_dump_json(indent=2)
            st.download_button(
                "💾 Save config",
                data=config_json,
                file_name="synthesis_config.json",
                mime="application/json",
            )
        with col2:
            uploaded_cfg = st.file_uploader("Load config", type=["json"], key="load_config")
            if uploaded_cfg is not None:
                try:
                    loaded = SynthesisConfig.model_validate_json(uploaded_cfg.read())
                    st.session_state["synthesis_respondents"] = [
                        {
                            "respondent_id": r.respondent_id,
                            "display_name": r.display_name,
                            "field_types": [ft.model_dump() for ft in r.field_types],
                        }
                        for r in loaded.respondents
                    ]
                    st.session_state["synthesis_zones"] = [z.model_dump() for z in loaded.zones]
                    st.success("Config loaded.")
                except Exception as exc:
                    st.error(f"Failed to load config: {exc}")

    st.markdown("### Preview")

    pdf_bytes_template: bytes | None = st.session_state.get("synthesis_template_pdf_bytes")

    col_btn, col_overlay = st.columns([1, 1])
    with col_overlay:
        show_overlays = st.checkbox(
            "Show zone overlays",
            value=st.session_state["show_zone_overlays"],
            key="show_overlays",
        )
        st.session_state["show_zone_overlays"] = show_overlays

    with col_btn:
        if st.button("🔍 Generate 3 previews"):
            if not zones:
                st.warning("Define at least one zone before previewing.")
            else:
                config = _build_synthesis_config()
                template_src = st.session_state["synthesis_template_image"]
                gen = SyntheticDocumentGenerator(
                    template=template_src,
                    synthesis_config=config,
                    pdf_bytes=pdf_bytes_template,
                )
                samples = []
                sample_pdfs = []
                for i in range(3):
                    try:
                        img, gt, pdf_out = gen.generate_one_pdf(seed=42 + i)
                        samples.append((img, gt))
                        sample_pdfs.append(pdf_out)
                    except Exception as exc:
                        st.error(f"Preview failed: {exc}")
                        break
                st.session_state["preview_samples"] = samples
                st.session_state["preview_sample_pdfs"] = sample_pdfs

    samples: list = st.session_state.get("preview_samples", [])
    sample_pdfs: list = st.session_state.get("preview_sample_pdfs", [])
    if samples:
        cols = st.columns(len(samples))
        for i, (img, gt) in enumerate(samples):
            display_img = img
            if show_overlays and zones:
                respondents = st.session_state["synthesis_respondents"]
                display_img = _draw_zones_on_image(img, zones, respondents)
            with cols[i]:
                st.image(display_img, caption=f"seed={42 + i}", use_container_width=True)
                btn_col, dl_col = st.columns([1, 1])
                if btn_col.button("↻", key=f"reroll_{i}"):
                    config = _build_synthesis_config()
                    template_src = st.session_state["synthesis_template_image"]
                    gen = SyntheticDocumentGenerator(
                        template=template_src,
                        synthesis_config=config,
                        pdf_bytes=pdf_bytes_template,
                    )
                    new_img, new_gt, new_pdf = gen.generate_one_pdf(seed=1000 + i)
                    samples[i] = (new_img, new_gt)
                    if i < len(sample_pdfs):
                        sample_pdfs[i] = new_pdf
                    else:
                        sample_pdfs.append(new_pdf)
                    st.session_state["preview_samples"] = samples
                    st.session_state["preview_sample_pdfs"] = sample_pdfs
                    st.rerun()
                pdf_data = sample_pdfs[i] if i < len(sample_pdfs) else None
                if pdf_data is not None:
                    dl_col.download_button(
                        "📄 PDF",
                        data=pdf_data,
                        file_name=f"preview_{42 + i}.pdf",
                        mime="application/pdf",
                        key=f"dl_pdf_{i}",
                    )

    st.divider()
    st.markdown("### Batch Generation")

    col1, col2 = st.columns(2)
    with col1:
        n_docs = st.number_input("Number of documents", min_value=1, value=10, step=1)
    with col2:
        output_dir = st.text_input("Output directory", value="output/synthetic")

    if st.button("⚙️ Generate batch"):
        if not zones:
            st.warning("Define at least one zone before generating.")
            return
        config = _build_synthesis_config()
        config.generator.n = int(n_docs)
        config.generator.output_dir = output_dir
        template_src = st.session_state["synthesis_template_image"]
        gen = SyntheticDocumentGenerator(
            template=template_src,
            synthesis_config=config,
            pdf_bytes=pdf_bytes_template,
        )
        with st.spinner(f"Generating {n_docs} documents…"):
            pairs = gen.generate(n=int(n_docs), write=True, output_pdf=True)
        st.success(f"Generated {len(pairs)} documents → {output_dir}")

        # Build ZIP: PDFs + JSON annotations
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for i, (img, gt) in enumerate(pairs):
                stem = f"doc_{i + 1:06d}"
                # Re-generate PDF for the ZIP (write=True already saved to disk;
                # this re-generates in memory for the download bundle)
                try:
                    _, _, pdf_out = gen.generate_one_pdf(
                        seed=config.generator.seed + i
                    )
                    zf.writestr(f"{stem}.pdf", pdf_out)
                except Exception:
                    # Fallback: include PNG if PDF generation fails
                    img_buf = io.BytesIO()
                    img.save(img_buf, format="PNG")
                    zf.writestr(f"{stem}.png", img_buf.getvalue())
                zf.writestr(f"{stem}.json", gt.model_dump_json(indent=2))
        buf.seek(0)
        st.download_button(
            "📦 Download ZIP",
            data=buf.getvalue(),
            file_name="synthetic_documents.zip",
            mime="application/zip",
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    st.set_page_config(page_title="Synthetic Document Generator", layout="wide")
    st.title("Synthetic Document Generator")
    st.info(
        "**How to use:** Upload a PDF or image template (or use a blank page), define "
        "respondents and field types in the **Respondents** tab, draw zones on the template "
        "in the **Zones** tab, then preview and generate a batch in **Preview & Generate**. "
        "Each generated document is saved as a PDF alongside a `.json` annotation file "
        "(same filename stem) — these pairs can be used directly as input to the "
        "**Evaluation Dashboard** and **RL Training** pages."
    )
    _init_state()

    tab1, tab2, tab3, tab4 = st.tabs(
        ["📄 Template", "👥 Respondents", "🗺️ Zones", "✨ Preview & Generate"]
    )

    with tab1:
        _tab_template()

    with tab2:
        _tab_respondents()

    with tab3:
        _zone_tab_fragment()

    with tab4:
        _tab_preview_generate()


main()
