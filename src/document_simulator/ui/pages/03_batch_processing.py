"""Batch Processing — augment many images at once and download the results."""

import io
import time
import zipfile

import streamlit as st

from document_simulator.augmentation import BatchAugmenter
from document_simulator.ui.components.file_uploader import (
    expand_uploads_to_pil,
    list_sample_files,
    load_path_as_pil_pages,
)
from document_simulator.ui.components.image_display import image_to_bytes
from document_simulator.ui.state.session_state import SessionStateManager

st.set_page_config(page_title="Batch Processing", page_icon="⚙️", layout="wide")
st.title("⚙️ Batch Processing")
st.info(
    "**How to use:** Upload one or more document images or PDFs (PDFs are expanded "
    "page-by-page into the batch). Select a pipeline preset and worker count in the "
    "sidebar, then click **Run Batch Augmentation**. Download the results as a ZIP — "
    "each file is named after its source (e.g. `report_p2.png` for page 2 of `report.pdf`). "
    "Use this page to generate augmented training data in bulk."
)

state = SessionStateManager()

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    preset = st.selectbox(
        "Pipeline preset", ["light", "medium", "heavy"], index=1, key="batch_preset"
    )
    n_workers = st.slider("Workers", min_value=1, max_value=8, value=4, key="batch_workers")
    parallel = st.checkbox("Parallel processing", value=True, key="batch_parallel")
    run_btn = st.button("Run Batch Augmentation", type="primary")

# ── Upload ────────────────────────────────────────────────────────────────────

uploaded_files = st.file_uploader(
    "Upload document images or PDFs",
    type=["png", "jpg", "jpeg", "bmp", "tiff", "pdf"],
    accept_multiple_files=True,
    key="batch_upload",
)

# ── Sample data ───────────────────────────────────────────────────────────────

_batch_samples = list_sample_files("batch_processing", (".pdf", ".png", ".jpg", ".jpeg", ".bmp", ".tiff"))
if _batch_samples:
    st.divider()
    _batch_sample_names = [p.name for p in _batch_samples]
    _bs_col1, _bs_col2 = st.columns([3, 1])
    _bs_selected = _bs_col1.selectbox(
        "Or choose a sample document",
        options=["— select —"] + _batch_sample_names,
        key="batch_sample_select",
    )
    if _bs_col2.button("Load sample", key="batch_load_sample") and _bs_selected != "— select —":
        _bs_path = _batch_samples[_batch_sample_names.index(_bs_selected)]
        try:
            _bs_pages = load_path_as_pil_pages(_bs_path)
            _bs_labels = (
                [f"{_bs_selected} — page {i+1}" for i in range(len(_bs_pages))]
                if _bs_path.suffix.lower() == ".pdf" and len(_bs_pages) > 1
                else [_bs_selected]
            )
            state.set_batch_inputs(_bs_pages)
            st.session_state["batch_input_labels"] = _bs_labels
            st.rerun()
        except ImportError as e:
            st.error(str(e))

if uploaded_files:
    n_files = len(uploaded_files)
    # Count total pages (PDFs expand to multiple pages)
    n_pages = sum(
        len([1])  # placeholder; actual expansion happens on run
        for _ in uploaded_files
    )
    st.caption(f"{n_files} file(s) selected.")

# ── Run ───────────────────────────────────────────────────────────────────────

if run_btn:
    if not uploaded_files:
        st.warning("Please upload at least one image.")
    else:
        images, labels = expand_uploads_to_pil(uploaded_files)
        state.set_batch_inputs(images)
        st.session_state["batch_input_labels"] = labels

        progress = st.progress(0.0, text="Augmenting…")
        t0 = time.time()

        batch = BatchAugmenter(augmenter=str(preset), num_workers=int(n_workers))
        results = batch.augment_batch(images, parallel=bool(parallel))

        elapsed = time.time() - t0
        progress.progress(1.0, text="Done!")

        state.set_batch_results(results)
        state.set_batch_elapsed(elapsed)

        n_files = len(uploaded_files)
        n_pages = len(labels)
        if n_pages != n_files:
            st.caption(f"{n_files} file(s) selected — {n_pages} pages total.")

# ── Results ───────────────────────────────────────────────────────────────────

results = state.get_batch_results()
inputs = state.get_batch_inputs()
elapsed = state.get_batch_elapsed()
labels = st.session_state.get("batch_input_labels", [])

if results:
    n = len(results)
    c1, c2, c3 = st.columns(3)
    c1.metric("Processed", n)
    c2.metric("Time (s)", f"{elapsed:.1f}")
    c3.metric("Throughput", f"{n / elapsed:.1f} img/s" if elapsed > 0 else "—")

    # Build ZIP in memory — use labels for filenames when available
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for i, img in enumerate(results):
            if i < len(labels):
                safe_name = (
                    labels[i]
                    .replace(" — page ", "_p")
                    .replace("/", "_")
                    .replace("\\", "_")
                )
                # Strip original extension and add .png
                stem = safe_name.rsplit(".", 1)[0] if "." in safe_name else safe_name
                filename = f"{stem}.png"
            else:
                filename = f"augmented_{i:04d}.png"
            zf.writestr(filename, image_to_bytes(img))
    buf.seek(0)

    st.download_button(
        "Download all as ZIP",
        data=buf.getvalue(),
        file_name="augmented_batch.zip",
        mime="application/zip",
    )

    # Thumbnail grid (up to 8 pairs)
    st.subheader("Preview (original / augmented)")
    display_n = min(n, 8)
    cols = st.columns(min(display_n, 4))
    for i in range(display_n):
        with cols[i % 4]:
            caption_orig = labels[i] if i < len(labels) else f"orig {i + 1}"
            caption_aug = f"aug — {labels[i]}" if i < len(labels) else f"aug {i + 1}"
            if inputs and i < len(inputs):
                st.image(inputs[i], caption=caption_orig, use_container_width=True)
            st.image(results[i], caption=caption_aug, use_container_width=True)
