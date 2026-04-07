"""Synthetic Document Generator — select a template style and generate filled documents.

Exposes:
- Template style selector (receipt/thermal, receipt/a4) via the TemplateRegistry
- Min/max line item count controls for the RepeatingSection
- Template structure preview (section list + estimated height range)
- Seed control and one-shot generate button
- Download generated PNG
- Link to the full React zone editor for advanced use
"""

from __future__ import annotations

import io

import streamlit as st
from PIL import Image

from document_simulator.synthesis.document_template import DocumentTemplate
from document_simulator.synthesis.sections import RepeatingSection, StaticSection
from document_simulator.synthesis.template_registry import TemplateRegistry
from document_simulator.synthesis.templates.receipt_a4 import receipt_a4_template
from document_simulator.synthesis.templates.receipt_thermal import receipt_thermal_template
from document_simulator.ui.state.session_state import SessionStateManager

st.set_page_config(page_title="Synthetic Generator", page_icon="📄", layout="wide")
st.title("📄 Synthetic Document Generator")
st.info(
    "Generate filled synthetic document images from a built-in template. "
    "Pick a **template style**, adjust the number of line items, set a seed, "
    "and click **Generate**. For advanced zone editing, use the React zone editor below."
)

state = SessionStateManager()

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_REGISTRY = TemplateRegistry()
_REGISTRY.register("receipt", "thermal", receipt_thermal_template)
_REGISTRY.register("receipt", "a4", receipt_a4_template)

# Session state keys specific to this page
_KEY_GEN_IMAGE = "synth_gen_image"
_KEY_GEN_SEED = "synth_gen_seed"
_KEY_GEN_NUM_ITEMS = "synth_gen_num_items"
_KEY_GEN_DOC_TYPE = "synth_gen_doc_type"
_KEY_GEN_STYLE = "synth_gen_style"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_repeating_sections(template: DocumentTemplate) -> list[RepeatingSection]:
    return [s for s in template.sections if isinstance(s, RepeatingSection)]


def _section_table_rows(template: DocumentTemplate, num_items: int) -> list[dict]:
    """Build a summary row per section for the structure preview."""
    rows = []
    for section in template.sections:
        if isinstance(section, RepeatingSection):
            lo, hi = section.num_rows_range
            rows.append(
                {
                    "Section": section.section_id,
                    "Type": "Repeating",
                    "Rows (this run)": num_items,
                    "Range": f"{lo}–{hi}",
                    "Est. height (px)": section.computed_height(num_items),
                }
            )
        elif isinstance(section, StaticSection):
            rows.append(
                {
                    "Section": section.section_id,
                    "Type": "Static",
                    "Rows (this run)": "—",
                    "Range": "—",
                    "Est. height (px)": round(section.height),
                }
            )
        else:
            rows.append(
                {
                    "Section": section.section_id,
                    "Type": "Unknown",
                    "Rows (this run)": "—",
                    "Range": "—",
                    "Est. height (px)": round(section.height),
                }
            )
    return rows


def _estimated_height_range(template: DocumentTemplate) -> tuple[int, int]:
    """Return (min_height, max_height) across all sections."""
    static_h = sum(
        s.height for s in template.sections if isinstance(s, StaticSection)
    )
    min_h = static_h
    max_h = static_h
    for section in template.sections:
        if isinstance(section, RepeatingSection):
            lo, hi = section.num_rows_range
            min_h += section.computed_height(lo)
            max_h += section.computed_height(hi)
    return int(round(min_h)), int(round(max_h))


def _generate_image(
    template: DocumentTemplate,
    num_items: int,
    seed: int,
) -> Image.Image:
    """Run the generator pipeline and return a PIL image."""
    from document_simulator.synthesis.generator import SyntheticDocumentGenerator

    synthesis_config = template.to_synthesis_config(
        num_line_items=num_items,
        seed=seed,
    )
    gen = SyntheticDocumentGenerator(
        template="blank",
        synthesis_config=synthesis_config,
    )
    img, _ = gen.generate_one(seed=seed)
    return img


# ---------------------------------------------------------------------------
# Sidebar — controls
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Template Settings")

    doc_types = _REGISTRY.list_types()
    selected_doc_type = st.selectbox(
        "Document type",
        options=doc_types,
        index=0,
        key=_KEY_GEN_DOC_TYPE,
        help="The category of document to generate.",
    )

    styles = _REGISTRY.list_styles(selected_doc_type)
    selected_style = st.selectbox(
        "Style",
        options=styles,
        index=0,
        key=_KEY_GEN_STYLE,
        help="Visual variant for the selected document type.",
    )

    template = _REGISTRY.get(selected_doc_type, selected_style)
    repeating = _get_repeating_sections(template)

    st.divider()
    st.subheader("Line Items")

    if repeating:
        rep = repeating[0]  # Primary repeating section
        lo, hi = rep.num_rows_range
        num_items = st.slider(
            "Number of line items",
            min_value=lo,
            max_value=hi,
            value=min(lo + 2, hi),
            step=1,
            key=_KEY_GEN_NUM_ITEMS,
            help=f"Controls row count for the '{rep.section_id}' section (range {lo}–{hi}).",
        )
    else:
        num_items = 0
        st.caption("This template has no repeating sections.")

    st.divider()
    st.subheader("Reproducibility")

    seed = st.number_input(
        "Seed",
        min_value=0,
        max_value=9999,
        value=42,
        step=1,
        key=_KEY_GEN_SEED,
        help="Set a fixed seed for reproducible output. Different seeds produce different fake data.",
    )

    generate_clicked = st.button("Generate document", type="primary", use_container_width=True)

# ---------------------------------------------------------------------------
# Main area — template preview + generated image
# ---------------------------------------------------------------------------

col_preview, col_output = st.columns([1, 1], gap="large")

with col_preview:
    st.subheader("Template structure")

    style_meta = {
        "receipt / thermal": "58mm wide thermal receipt (fast-food / transit)",
        "receipt / a4": "A4 portrait invoice-style receipt (hotel / airline)",
    }
    desc = style_meta.get(f"{selected_doc_type} / {selected_style}", "")
    if desc:
        st.caption(desc)

    rows = _section_table_rows(template, num_items if repeating else 0)
    st.dataframe(rows, use_container_width=True, hide_index=True)

    min_h, max_h = _estimated_height_range(template)
    st.metric("Min document height (px)", min_h)
    st.metric("Max document height (px)", max_h)
    if repeating:
        effective_h = min_h - _get_repeating_sections(template)[0].computed_height(
            _get_repeating_sections(template)[0].num_rows_range[0]
        ) + _get_repeating_sections(template)[0].computed_height(num_items)
        st.metric("This run — estimated height (px)", int(round(effective_h)))

with col_output:
    st.subheader("Generated document")

    # Run generation when button is clicked
    if generate_clicked:
        with st.spinner("Generating…"):
            try:
                img = _generate_image(template, num_items=num_items if repeating else None, seed=seed)
                st.session_state[_KEY_GEN_IMAGE] = img
            except Exception as exc:  # noqa: BLE001
                st.error(f"Generation failed: {exc}")
                st.session_state.pop(_KEY_GEN_IMAGE, None)

    # Show the generated image from state
    generated: Image.Image | None = st.session_state.get(_KEY_GEN_IMAGE)
    if generated is not None:
        # Scale for display — cap at 600px wide
        display_w = min(generated.width, 600)
        ratio = display_w / generated.width
        display_h = int(generated.height * ratio)
        display_img = generated.resize((display_w, display_h), Image.LANCZOS)
        st.image(display_img, caption=f"{selected_doc_type}/{selected_style} — seed {seed}")

        buf = io.BytesIO()
        generated.save(buf, format="PNG")
        st.session_state["synth_download_ready"] = True
        st.download_button(
            label="Download PNG",
            data=buf.getvalue(),
            file_name=f"synth_{selected_doc_type}_{selected_style}_seed{seed}.png",
            mime="image/png",
        )
    else:
        st.caption("Click **Generate document** in the sidebar to create an image.")

# ---------------------------------------------------------------------------
# Advanced zone editor link
# ---------------------------------------------------------------------------

st.divider()
st.markdown(
    "**Advanced use:** For custom zone layout, open the React zone editor. "
    "Start the API server with `uv run python -m document_simulator.api`, then:"
)
st.markdown(
    "[Open Zone Editor →](http://localhost:8000)",
    unsafe_allow_html=True,
)
