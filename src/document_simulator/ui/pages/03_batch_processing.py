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
    "**How to use:** Upload one or more document images or PDFs. "
    "Choose an augmentation mode in the sidebar: **Single template** (one augmented copy per "
    "upload), **N×M** (M copies of every template), or **M-total** (M outputs sampled randomly "
    "from your templates). Click **Run Batch Augmentation** and download the ZIP."
)

state = SessionStateManager()

# ── Sidebar ───────────────────────────────────────────────────────────────────

_MODE_SINGLE = "Single template"
_MODE_PER_TPL = "N×M (copies per template)"
_MODE_RANDOM = "M-total (random sample)"

with st.sidebar:
    preset = st.selectbox(
        "Pipeline preset", ["light", "medium", "heavy"], index=1, key="batch_preset"
    )
    n_workers = st.slider("Workers", min_value=1, max_value=8, value=4, key="batch_workers")
    parallel = st.checkbox("Parallel processing", value=True, key="batch_parallel")

    st.divider()

    batch_mode_label = st.radio(
        "Augmentation mode",
        [_MODE_SINGLE, _MODE_PER_TPL, _MODE_RANDOM],
        index=0,
        key="batch_mode_radio",
        help=(
            "**Single template**: one augmented copy per uploaded image.  \n"
            "**N×M**: M copies of each template (N templates × M copies = N×M outputs).  \n"
            "**M-total**: M outputs sampled randomly from your N templates."
        ),
    )

    copies_per_tpl = 3
    total_outputs = 20
    seed_value = 0

    if batch_mode_label == _MODE_PER_TPL:
        copies_per_tpl = int(
            st.number_input(
                "Copies per template (M)",
                min_value=1,
                max_value=100,
                value=3,
                step=1,
                key="batch_copies_per_tpl",
            )
        )
    elif batch_mode_label == _MODE_RANDOM:
        total_outputs = int(
            st.number_input(
                "Total outputs (M)",
                min_value=1,
                max_value=500,
                value=20,
                step=1,
                key="batch_total_outputs",
            )
        )
        seed_value = int(
            st.number_input(
                "Random seed (0 = unseeded)",
                min_value=0,
                max_value=2**31 - 1,
                value=0,
                step=1,
                key="batch_seed",
            )
        )
        if total_outputs > 50:
            st.warning(f"Generating {total_outputs} outputs may be slow.")

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
    st.caption(f"{n_files} file(s) selected.")

# ── Run ───────────────────────────────────────────────────────────────────────


def _build_zip_multi(results_with_stems) -> bytes:
    """Build an in-memory ZIP from (image, stem) pairs.

    For N×M and M-total modes, multiple entries may share the same stem.
    A per-stem counter ensures unique filenames.
    """
    buf = io.BytesIO()
    stem_counter: dict = {}
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for img, stem in results_with_stems:
            count = stem_counter.get(stem, 0)
            stem_counter[stem] = count + 1
            if batch_mode_label == _MODE_RANDOM:
                filename = f"{stem}_{count:04d}.png"
            else:
                filename = f"{stem}_{count:03d}.png"
            zf.writestr(filename, image_to_bytes(img))
    buf.seek(0)
    return buf.getvalue()


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

        if batch_mode_label == _MODE_SINGLE:
            # Existing single-template path (unchanged behaviour)
            results_images = batch.augment_batch(images, parallel=bool(parallel))
            results_with_stems = None  # use label-based ZIP below
        elif batch_mode_label == _MODE_PER_TPL:
            pairs = batch.augment_multi_template(
                images,
                mode="per_template",
                copies_per_template=copies_per_tpl,
                parallel=bool(parallel),
            )
            results_images = [img for img, _ in pairs]
            results_with_stems = pairs
        else:  # M-total
            seed_arg = seed_value if seed_value > 0 else None
            pairs = batch.augment_multi_template(
                images,
                mode="random_sample",
                total_outputs=total_outputs,
                seed=seed_arg,
                parallel=bool(parallel),
            )
            results_images = [img for img, _ in pairs]
            results_with_stems = pairs

        elapsed = time.time() - t0
        progress.progress(1.0, text="Done!")

        state.set_batch_results(results_images)
        state.set_batch_elapsed(elapsed)
        st.session_state["_batch_results_with_stems"] = results_with_stems

        n_files = len(uploaded_files)
        n_pages = len(labels)
        if n_pages != n_files:
            st.caption(f"{n_files} file(s) selected — {n_pages} pages total.")

# ── Results ───────────────────────────────────────────────────────────────────

results = state.get_batch_results()
inputs = state.get_batch_inputs()
elapsed = state.get_batch_elapsed()
labels = st.session_state.get("batch_input_labels", [])
results_with_stems = st.session_state.get("_batch_results_with_stems")

if results:
    n = len(results)
    c1, c2, c3 = st.columns(3)
    c1.metric("Processed", n)
    c2.metric("Time (s)", f"{elapsed:.1f}")
    c3.metric("Throughput", f"{n / elapsed:.1f} img/s" if elapsed > 0 else "—")

    # Build ZIP in memory
    if results_with_stems is not None:
        # N×M or M-total: use stem-based naming
        zip_bytes = _build_zip_multi(results_with_stems)
    else:
        # Single-template: use original label-based naming
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
                    stem = safe_name.rsplit(".", 1)[0] if "." in safe_name else safe_name
                    filename = f"{stem}.png"
                else:
                    filename = f"augmented_{i:04d}.png"
                zf.writestr(filename, image_to_bytes(img))
        buf.seek(0)
        zip_bytes = buf.getvalue()

    st.download_button(
        "Download all as ZIP",
        data=zip_bytes,
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
