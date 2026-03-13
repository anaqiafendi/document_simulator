"""Typed session state accessors — pages never write raw st.session_state keys directly."""

from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st
from PIL import Image

# ── Key constants ─────────────────────────────────────────────────────────────
KEY_LAST_UPLOADED_IMAGE = "last_uploaded_image"
KEY_LAST_AUG_IMAGE = "last_aug_image"
KEY_LAST_OCR_RESULT = "last_ocr_result"
KEY_EVAL_RESULTS = "eval_results"
KEY_TRAINING_LOG = "training_log"
KEY_TRAINING_RUNNING = "training_running"
KEY_TRAINING_ERROR = "training_error"
KEY_RL_MODEL_PATH = "rl_model_path"
KEY_BATCH_INPUTS = "batch_input_images"
KEY_BATCH_RESULTS = "batch_results"
KEY_BATCH_ELAPSED = "batch_elapsed"
KEY_BATCH_MODE = "batch_mode"
KEY_BATCH_COPIES_PER_TPL = "batch_copies_per_tpl"
KEY_BATCH_TOTAL_OUTPUTS = "batch_total_outputs"
KEY_BATCH_SEED = "batch_seed"

# Catalogue mode keys
KEY_AUG_MODE = "aug_mode"
KEY_AUG_CATALOGUE_ENABLED = "aug_catalogue_enabled"
KEY_AUG_CATALOGUE_PARAMS = "aug_catalogue_params"
KEY_AUG_CATALOGUE_THUMBNAILS = "aug_catalogue_thumbnails"

_ALL_KEYS = [
    KEY_LAST_UPLOADED_IMAGE,
    KEY_LAST_AUG_IMAGE,
    KEY_LAST_OCR_RESULT,
    KEY_EVAL_RESULTS,
    KEY_TRAINING_LOG,
    KEY_TRAINING_RUNNING,
    KEY_TRAINING_ERROR,
    KEY_RL_MODEL_PATH,
    KEY_BATCH_INPUTS,
    KEY_BATCH_RESULTS,
    KEY_BATCH_ELAPSED,
    KEY_BATCH_MODE,
    KEY_BATCH_COPIES_PER_TPL,
    KEY_BATCH_TOTAL_OUTPUTS,
    KEY_BATCH_SEED,
    KEY_AUG_MODE,
    KEY_AUG_CATALOGUE_ENABLED,
    KEY_AUG_CATALOGUE_PARAMS,
    KEY_AUG_CATALOGUE_THUMBNAILS,
]


class SessionStateManager:
    """Typed wrapper around ``st.session_state`` with named accessors."""

    # ── Uploaded / augmented images ───────────────────────────────────────────

    def get_uploaded_image(self) -> Optional[Image.Image]:
        return st.session_state.get(KEY_LAST_UPLOADED_IMAGE)

    def set_uploaded_image(self, image: Image.Image) -> None:
        st.session_state[KEY_LAST_UPLOADED_IMAGE] = image

    def get_aug_image(self) -> Optional[Image.Image]:
        return st.session_state.get(KEY_LAST_AUG_IMAGE)

    def set_aug_image(self, image: Image.Image) -> None:
        st.session_state[KEY_LAST_AUG_IMAGE] = image

    # ── OCR ───────────────────────────────────────────────────────────────────

    def get_ocr_result(self) -> Optional[Dict[str, Any]]:
        return st.session_state.get(KEY_LAST_OCR_RESULT)

    def set_ocr_result(self, result: Dict[str, Any]) -> None:
        st.session_state[KEY_LAST_OCR_RESULT] = result

    # ── Evaluation ────────────────────────────────────────────────────────────

    def get_eval_results(self) -> Optional[Dict[str, Any]]:
        return st.session_state.get(KEY_EVAL_RESULTS)

    def set_eval_results(self, results: Dict[str, Any]) -> None:
        st.session_state[KEY_EVAL_RESULTS] = results

    # ── RL Training ───────────────────────────────────────────────────────────

    def is_training_running(self) -> bool:
        return bool(st.session_state.get(KEY_TRAINING_RUNNING, False))

    def set_training_running(self, running: bool) -> None:
        st.session_state[KEY_TRAINING_RUNNING] = running

    def get_training_log(self) -> List[Dict[str, Any]]:
        return st.session_state.get(KEY_TRAINING_LOG, [])

    def append_training_log(self, entry: Dict[str, Any]) -> None:
        log: List[Dict[str, Any]] = st.session_state.get(KEY_TRAINING_LOG, [])
        log.append(entry)
        st.session_state[KEY_TRAINING_LOG] = log

    def get_training_error(self) -> Optional[str]:
        return st.session_state.get(KEY_TRAINING_ERROR)

    def set_training_error(self, error: str) -> None:
        st.session_state[KEY_TRAINING_ERROR] = error

    def get_rl_model_path(self) -> Optional[Path]:
        raw = st.session_state.get(KEY_RL_MODEL_PATH)
        return Path(raw) if raw else None

    def set_rl_model_path(self, path: Path) -> None:
        st.session_state[KEY_RL_MODEL_PATH] = str(path)

    # ── Batch ─────────────────────────────────────────────────────────────────

    def get_batch_inputs(self) -> List[Image.Image]:
        return st.session_state.get(KEY_BATCH_INPUTS, [])

    def set_batch_inputs(self, images: List[Image.Image]) -> None:
        st.session_state[KEY_BATCH_INPUTS] = images

    def get_batch_results(self) -> List[Image.Image]:
        return st.session_state.get(KEY_BATCH_RESULTS, [])

    def set_batch_results(self, images: List[Image.Image]) -> None:
        st.session_state[KEY_BATCH_RESULTS] = images

    def get_batch_elapsed(self) -> float:
        return float(st.session_state.get(KEY_BATCH_ELAPSED, 0.0))

    def set_batch_elapsed(self, seconds: float) -> None:
        st.session_state[KEY_BATCH_ELAPSED] = seconds

    def get_batch_mode(self) -> str:
        """Return current batch mode: 'single', 'per_template', or 'random_sample'."""
        return st.session_state.get(KEY_BATCH_MODE, "single")

    def set_batch_mode(self, mode: str) -> None:
        """Set batch mode. Must be 'single', 'per_template', or 'random_sample'."""
        st.session_state[KEY_BATCH_MODE] = mode

    def get_batch_copies_per_tpl(self) -> int:
        return int(st.session_state.get(KEY_BATCH_COPIES_PER_TPL, 3))

    def set_batch_copies_per_tpl(self, copies: int) -> None:
        st.session_state[KEY_BATCH_COPIES_PER_TPL] = copies

    def get_batch_total_outputs(self) -> int:
        return int(st.session_state.get(KEY_BATCH_TOTAL_OUTPUTS, 20))

    def set_batch_total_outputs(self, total: int) -> None:
        st.session_state[KEY_BATCH_TOTAL_OUTPUTS] = total

    def get_batch_seed(self) -> Optional[int]:
        """Return the random seed, or None if unseeded (seed stored as 0 = unseeded)."""
        raw = st.session_state.get(KEY_BATCH_SEED, 0)
        return int(raw) if raw else None

    def set_batch_seed(self, seed: Optional[int]) -> None:
        st.session_state[KEY_BATCH_SEED] = seed or 0

    # ── Catalogue mode ────────────────────────────────────────────────────────

    def get_aug_mode(self) -> str:
        """Return current augmentation mode: "preset" or "catalogue"."""
        return st.session_state.get(KEY_AUG_MODE, "preset")

    def set_aug_mode(self, mode: str) -> None:
        """Set augmentation mode. Must be "preset" or "catalogue"."""
        st.session_state[KEY_AUG_MODE] = mode

    def get_aug_catalogue_enabled(self) -> Dict[str, bool]:
        """Return dict mapping aug_name -> enabled (bool)."""
        return st.session_state.get(KEY_AUG_CATALOGUE_ENABLED, {})

    def set_aug_catalogue_enabled(self, enabled: Dict[str, bool]) -> None:
        st.session_state[KEY_AUG_CATALOGUE_ENABLED] = enabled

    def get_aug_catalogue_params(self) -> Dict[str, Dict]:
        """Return dict mapping aug_name -> {param_key: value}."""
        return st.session_state.get(KEY_AUG_CATALOGUE_PARAMS, {})

    def set_aug_catalogue_params(self, params: Dict[str, Dict]) -> None:
        st.session_state[KEY_AUG_CATALOGUE_PARAMS] = params

    def get_aug_catalogue_thumbnails(self) -> Dict[str, bytes]:
        """Return dict mapping aug_name -> PNG bytes of cached thumbnail."""
        return st.session_state.get(KEY_AUG_CATALOGUE_THUMBNAILS, {})

    def set_aug_catalogue_thumbnails(self, thumbnails: Dict[str, bytes]) -> None:
        st.session_state[KEY_AUG_CATALOGUE_THUMBNAILS] = thumbnails

    # ── Utility ───────────────────────────────────────────────────────────────

    def clear(self) -> None:
        """Reset all managed keys."""
        for key in _ALL_KEYS:
            st.session_state.pop(key, None)
