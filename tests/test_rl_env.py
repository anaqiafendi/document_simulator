"""Tests for the DocumentEnv Gymnasium environment."""

import numpy as np
import pytest

from document_simulator.rl.environment import ACTION_DIM, DocumentEnv


@pytest.fixture
def env():
    """Environment without dataset or OCR engine (pure structural tests)."""
    return DocumentEnv(dataset_path=None, ocr_engine=None)


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

def test_env_initialization(env):
    assert env.action_space is not None
    assert env.observation_space is not None


def test_env_action_space_shape(env):
    assert env.action_space.shape == (ACTION_DIM,)


def test_env_observation_space_shape(env):
    assert env.observation_space.shape == (224, 224, 3)


def test_env_action_space_bounds(env):
    assert env.action_space.low.min() == pytest.approx(0.0)
    assert env.action_space.high.max() == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# reset()
# ---------------------------------------------------------------------------

def test_env_reset_returns_valid_observation(env):
    obs, info = env.reset()
    assert env.observation_space.contains(obs)


def test_env_reset_obs_shape(env):
    obs, _ = env.reset()
    assert obs.shape == (224, 224, 3)


def test_env_reset_obs_dtype(env):
    obs, _ = env.reset()
    assert obs.dtype == np.uint8


def test_env_reset_returns_dict_info(env):
    _, info = env.reset()
    assert isinstance(info, dict)


def test_env_reset_with_seed(env):
    obs1, _ = env.reset(seed=42)
    obs2, _ = env.reset(seed=42)
    np.testing.assert_array_equal(obs1, obs2)


# ---------------------------------------------------------------------------
# step()
# ---------------------------------------------------------------------------

def test_env_step_returns_5_tuple(env):
    env.reset()
    action = env.action_space.sample()
    result = env.step(action)
    assert len(result) == 5


def test_env_step_obs_in_observation_space(env):
    env.reset()
    action = env.action_space.sample()
    next_obs, reward, terminated, truncated, info = env.step(action)
    assert env.observation_space.contains(next_obs)


def test_env_step_reward_is_numeric(env):
    env.reset()
    action = env.action_space.sample()
    _, reward, _, _, _ = env.step(action)
    assert isinstance(reward, (int, float))


def test_env_step_terminated_after_one_step(env):
    """Each episode is a single step."""
    env.reset()
    action = env.action_space.sample()
    _, _, terminated, truncated, _ = env.step(action)
    assert terminated is True
    assert truncated is False


def test_env_step_info_has_params(env):
    env.reset()
    action = env.action_space.sample()
    _, _, _, _, info = env.step(action)
    assert "params" in info


# ---------------------------------------------------------------------------
# action_to_params
# ---------------------------------------------------------------------------

def test_action_to_parameters_all_zero(env):
    action = np.zeros(ACTION_DIM, dtype=np.float32)
    params = env._action_to_params(action)
    assert all(isinstance(v, (int, float)) for v in params.values())


def test_action_to_parameters_all_one(env):
    action = np.ones(ACTION_DIM, dtype=np.float32)
    params = env._action_to_params(action)
    assert params["noise_sigma_max"] == pytest.approx(20.0)


def test_action_to_parameters_count(env):
    action = env.action_space.sample()
    params = env._action_to_params(action)
    assert len(params) == ACTION_DIM
