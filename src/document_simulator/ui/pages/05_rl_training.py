"""RL Training — configure, launch, and monitor PPO training in a background thread."""

import threading
import time
from pathlib import Path
from typing import Any, Dict

import streamlit as st

from document_simulator.ui.components.metrics_charts import reward_line
from document_simulator.ui.state.session_state import SessionStateManager

st.set_page_config(page_title="RL Training", page_icon="🤖", layout="wide")
st.title("🤖 RL Training")
st.info(
    "**How to use:** Point **Dataset directory** at a folder of annotated document/JSON pairs "
    "(the same format used by the Evaluation Dashboard — the **Synthetic Generator** produces "
    "these automatically). Configure hyperparameters in the sidebar, then click **Start "
    "Training**. A PPO agent learns which augmentation parameters maximise OCR quality while "
    "preserving visual realism. Training runs in a background thread — the reward chart "
    "updates live. Click **Stop** to end early; checkpoints are saved automatically."
)

state = SessionStateManager()

# ── Initialise persistent threading objects in session_state ──────────────────
if "_rl_stop_event" not in st.session_state:
    st.session_state["_rl_stop_event"] = threading.Event()

_stop_event: threading.Event = st.session_state["_rl_stop_event"]

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    data_dir = st.text_input("Dataset directory", "./data/train", key="rl_data_dir")
    lr = st.number_input("Learning rate", value=3e-4, format="%e", key="rl_lr")
    batch_size = st.number_input("Batch size", value=64, step=16, min_value=16, key="rl_bs")
    n_steps = st.number_input("N steps", value=2048, step=256, min_value=256, key="rl_nsteps")
    num_envs = st.slider("Num environments", 1, 8, 4, key="rl_envs")
    total_steps = st.number_input(
        "Total timesteps", value=100_000, step=10_000, min_value=1_000, key="rl_total"
    )
    ckpt_freq = st.number_input(
        "Checkpoint frequency", value=10_000, step=1_000, min_value=1_000, key="rl_ckpt"
    )

    st.divider()
    btn_col1, btn_col2 = st.columns(2)
    start_btn = btn_col1.button(
        "▶ Start", type="primary", disabled=state.is_training_running(), key="rl_start"
    )
    stop_btn = btn_col2.button(
        "⏹ Stop", disabled=not state.is_training_running(), key="rl_stop"
    )

    st.divider()
    save_btn = st.button(
        "💾 Save Model",
        disabled=state.is_training_running() or state.get_rl_model_path() is None,
        key="rl_save",
    )
    model_upload = st.file_uploader("📂 Load Model (.zip)", type=["zip"], key="rl_load")


# ── Background training thread ────────────────────────────────────────────────


def _training_thread(config_kwargs: Dict[str, Any], stop_event: threading.Event) -> None:
    """Runs PPO training; appends log dicts to session_state after each checkpoint."""
    from document_simulator.rl import RLConfig, RLTrainer

    try:
        config = RLConfig(**config_kwargs)
        trainer = RLTrainer(config)

        # Monkey-patch a lightweight logging step into PPO's learn() via a callback
        from stable_baselines3.common.callbacks import BaseCallback

        log_ref = []  # use list so the closure can mutate it

        class _LogCallback(BaseCallback):
            def __init__(self):
                super().__init__()
                self._last_step = 0

            def _on_step(self) -> bool:
                if stop_event.is_set():
                    return False
                if self.num_timesteps - self._last_step >= int(ckpt_freq):
                    self._last_step = self.num_timesteps
                    ep_rew = self.locals.get("infos", [{}])
                    mean_rew = float(
                        sum(i.get("episode", {}).get("r", 0) for i in ep_rew) / max(len(ep_rew), 1)
                    )
                    entry: Dict[str, Any] = {"step": self.num_timesteps, "reward": mean_rew}
                    state.append_training_log(entry)
                return True

        callback = _LogCallback()
        trainer.model.learn(
            total_timesteps=int(total_steps),
            callback=callback,
            reset_num_timesteps=True,
        )

        saved_path = trainer.save()
        state.set_rl_model_path(saved_path)

    except Exception as exc:
        state.set_training_error(str(exc))
    finally:
        state.set_training_running(False)


# ── Button handlers ───────────────────────────────────────────────────────────

if start_btn:
    _stop_event.clear()
    st.session_state["training_log"] = []
    state.set_training_running(True)
    state.set_training_error("")  # clear old errors

    config_kwargs: Dict[str, Any] = {
        "train_data_dir": Path(data_dir) if data_dir else None,
        "learning_rate": float(lr),
        "batch_size": int(batch_size),
        "n_steps": int(n_steps),
        "num_envs": int(num_envs),
        "checkpoint_freq": int(ckpt_freq),
    }
    t = threading.Thread(
        target=_training_thread,
        args=(config_kwargs, _stop_event),
        daemon=True,
        name="RLTrainingThread",
    )
    t.start()
    st.rerun()

if stop_btn:
    _stop_event.set()

# ── Live display ───────────────────────────────────────────────────────────────

log = state.get_training_log()
running = state.is_training_running()
error = state.get_training_error()

if error:
    st.error(f"Training error: {error}")

if running:
    st.info("⏳ Training in progress…")

if log:
    latest = log[-1]
    pct = min(latest["step"] / max(int(total_steps), 1), 1.0)
    st.progress(pct, text=f"Step {latest['step']:,} / {int(total_steps):,}")

    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("Step", f"{latest['step']:,}")
    metric_col2.metric("Reward", f"{latest.get('reward', 0.0):.4f}")
    if "cer" in latest:
        metric_col3.metric("CER", f"{latest['cer']:.4f}")
    if "confidence" in latest:
        st.metric("Confidence", f"{latest['confidence']:.4f}")

    st.plotly_chart(reward_line(log), use_container_width=True)

elif not running:
    st.info(
        "Configure training parameters in the sidebar and click **▶ Start**. "
        "Training runs in a background thread so the UI remains responsive."
    )

# ── Saved model info ───────────────────────────────────────────────────────────

model_path = state.get_rl_model_path()
if model_path and model_path.exists():
    st.success(f"Model saved: `{model_path}`")

# Auto-rerun while training to pick up new log entries
if running:
    time.sleep(2)
    st.rerun()
