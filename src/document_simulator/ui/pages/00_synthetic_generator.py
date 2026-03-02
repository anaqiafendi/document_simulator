"""Synthetic Document Generator — Streamlit UI page.

Workflow:
  Panel 1 — Upload template (PDF / image / blank canvas)
  Panel 2 — Define respondents and their field-type style profiles
  Panel 3 — Draw zones on the template canvas, assign to respondent + field type
  Preview  — Generate a few samples in-memory, gallery with re-roll
  Batch    — Full batch generation with disk write + ZIP download
"""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import streamlit as st
from PIL import Image

from document_simulator.synthesis.generator import SyntheticDocumentGenerator
from document_simulator.synthesis.zones import (
    FieldTypeConfig,
    GeneratorConfig,
    RespondentConfig,
    SynthesisConfig,
    ZoneConfig,
)
from document_simulator.ui.components.image_display import image_to_bytes, overlay_bboxes

# ---------------------------------------------------------------------------
# Optional canvas component
# ---------------------------------------------------------------------------
try:
    from streamlit_drawable_canvas import st_canvas

    _CANVAS_AVAILABLE = True
except ImportError:
    _CANVAS_AVAILABLE = False

# ---------------------------------------------------------------------------
# Ink colour presets
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


# ---------------------------------------------------------------------------
# Session state helpers
# ---------------------------------------------------------------------------


def _init_state() -> None:
    defaults: dict = {
        "synthesis_respondents": [
            {
                "respondent_id": "person_1",
                "display_name": "Person 1",
                "field_types": [
                    {
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
                ],
            }
        ],
        "synthesis_zones": [],
        "synthesis_template_image": None,
        "preview_samples": [],
        "show_zone_overlays": False,
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
# Sub-panels
# ---------------------------------------------------------------------------


def _panel_template() -> None:
    st.subheader("1. Template")
    col_a, col_b = st.columns([2, 1])
    with col_a:
        uploaded = st.file_uploader(
            "Upload PDF or image template",
            type=["png", "jpg", "jpeg", "pdf"],
            key="template_upload",
        )
    with col_b:
        use_blank = st.checkbox("Use blank page", value=True, key="use_blank")
        blank_w = st.number_input("Width (px)", value=794, min_value=100, key="blank_w")
        blank_h = st.number_input("Height (px)", value=1123, min_value=100, key="blank_h")

    if uploaded is not None:
        if uploaded.name.lower().endswith(".pdf"):
            try:
                import fitz

                data = uploaded.read()
                doc = fitz.open(stream=data, filetype="pdf")
                page = doc[0]
                mat = fitz.Matrix(150 / 72, 150 / 72)
                pix = page.get_pixmap(matrix=mat)
                img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            except ImportError:
                st.warning("PyMuPDF not installed. Install with: uv sync --extra synthesis")
                img = Image.new("RGB", (int(blank_w), int(blank_h)), (255, 255, 255))
        else:
            img = Image.open(io.BytesIO(uploaded.read())).convert("RGB")
        st.session_state["synthesis_template_image"] = img
    elif use_blank or st.session_state["synthesis_template_image"] is None:
        st.session_state["synthesis_template_image"] = Image.new(
            "RGB", (int(blank_w), int(blank_h)), (255, 255, 255)
        )


def _panel_respondents() -> None:
    st.subheader("2. Respondents & Field Types")
    respondents: list[dict] = st.session_state["synthesis_respondents"]

    if st.button("+ Add respondent", key="add_respondent"):
        idx = len(respondents) + 1
        respondents.append(
            {
                "respondent_id": f"person_{idx}",
                "display_name": f"Person {idx}",
                "field_types": [
                    {
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
                ],
            }
        )
        st.session_state["synthesis_respondents"] = respondents

    to_remove_r: list[int] = []
    for ri, resp in enumerate(respondents):
        with st.expander(f"👤 {resp['display_name']}", expanded=(ri == 0)):
            resp["display_name"] = st.text_input(
                "Name", value=resp["display_name"], key=f"resp_name_{ri}"
            )
            resp["respondent_id"] = resp["display_name"].lower().replace(" ", "_")

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

            to_remove_ft: list[int] = []
            for fti, ft in enumerate(resp["field_types"]):
                with st.expander(f"  📝 {ft['display_name']}", expanded=False):
                    ft["display_name"] = st.text_input(
                        "Field type name", value=ft["display_name"], key=f"ft_name_{ri}_{fti}"
                    )
                    ft["field_type_id"] = ft["display_name"].lower().replace(" ", "_")

                    # Ink colour presets
                    preset_cols = st.columns(len(_INK_PRESETS))
                    for pi, (label, hex_val) in enumerate(_INK_PRESETS):
                        if preset_cols[pi].button(label, key=f"preset_{ri}_{fti}_{pi}"):
                            ft["font_color"] = hex_val

                    ft["font_color"] = st.color_picker(
                        "Ink colour", value=ft["font_color"], key=f"ft_color_{ri}_{fti}"
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
                    c1, c2 = st.columns(2)
                    ft["bold"] = c1.checkbox("Bold", value=ft.get("bold", False), key=f"ft_bold_{ri}_{fti}")
                    ft["italic"] = c2.checkbox("Italic", value=ft.get("italic", False), key=f"ft_italic_{ri}_{fti}")
                    ft["jitter_x"] = st.slider(
                        "Jitter X", 0.0, 0.5, ft.get("jitter_x", 0.05), key=f"ft_jx_{ri}_{fti}"
                    )
                    ft["jitter_y"] = st.slider(
                        "Jitter Y", 0.0, 0.3, ft.get("jitter_y", 0.02), key=f"ft_jy_{ri}_{fti}"
                    )

                    if len(resp["field_types"]) > 1 and st.button(
                        "🗑 Remove field type", key=f"rm_ft_{ri}_{fti}"
                    ):
                        to_remove_ft.append(fti)

            for fti in reversed(to_remove_ft):
                resp["field_types"].pop(fti)

            if len(respondents) > 1 and st.button(
                "🗑 Remove respondent", key=f"rm_resp_{ri}"
            ):
                to_remove_r.append(ri)

    for ri in reversed(to_remove_r):
        respondents.pop(ri)
    st.session_state["synthesis_respondents"] = respondents


def _panel_zones() -> None:
    st.subheader("3. Zone Placement")
    respondents: list[dict] = st.session_state["synthesis_respondents"]
    template_img: Image.Image = st.session_state["synthesis_template_image"]
    zones: list[dict] = st.session_state["synthesis_zones"]

    # Respondent → field type options for dropdowns
    resp_options = {r["respondent_id"]: r for r in respondents}
    resp_display_map = {r["display_name"]: r["respondent_id"] for r in respondents}

    # --- Canvas (or fallback) ---
    st.markdown("**Draw rectangles on the template to place zones.**")

    if _CANVAS_AVAILABLE and template_img is not None:
        try:
            canvas_result = st_canvas(
                fill_color="rgba(0, 100, 255, 0.15)",
                stroke_width=2,
                stroke_color="#0050FF",
                background_image=template_img,
                drawing_mode="rect",
                key="zone_canvas",
                height=min(template_img.height, 600),
                width=min(template_img.width, 800),
            )
        except Exception:
            st.info("Canvas component is not available. Use manual zone entry below.")
            canvas_result = None
        # Extract new drawn rectangles
        if canvas_result is not None and canvas_result.json_data is not None:
            objects = canvas_result.json_data.get("objects", [])
            existing_ids = {z["zone_id"] for z in zones}
            display_w = min(template_img.width, 800)
            display_h = min(template_img.height, 600)
            scale_x = template_img.width / display_w
            scale_y = template_img.height / display_h
            for obj in objects:
                if obj.get("type") == "rect":
                    zone_id = f"z_{obj['left']:.0f}_{obj['top']:.0f}"
                    if zone_id not in existing_ids:
                        left = obj["left"] * scale_x
                        top = obj["top"] * scale_y
                        w = obj["width"] * scale_x
                        h = obj["height"] * scale_y
                        zones.append(
                            {
                                "zone_id": zone_id,
                                "label": f"zone_{len(zones) + 1}",
                                "box": [
                                    [left, top],
                                    [left + w, top],
                                    [left + w, top + h],
                                    [left, top + h],
                                ],
                                "respondent_id": respondents[0]["respondent_id"],
                                "field_type_id": respondents[0]["field_types"][0]["field_type_id"],
                                "faker_provider": "name",
                                "custom_values": [],
                                "alignment": "left",
                            }
                        )
            st.session_state["synthesis_zones"] = zones
    else:
        st.info("Canvas not available. Add zones manually below.")
        if st.button("+ Add zone manually"):
            idx = len(zones) + 1
            zones.append(
                {
                    "zone_id": f"z_{idx}",
                    "label": f"zone_{idx}",
                    "box": [[0, 0], [200, 0], [200, 40], [0, 40]],
                    "respondent_id": respondents[0]["respondent_id"] if respondents else "default",
                    "field_type_id": "standard",
                    "faker_provider": "name",
                    "custom_values": [],
                    "alignment": "left",
                }
            )
            st.session_state["synthesis_zones"] = zones

    # --- Zone configuration cards ---
    if zones:
        st.markdown("---")
        to_remove: list[int] = []
        for zi, zone in enumerate(zones):
            resp_id = zone.get("respondent_id", respondents[0]["respondent_id"])
            resp = resp_options.get(resp_id, respondents[0])
            ft_ids = [ft["field_type_id"] for ft in resp["field_types"]]
            ft_color = next(
                (ft["font_color"] for ft in resp["field_types"]
                 if ft["field_type_id"] == zone.get("field_type_id")),
                "#000000",
            )

            with st.expander(
                f"Zone {zi + 1}: {zone['label']}  |  {resp['display_name']} / {zone.get('field_type_id', 'standard')}",
                expanded=False,
            ):
                zone["label"] = st.text_input("Label", value=zone["label"], key=f"z_label_{zi}")

                resp_name = st.selectbox(
                    "Respondent",
                    list(resp_display_map.keys()),
                    index=list(resp_display_map.values()).index(zone["respondent_id"])
                    if zone["respondent_id"] in resp_display_map.values()
                    else 0,
                    key=f"z_resp_{zi}",
                )
                zone["respondent_id"] = resp_display_map[resp_name]
                resp = resp_options[zone["respondent_id"]]
                ft_ids = [ft["field_type_id"] for ft in resp["field_types"]]

                zone["field_type_id"] = st.selectbox(
                    "Field type",
                    ft_ids,
                    index=ft_ids.index(zone["field_type_id"])
                    if zone["field_type_id"] in ft_ids
                    else 0,
                    key=f"z_ft_{zi}",
                )
                zone["faker_provider"] = st.selectbox(
                    "Faker provider",
                    ["name", "first_name", "last_name", "full_name", "initials",
                     "address", "date", "phone_number", "ssn", "pricetag", "company", "custom"],
                    index=0,
                    key=f"z_provider_{zi}",
                )
                if zone["faker_provider"] == "custom":
                    raw = st.text_area(
                        "Custom values (one per line)",
                        value="\n".join(zone.get("custom_values", [])),
                        key=f"z_custom_{zi}",
                    )
                    zone["custom_values"] = [v.strip() for v in raw.splitlines() if v.strip()]
                else:
                    zone["custom_values"] = []

                zone["alignment"] = st.radio(
                    "Alignment",
                    ["left", "center", "right"],
                    horizontal=True,
                    key=f"z_align_{zi}",
                )
                if st.button("🗑 Remove zone", key=f"rm_z_{zi}"):
                    to_remove.append(zi)

        for zi in reversed(to_remove):
            zones.pop(zi)
        st.session_state["synthesis_zones"] = zones


def _panel_actions() -> None:
    st.subheader("Config")
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
        uploaded_cfg = st.file_uploader(
            "Load config", type=["json"], key="load_config"
        )
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


def _panel_preview() -> None:
    st.subheader("Preview")
    zones = st.session_state["synthesis_zones"]
    col_btn, col_overlay = st.columns([1, 1])
    with col_overlay:
        show_overlays = st.checkbox(
            "Show zone overlays", value=st.session_state["show_zone_overlays"], key="show_overlays"
        )
        st.session_state["show_zone_overlays"] = show_overlays

    with col_btn:
        if st.button("🔍 Preview (3 samples)"):
            if not zones:
                st.warning("Define at least one zone before previewing.")
            else:
                config = _build_synthesis_config()
                gen = SyntheticDocumentGenerator(
                    template="blank"
                    if st.session_state.get("use_blank", True)
                    else st.session_state["synthesis_template_image"],
                    synthesis_config=config,
                )
                samples = []
                for i in range(3):
                    try:
                        img, gt = gen.generate_one(seed=42 + i)
                        samples.append((img, gt))
                    except Exception as exc:
                        st.error(f"Preview failed: {exc}")
                        break
                st.session_state["preview_samples"] = samples

    samples: list = st.session_state.get("preview_samples", [])
    if samples:
        cols = st.columns(len(samples))
        for i, (img, gt) in enumerate(samples):
            display_img = img
            if show_overlays and zones:
                boxes = [z["box"] for z in zones]
                labels = [z["label"] for z in zones]
                display_img = overlay_bboxes(img, boxes, labels)
            with cols[i]:
                st.image(display_img, caption=f"seed={42 + i}", use_container_width=True)
                if st.button("↻", key=f"reroll_{i}"):
                    config = _build_synthesis_config()
                    gen = SyntheticDocumentGenerator(
                        template="blank", synthesis_config=config
                    )
                    new_img, new_gt = gen.generate_one(seed=1000 + i)
                    samples[i] = (new_img, new_gt)
                    st.session_state["preview_samples"] = samples
                    st.rerun()


def _panel_batch() -> None:
    st.subheader("Batch Generation")
    zones = st.session_state["synthesis_zones"]
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
        gen = SyntheticDocumentGenerator(template="blank", synthesis_config=config)
        with st.spinner(f"Generating {n_docs} documents…"):
            pairs = gen.generate(n=int(n_docs), write=True)
        st.success(f"Generated {len(pairs)} documents → {output_dir}")

        # Build in-memory ZIP
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for i, (img, gt) in enumerate(pairs):
                stem = f"doc_{i + 1:06d}"
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
    _init_state()

    _panel_template()
    st.divider()
    _panel_respondents()
    st.divider()
    _panel_zones()
    st.divider()
    _panel_actions()
    st.divider()
    _panel_preview()
    st.divider()
    _panel_batch()


main()
