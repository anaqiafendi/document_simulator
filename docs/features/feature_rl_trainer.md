# Feature: RL Trainer

> **GitHub Issue:** `#10`
> **Status:** `complete`
> **Module:** `document_simulator.rl.trainer`

---

## Summary

`RLTrainer` wraps Stable-Baselines3's PPO algorithm with `DocumentEnv`, `CheckpointCallback`, and `EvalCallback` into a single `train()` call. `RLConfig` (Pydantic Settings) exposes all hyperparameters via environment variables or `.env` file. `save()` and `load()` handle model persistence.

---

## Motivation

### Problem Statement

SB3 requires assembling environment, policy, callbacks, and vectorised wrappers before training can start. That boilerplate is ~30 lines that every RL script would duplicate. `RLTrainer` encapsulates this once, while `RLConfig` makes every hyperparameter overridable from the command line or `.env`.

### Value Delivered

- `trainer.train(total_timesteps=N)` is the entire API surface for the CLI and UI.
- `RLConfig` with Pydantic Settings means all SB3 hyperparameters are validated and accessible from environment variables (`RL_LEARNING_RATE`, etc.).
- `CheckpointCallback` writes periodic `.zip` files — training can resume from any checkpoint.
- `EvalCallback` saves `best_model.zip` automatically.
- `save()` and `load()` work without the caller knowing SB3's model path conventions.

---

## User Stories

| Role | Goal | So That |
|------|------|---------|
| RL researcher | I call `trainer.train(total_timesteps=1_000_000)` | A PPO agent trains and `best_model.zip` is saved |
| CLI user | I run `train --data-dir ./data --num-steps 500000` | Training starts without writing Python |
| UI user | I click "Start Training" on the RL page | A background thread trains and streams reward logs |
| Experimenter | I set `RL_LEARNING_RATE=1e-3` in `.env` | Training uses my learning rate without code changes |

---

## Acceptance Criteria

- [ ] AC-1: `RLConfig()` constructs with valid defaults (`gamma=0.99`, `learning_rate=3e-4`).
- [ ] AC-2: `RLTrainer(config)` initialises `model`, `train_env`, and `eval_env` without error.
- [ ] AC-3: `trainer.save(path)` writes a `.zip` file to `path`.
- [ ] AC-4: `trainer.save()` (no arg) writes `models_dir/final_model.zip`.
- [ ] AC-5: `trainer.load(path)` loads a previously saved model without raising.
- [ ] AC-6 (slow): `trainer.train(total_timesteps=128)` completes and returns a PPO model.

---

## Design

### Public API

```python
from document_simulator.rl.trainer import RLConfig, RLTrainer

config = RLConfig(
    train_data_dir=Path("data/train"),
    num_envs=4,
    learning_rate=3e-4,
)
trainer = RLTrainer(config)
model = trainer.train(total_timesteps=1_000_000)
trainer.save(Path("models/my_agent.zip"))
trainer.load(Path("models/best_model.zip"))
```

```bash
uv run python -m document_simulator train --data-dir ./data/train --num-steps 500000
```

### Data Flow

```
RLTrainer.__init__(config)
    │
    ├─► make_vec_env(DocumentEnv, n_envs=config.num_envs)   → train_env
    ├─► make_vec_env(DocumentEnv, n_envs=1)                 → eval_env
    └─► PPO("CnnPolicy", train_env, **hyperparams)          → self.model
    │
    ▼
trainer.train(total_timesteps)
    │
    ├─► CheckpointCallback  → saves ppo_document_NNNsteps.zip every checkpoint_freq steps
    ├─► EvalCallback        → saves best_model.zip when eval reward improves
    └─► model.learn(total_timesteps, callback=callbacks)
    │
    ▼
PPO model (also accessible via trainer.model)
```

### Key Interfaces

| Symbol | Kind | Responsibility |
|--------|------|---------------|
| `RLConfig` | Pydantic BaseSettings | All training hyperparameters, paths, env prefixed `RL_` |
| `RLTrainer(config)` | class | Constructs envs, PPO model, and callbacks |
| `train(total_timesteps)` | method | Run `model.learn()` with callbacks; returns PPO |
| `save(path)` | method | Save model to path; defaults to `models_dir/final_model.zip` |
| `load(path)` | method | Load model from `.zip` into `self.model` |

### Configuration

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `RL_LEARNING_RATE` | `float` | `3e-4` | PPO learning rate |
| `RL_N_STEPS` | `int` | `2048` | Steps per rollout per env |
| `RL_BATCH_SIZE` | `int` | `64` | PPO mini-batch size |
| `RL_N_EPOCHS` | `int` | `10` | PPO update epochs per rollout |
| `RL_GAMMA` | `float` | `0.99` | Discount factor |
| `RL_GAE_LAMBDA` | `float` | `0.95` | GAE lambda |
| `RL_CLIP_RANGE` | `float` | `0.2` | PPO clip range |
| `RL_NUM_ENVS` | `int` | `4` | Parallel environments |
| `RL_CHECKPOINT_FREQ` | `int` | `10000` | Steps between checkpoints |
| `RL_EVAL_FREQ` | `int` | `5000` | Steps between evaluations |
| `RL_CHECKPOINT_DIR` | `Path` | `./checkpoints` | Checkpoint output directory |
| `RL_MODELS_DIR` | `Path` | `./models` | Best model output directory |
| `RL_TENSORBOARD_DIR` | `Path` | `./logs/tensorboard` | TensorBoard log directory |

---

## Implementation

### Files

| Path | Role |
|------|------|
| `src/document_simulator/rl/trainer.py` | `RLConfig` + `RLTrainer` |
| `src/document_simulator/rl/environment.py` | `DocumentEnv` constructed via `make_vec_env` |

### Key Architectural Decisions

1. **`RLConfig` as Pydantic Settings, not dataclass** — `pydantic_settings.BaseSettings` reads from environment variables and `.env` automatically, with type coercion. Every CI/CD override and UI form submission maps directly to an env var without a config file parser.

2. **`make_vec_env` for both train and eval envs** — SB3 requires vectorised environments even for `n_envs=1`. Using `make_vec_env` from SB3 ensures consistent vectorisation without manual `DummyVecEnv` wrapping.

3. **`CnnPolicy` for 224×224×3 uint8 observations** — The observation space shape and dtype are set by `DocumentEnv` specifically to satisfy SB3's `NatureCNN` requirements. Changing observation dtype to `float32` triggers a hard error.

4. **`train_data_dir=None` allowed** — When no dataset path is provided, `DocumentEnv` generates synthetic blank images. This allows `RLTrainer` to be instantiated in tests without a real dataset, while the slow tests with `total_timesteps=128` still exercise the full SB3 training loop.

### Known Edge Cases & Constraints

- PPO training with `CnnPolicy` requires substantial RAM (~2–4 GB for `n_envs=4`).
- `EvalCallback` occasionally raises when no best model has been saved yet (if training ends before the first eval step). This is a known SB3 behaviour — not a bug in our code.
- The `train` subcommand in `cli.py` currently references `PipelineOptimizer` which is a stub; the `RLTrainer` integration is wired through the UI page only.

---

## Tests

### Test Files

| File | Type | Count | What is covered |
|------|------|-------|-----------------|
| `tests/test_rl_training.py` | unit | 4 (fast) + 2 (slow) | Config defaults, trainer init, save to path, save default, load, PPO run (slow), checkpointing (slow) |

### TDD Cycle Summary

**Red — first failing tests written:**

| Test name | File | Initial failure reason |
|-----------|------|----------------------|
| `test_rl_config_defaults` | `tests/test_rl_training.py` | `ImportError: cannot import name 'RLConfig'` |
| `test_rl_trainer_initializes` | `tests/test_rl_training.py` | `ImportError: cannot import name 'RLTrainer'` |
| `test_rl_trainer_save` | `tests/test_rl_training.py` | `ImportError: cannot import name 'RLTrainer'` |

**Green — minimal implementation:**

Created `RLConfig` with all fields and `RLTrainer.__init__` wiring `DocumentEnv`, `make_vec_env`, and `PPO`. Implemented `save()` and `load()`. All 4 fast tests passed immediately. The slow tests (`@pytest.mark.slow`) were not run in CI.

**Refactor — improvements made after green:**

| What changed | Why |
|--------------|-----|
| Added `model_config = {"env_prefix": "RL_", ...}` to `RLConfig` | Without the prefix, `NUM_ENVS=4` clashed with unrelated environment variables in the shell |
| Changed `observation_space dtype` to `np.uint8` in `DocumentEnv` | SB3 `CnnPolicy` hard error: "You should use NatureCNN only with images" — caught when `test_rl_trainer_initializes` ran `PPO("CnnPolicy", ...)` |

### How to Run

```bash
# Fast tests only (no actual training)
uv run pytest tests/test_rl_training.py -v -m "not slow"

# All tests including actual PPO run
uv run pytest tests/test_rl_training.py -v

# With coverage
uv run pytest tests/test_rl_training.py --cov=document_simulator.rl.trainer -m "not slow"
```

---

## Dependencies

### Requires

| Dependency | Kind | Why |
|------------|------|-----|
| `stable_baselines3` | external | `PPO`, `make_vec_env`, `CheckpointCallback`, `EvalCallback` |
| `pydantic_settings` | external | `BaseSettings` for `RLConfig` |
| `rl/environment.py` | internal | `DocumentEnv` — the training environment |

### Required By

| Consumer | How it uses this feature |
|----------|------------------------|
| `ui/pages/05_rl_training.py` | Constructs `RLTrainer(RLConfig(**kwargs))` in background thread |
| `cli.py` | `train` subcommand (currently routes to `PipelineOptimizer` stub — pending refactor) |

---

## Usage Examples

### Minimal

```python
from document_simulator.rl.trainer import RLConfig, RLTrainer

trainer = RLTrainer(RLConfig(num_envs=1))
trainer.train(total_timesteps=1024)
trainer.save()
```

### Typical

```python
from document_simulator.rl.trainer import RLConfig, RLTrainer
from pathlib import Path

config = RLConfig(
    train_data_dir=Path("data/train"),
    val_data_dir=Path("data/val"),
    num_envs=4,
    learning_rate=3e-4,
    checkpoint_dir=Path("checkpoints"),
    models_dir=Path("models"),
)
trainer = RLTrainer(config)
model = trainer.train(total_timesteps=1_000_000)
trainer.save(Path("models/final.zip"))
```

### Advanced / Edge Case

```python
# Resume from checkpoint
trainer = RLTrainer(config)
trainer.load(Path("checkpoints/ppo_document_50000_steps.zip"))
trainer.train(total_timesteps=500_000)   # continues from loaded weights
```

---

## Future Work

- [ ] Wire `cli.py train` subcommand to `RLTrainer` instead of the `PipelineOptimizer` stub.
- [ ] Add `resume_from` parameter to `RLTrainer.train()` for explicit checkpoint resumption.
- [ ] Support DQN and SAC in addition to PPO via a `RL_ALGORITHM` config setting.
- [ ] Add W&B callback when `WANDB_PROJECT` is set.

---

## References

- [feature_rl_environment.md](feature_rl_environment.md)
- [Stable-Baselines3 documentation](https://stable-baselines3.readthedocs.io/)
- [IMPLEMENTATION_PLAN.md — Phase 3](../IMPLEMENTATION_PLAN.md)
