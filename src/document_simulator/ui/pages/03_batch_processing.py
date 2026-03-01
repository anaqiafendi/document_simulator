"""Batch Processing — augment many images at once and download the results."""

import io
import time
import zipfile

import streamlit as st

from document_simulator.augmentation import BatchAugmenter
from document_simulator.ui.components.file_uploader import uploaded_files_to_pil
from document_simulator.ui.components.image_display import image_to_bytes
from document_simulator.ui.state.session_state import SessionStateManager

st.set_page_config(page_title="Batch Processing", page_icon="⚙️", layout="wide")
st.title("⚙️ Batch Processing")

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
    "Upload document images",
    type=["png", "jpg", "jpeg", "bmp", "tiff"],
    accept_multiple_files=True,
    key="batch_upload",
)

if uploaded_files:
    st.caption(f"{len(uploaded_files)} file(s) selected.")

# ── Run ───────────────────────────────────────────────────────────────────────

if run_btn:
    if not uploaded_files:
        st.warning("Please upload at least one image.")
    else:
        images = uploaded_files_to_pil(uploaded_files)
        state.set_batch_inputs(images)

        progress = st.progress(0.0, text="Augmenting…")
        t0 = time.time()

        batch = BatchAugmenter(augmenter=str(preset), num_workers=int(n_workers))
        results = batch.augment_batch(images, parallel=bool(parallel))

        elapsed = time.time() - t0
        progress.progress(1.0, text="Done!")

        state.set_batch_results(results)
        state.set_batch_elapsed(elapsed)

# ── Results ───────────────────────────────────────────────────────────────────

results = state.get_batch_results()
inputs = state.get_batch_inputs()
elapsed = state.get_batch_elapsed()

if results:
    n = len(results)
    c1, c2, c3 = st.columns(3)
    c1.metric("Processed", n)
    c2.metric("Time (s)", f"{elapsed:.1f}")
    c3.metric("Throughput", f"{n / elapsed:.1f} img/s" if elapsed > 0 else "—")

    # Build ZIP in memory
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for i, img in enumerate(results):
            zf.writestr(f"augmented_{i:04d}.png", image_to_bytes(img))
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
            if inputs and i < len(inputs):
                st.image(inputs[i], caption=f"orig {i + 1}", use_container_width=True)
            st.image(results[i], caption=f"aug {i + 1}", use_container_width=True)
