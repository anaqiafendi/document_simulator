"""Tests for RLTrainer and RLConfig."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from document_simulator.rl.trainer import RLConfig, RLTrainer


@pytest.fixture
def minimal_config(tmp_path):
    return RLConfig(
        train_data_dir=None,
        val_data_dir=None,
        num_envs=1,
        checkpoint_dir=tmp_path / "checkpoints",
        models_dir=tmp_path / "models",
        logs_dir=tmp_path / "logs",
        tensorboard_dir=tmp_path / "logs" / "tb",
        checkpoint_freq=500,
        eval_freq=250,
    )


def test_rl_config_defaults():
    cfg = RLConfig()
    assert cfg.num_envs >= 1
    assert 0 < cfg.learning_rate < 1
    assert cfg.gamma == pytest.approx(0.99)


def test_rl_trainer_initializes(minimal_config):
    trainer = RLTrainer(minimal_config)
    assert trainer.model is not None
    assert trainer.train_env is not None
    assert trainer.eval_env is not None


def test_rl_trainer_save(minimal_config, tmp_path):
    trainer = RLTrainer(minimal_config)
    save_path = tmp_path / "test_model.zip"
    returned_path = trainer.save(save_path)
    assert save_path.exists()
    assert returned_path == save_path


def test_rl_trainer_save_default_path(minimal_config):
    trainer = RLTrainer(minimal_config)
    returned_path = trainer.save()
    assert returned_path.exists()
    assert returned_path.name == "final_model.zip"


def test_rl_trainer_load(minimal_config, tmp_path):
    trainer = RLTrainer(minimal_config)
    save_path = tmp_path / "model.zip"
    trainer.save(save_path)
    # Load should not raise
    trainer.load(save_path)
    assert trainer.model is not None


@pytest.mark.slow
def test_ppo_training_runs(minimal_config):
    """PPO training completes a minimal run without errors."""
    trainer = RLTrainer(minimal_config)
    model = trainer.train(total_timesteps=128)
    assert model is not None


@pytest.mark.slow
def test_model_checkpointing(minimal_config):
    """Models are saved at checkpoints."""
    minimal_config.checkpoint_freq = 64
    trainer = RLTrainer(minimal_config)
    trainer.train(total_timesteps=128)
    # At least the best_model or a checkpoint should exist
    checkpoint_files = list(minimal_config.checkpoint_dir.glob("*.zip"))
    best_model = minimal_config.models_dir / "best_model.zip"
    assert checkpoint_files or best_model.exists()
