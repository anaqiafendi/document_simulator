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

    # ── Utility ───────────────────────────────────────────────────────────────

    def clear(self) -> None:
        """Reset all managed keys."""
        for key in _ALL_KEYS:
            st.session_state.pop(key, None)
