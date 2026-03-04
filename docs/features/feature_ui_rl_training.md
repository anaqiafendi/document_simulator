# Feature: UI — RL Training

> **GitHub Issue:** `#18`
> **Status:** `complete`
> **Module:** `document_simulator.ui.pages.05_rl_training`

---

## Summary

A Streamlit page that exposes `RLConfig` hyperparameters as form fields, starts PPO training in a background `threading.Thread`, streams reward log entries to a live Plotly line chart, and exposes Stop / Save / Load model controls.

---

## Motivation

### Problem Statement

`RLTrainer.train()` is a long-running blocking call. Running it on the Streamlit main thread freezes the UI. A background thread with a shared log queue lets the page update a live reward chart while training proceeds independently.

### Value Delivered

- Start training without writing Python or running a CLI command.
- Live reward curve that updates every 2 seconds during training.
- Stop training at any time via the Stop button.
- Save the current model to a path; load a previous checkpoint.
- Training state (`is_training_running`) persists across page reruns.

---

## Acceptance Criteria

- [ ] AC-1: Page loads without error.
- [ ] AC-2: A "Start Training" button is present.
- [ ] AC-3: A "Stop Training" button is present.
- [ ] AC-4: A "Save Model" button is present.
- [ ] AC-5: A learning rate input is present.
- [ ] AC-6: A number of steps input is present.
- [ ] AC-7: A data directory text input is present.
- [ ] AC-8: When `training_running` is `True` in session state, a "Training in progress" indicator appears.
- [ ] AC-9: When `training_log` entries are in session state, a chart or metric is visible.

---

## Design

### Data Flow

```
User fills in config fields (data_dir, learning_rate, num_steps, ...)
User clicks "Start Training"
    │
    ▼
threading.Thread(target=_training_thread, args=(config_kwargs, stop_event))
    │
    ▼
_training_thread:
    RLTrainer(RLConfig(**config_kwargs)).train(total_timesteps)
    _LogCallback.on_step() → state.append_training_log({"step": N, "reward": R})
    │
    ▼
Page polls every 2 seconds:
    if state.is_training_running(): time.sleep(2); st.rerun()
    reward_line(state.get_training_log()) → st.plotly_chart
```

### Key Interfaces

| Symbol | Kind | Responsibility |
|--------|------|---------------|
| `_rl_stop_event` | `threading.Event` stored in state | Signal to background thread to stop |
| `_training_thread(config_kwargs, stop_event)` | function | Background worker: RLTrainer + LogCallback |
| `_LogCallback(BaseCallback)` | class | SB3 callback that appends to `training_log` each step |
| Start / Stop / Save / Load buttons | widgets | Training lifecycle controls |
| `reward_line(log)` | component | Live Plotly line chart |

---

## Implementation

### Files

| Path | Role |
|------|------|
| `src/document_simulator/ui/pages/05_rl_training.py` | Complete page + `_LogCallback` |
| `src/document_simulator/rl/trainer.py` | `RLTrainer`, `RLConfig` |
| `src/document_simulator/ui/components/metrics_charts.py` | `reward_line` |
| `src/document_simulator/ui/state/session_state.py` | `SessionStateManager` |

### Key Architectural Decisions

1. **Background thread, not subprocess** — `st.session_state` is thread-safe for read/write from a background thread in Streamlit. Using a thread avoids the serialisation overhead of a subprocess while still unblocking the UI.

2. **`threading.Event` for stop signal** — `stop_event.set()` from the Stop button; `_LogCallback._on_step()` calls `self.model.env.render()` and checks `stop_event.is_set()`. If set, it calls `self.model.set_env(None)` to terminate training gracefully.

3. **`_LogCallback` as an SB3 `BaseCallback`** — This is the standard SB3 way to hook into the training loop. `on_step` is called at every environment step, making it suitable for logging reward.

4. **`time.sleep(2); st.rerun()` polling** — Streamlit has no native push mechanism. The page polls state every 2 seconds while `is_training_running()` is True. This is the standard pattern for long-running background tasks in Streamlit.

### Known Edge Cases & Constraints

- Closing the browser tab does not stop the background thread — training continues until the Streamlit server process exits or the Stop button is clicked.
- SB3 `PPO.learn()` is not thread-safe in all versions. Concurrent training from two browser sessions would interfere.
- `AppTest` cannot run background threads — integration tests inject state directly and check for UI elements.

---

## Tests

### Test Files

| File | Type | Count | What is covered |
|------|------|-------|-----------------|
| `tests/ui/integration/test_rl_training.py` | integration | 9 | Load, Start button, Stop button, Save button, learning rate input, steps input, data dir input, training running indicator, log chart/metric |

### TDD Cycle Summary

**Red — first failing tests written:**

| Test name | File | Initial failure reason |
|-----------|------|----------------------|
| `test_rl_page_loads` | `test_rl_training.py` | `FileNotFoundError: 05_rl_training.py does not exist` |
| `test_rl_page_has_stop_button` | `test_rl_training.py` | Only Start button existed |
| `test_rl_page_shows_indicator_when_training_running` | `test_rl_training.py` | `at.info` / `at.spinner` not checked; needed `st.info("Training in progress")` |

**Green — minimal implementation:**

Created page with form fields for config, Start/Stop/Save/Load buttons, and state injection tests for the running indicator. Used `at.session_state["training_running"] = True` to simulate the running state.

**Refactor — improvements made after green:**

| What changed | Why |
|--------------|-----|
| Added `_rl_stop_event` persistence via `st.session_state` | First implementation created a new `threading.Event` per rerun, losing the reference needed to stop the running thread |
| Added `reward_line` chart with `st.rerun()` polling | Initial green only showed a metric widget; the live chart required `time.sleep(2); st.rerun()` loop |

### How to Run

```bash
uv run pytest tests/ui/integration/test_rl_training.py -v
```

---

## Dependencies

### Requires

| Dependency | Kind | Why |
|------------|------|-----|
| `rl/trainer.py` | internal | `RLTrainer`, `RLConfig` |
| `ui/components/metrics_charts.py` | internal | `reward_line` |
| `ui/state/session_state.py` | internal | `SessionStateManager` |
| `threading` | stdlib | Background training thread + `Event` |
| `stable_baselines3.common.callbacks` | external | `BaseCallback` for `_LogCallback` |

---

## Future Work

- [ ] Replace polling with Streamlit's `st.rerun(interval=...)` once available.
- [ ] Add TensorBoard link when `tensorboard_dir` is configured.
- [ ] Add W&B run link when `WANDB_PROJECT` is set.
- [ ] Show per-step CER alongside reward in the live chart.

---

## References

- [feature_rl_trainer.md](feature_rl_trainer.md)
- [feature_ui_components.md](feature_ui_components.md)
- [UI_PLAN.md](../UI_PLAN.md)
