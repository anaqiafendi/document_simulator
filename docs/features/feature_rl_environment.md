# Feature: RL Environment

> **GitHub Issue:** `#9`
> **Status:** `complete`
> **Module:** `document_simulator.rl.environment`

---

## Summary

`DocumentEnv` is a Gymnasium-compatible single-step environment where an agent proposes 12 continuous augmentation parameters, the environment applies them to a document image, runs OCR, and returns a composite reward measuring OCR accuracy, confidence, and visual change (SSIM).

---

## Motivation

### Problem Statement

Finding the augmentation parameters that maximally stress-test an OCR pipeline without human labelling of "good" vs "bad" degradation is a search problem with a 12-dimensional continuous action space. Reinforcement learning is a natural fit, but requires a standard Gymnasium interface to plug into Stable-Baselines3.

### Value Delivered

- Implements `gym.Env` fully — `reset()`, `step()`, `action_space`, `observation_space`.
- Works without a real dataset or OCR engine (synthetic blank images + zero reward) for fast unit tests.
- Reward function is decomposable: `0.5 × CAR + 0.3 × confidence + 0.2 × (1 − SSIM)`.
- Action-to-parameter mapping is documented and testable in isolation.
- `dtype=np.uint8` observation satisfies SB3 `CnnPolicy` requirement.

---

## User Stories

| Role | Goal | So That |
|------|------|---------|
| RL researcher | I pass `DocumentEnv` to `make_vec_env()` | I can train a PPO agent with SB3 out of the box |
| Developer | I run `env = DocumentEnv(); env.reset(); env.step(action)` | I verify the environment contract without model downloads |
| Experimenter | I adjust reward weights | I can bias the agent toward accuracy vs realism |

---

## Acceptance Criteria

- [ ] AC-1: `DocumentEnv()` initialises without error.
- [ ] AC-2: `action_space.shape == (12,)` with bounds `[0, 1]`.
- [ ] AC-3: `observation_space.shape == (224, 224, 3)` with `dtype=np.uint8`.
- [ ] AC-4: `reset()` returns `(obs, info)` where `obs` is contained in `observation_space`.
- [ ] AC-5: `reset(seed=42)` twice produces identical observations.
- [ ] AC-6: `step(action)` returns 5-tuple `(obs, reward, terminated, truncated, info)`.
- [ ] AC-7: `terminated is True` after every step (single-step episode).
- [ ] AC-8: `info` contains `"params"` key mapping action indices to named floats.
- [ ] AC-9: `_action_to_params(zeros)` returns a dict with 12 numeric values.
- [ ] AC-10: `_action_to_params(ones)["noise_sigma_max"]` ≈ 20.0 (scaled action).

---

## Design

### Public API

```python
from document_simulator.rl.environment import DocumentEnv

env = DocumentEnv(dataset_path=None, ocr_engine=None)
obs, info = env.reset(seed=42)
action = env.action_space.sample()
next_obs, reward, terminated, truncated, info = env.step(action)
```

### Data Flow

```
step(action: np.ndarray shape=(12,))
    │
    ▼
_action_to_params(action)
    → dict of 12 named floats (probabilities + scaled intensities)
    │
    ▼
_build_augmenter(params)
    → DocumentAugmenter with custom AugraphyPipeline
    │
    ▼
augmenter.augment(self._current_image)
    → aug_arr: np.ndarray
    │
    ▼
_calculate_reward(aug_arr, params)
    ├─► ocr.recognize(aug_arr) → CER, confidence
    ├─► _compute_ssim(original, aug_arr)
    └─► reward = 0.5×CAR + 0.3×confidence + 0.2×(1−SSIM)
    │
    ▼
(next_obs, reward, terminated=True, truncated=False, info)
```

### Key Interfaces

| Symbol | Kind | Responsibility |
|--------|------|---------------|
| `DocumentEnv(dataset_path, target_degradation, ocr_engine)` | class | Gymnasium env; synthetic data when no dataset provided |
| `reset(seed, options)` | method | Load random sample or blank; return uint8 obs |
| `step(action)` | method | Apply augmentation, compute reward, return 5-tuple |
| `_action_to_params(action)` | method | Map `[0,1]^12` → named parameter dict |
| `_build_augmenter(params)` | method | Construct `DocumentAugmenter` with custom Augraphy pipeline |
| `_calculate_reward(aug_arr, params)` | method | Composite reward from OCR + SSIM |
| `_compute_ssim(orig, aug)` | static method | SSIM via skimage; returns 0.5 on failure |
| `_image_to_obs(image)` | static method | Resize to 224×224, return uint8 |

### Configuration

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `ACTION_DIM` | `int` | `12` | Number of action dimensions |
| `OBS_HEIGHT` / `OBS_WIDTH` | `int` | `224` | Observation image size |

---

## Implementation

### Files

| Path | Role |
|------|------|
| `src/document_simulator/rl/environment.py` | Primary implementation |
| `src/document_simulator/augmentation/augmenter.py` | Used in `_build_augmenter()` (bypasses `__init__` via `__new__`) |
| `src/document_simulator/data/datasets.py` | `DocumentDataset` for sampling training images |
| `src/document_simulator/ocr/metrics.py` | `calculate_cer`, `aggregate_confidence` in reward calculation |

### Key Architectural Decisions

1. **`dtype=np.uint8` for observation space** — SB3's `CnnPolicy` wraps a `NatureCNN` that requires `dtype=uint8` observations shaped `(H, W, C)`. Passing `float32` triggers a hard error: "You should use NatureCNN only with images." All resizing and type conversion happens in `_image_to_obs`.

2. **Single-step episodes (`terminated=True`)** — Each episode is one augmentation step. This simplifies the reward function (no discounting needed) and allows `make_vec_env(n_envs=4)` to run many independent augmentation experiments in parallel.

3. **`_build_augmenter` uses `DocumentAugmenter.__new__`** — The standard `DocumentAugmenter(pipeline=...)` path calls `PresetFactory.create()` and builds a fixed Augraphy pipeline. `_build_augmenter` needs a dynamically-parameterised pipeline. Using `__new__` bypasses `__init__` and directly assigns a custom `_augraphy_pipeline` — a deliberate coupling to the augmenter internals, documented here.

4. **OCR engine is optional** — When `ocr_engine=None`, `_calculate_reward` returns `0.0` immediately. This lets the environment be instantiated in unit tests without triggering a PaddleOCR model download.

5. **SSIM fallback of 0.5** — If `skimage` is unavailable, SSIM defaults to 0.5 (neutral). This keeps the environment operational without the full dev environment and avoids crashing training.

### Known Edge Cases & Constraints

- `_build_augmenter` relies on `DocumentAugmenter` internals (`__new__`, `_augraphy_pipeline`). Renaming these would silently break the RL environment.
- `noise_sigma_max` is scaled by ×20 and `brightness_spread` by ×0.4 to map `[0,1]` to meaningful ranges. The RL agent must learn this scaling implicitly.

---

## Tests

### Test Files

| File | Type | Count | What is covered |
|------|------|-------|-----------------|
| `tests/test_rl_env.py` | unit | 15 | Init (2), action/obs space (3), reset (5), step (5), action-to-params (3) |

### TDD Cycle Summary

**Red — first failing tests written:**

| Test name | File | Initial failure reason |
|-----------|------|----------------------|
| `test_env_initialization` | `tests/test_rl_env.py` | `ImportError: cannot import name 'DocumentEnv'` |
| `test_env_action_space_shape` | `tests/test_rl_env.py` | `ImportError: cannot import name 'DocumentEnv'` |
| `test_env_reset_obs_dtype` | `tests/test_rl_env.py` | `AssertionError: dtype was float32, not uint8` |
| `test_env_step_terminated_after_one_step` | `tests/test_rl_env.py` | `AssertionError: terminated was False` |

**Green — minimal implementation:**

1. Created `DocumentEnv` inheriting `gym.Env` with the declared action/observation spaces.
2. `reset()` returned a blank 224×224×3 uint8 array — `test_env_reset_obs_dtype` passed.
3. `step()` returned a 5-tuple with `terminated=True` — step tests passed.
4. `_action_to_params` populated the dict with raw floats; `noise_sigma_max` scaling `× 20` caught by `test_action_to_parameters_all_one`.

**Refactor — improvements made after green:**

| What changed | Why |
|--------------|-----|
| Moved observation dtype from `float32` to `np.uint8` in `observation_space` | SB3 `CnnPolicy` validation error: "You should use NatureCNN only with images" — caught during first integration test with `RLTrainer` |
| Added `_compute_ssim` fallback to 0.5 | `skimage` import failure in a minimal test environment caused `_calculate_reward` to raise; wrapping in `try/except` makes the env robust |

### How to Run

```bash
uv run pytest tests/test_rl_env.py -v
uv run pytest tests/test_rl_env.py --cov=document_simulator.rl.environment
```

---

## Dependencies

### Requires

| Dependency | Kind | Why |
|------------|------|-----|
| `gymnasium` | external | `gym.Env` base class, space definitions |
| `numpy` | external | Observation and action arrays |
| `cv2` | external | `cv2.resize()` in `_image_to_obs` |
| `skimage.metrics.structural_similarity` | external | SSIM reward term (optional) |
| `augmentation/augmenter.py` | internal | `DocumentAugmenter` (via `__new__`) |
| `data/datasets.py` | internal | `DocumentDataset` for training samples |
| `ocr/metrics.py` | internal | `calculate_cer`, `aggregate_confidence` |

### Required By

| Consumer | How it uses this feature |
|----------|------------------------|
| `rl/trainer.py` | `RLTrainer.__init__` wraps `DocumentEnv` in `make_vec_env()` |
| `ui/pages/05_rl_training.py` | Passes `train_data_dir` to `RLConfig`, which creates `DocumentEnv` via `RLTrainer` |

---

## Usage Examples

### Minimal

```python
from document_simulator.rl.environment import DocumentEnv

env = DocumentEnv()  # no dataset, no OCR — for structure testing
obs, info = env.reset()
obs2, reward, done, _, info = env.step(env.action_space.sample())
```

### Typical

```python
from document_simulator.rl.environment import DocumentEnv
from document_simulator.ocr import OCREngine
from pathlib import Path

ocr = OCREngine(use_gpu=False)
env = DocumentEnv(dataset_path=Path("data/train"), ocr_engine=ocr)
obs, _ = env.reset(seed=0)
action = env.action_space.sample()
obs, reward, done, _, info = env.step(action)
print(f"reward={reward:.3f}  cer={info.get('cer', 'n/a')}")
```

### Advanced / Edge Case

```python
# Inspect action → parameter mapping
import numpy as np
from document_simulator.rl.environment import DocumentEnv, ACTION_DIM

env = DocumentEnv()
ones = np.ones(ACTION_DIM, dtype=np.float32)
params = env._action_to_params(ones)
# noise_sigma_max should be ≈ 20.0 (scaled by ×20)
assert abs(params["noise_sigma_max"] - 20.0) < 0.01
```

---

## Future Work

- [ ] Add multi-step episodes where the agent iteratively refines parameters.
- [ ] Add `target_degradation` reward shaping (currently stored but unused).
- [ ] Expose reward weight hyperparameters via `RLConfig`.

---

## References

- [feature_rl_trainer.md](feature_rl_trainer.md)
- [IMPLEMENTATION_PLAN.md — Phase 3](../IMPLEMENTATION_PLAN.md)
