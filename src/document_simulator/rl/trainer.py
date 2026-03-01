"""PPO training pipeline for document augmentation RL."""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import (
    CallbackList,
    CheckpointCallback,
    EvalCallback,
)
from stable_baselines3.common.env_util import make_vec_env

from document_simulator.rl.environment import DocumentEnv


class RLConfig(BaseSettings):
    """Hyper-parameters and paths for RL training.

    All fields can be overridden via environment variables or a ``.env`` file.
    """

    # Data
    train_data_dir: Optional[Path] = Field(default=None)
    val_data_dir: Optional[Path] = Field(default=None)

    # Environment
    num_envs: int = Field(default=4, description="Number of parallel environments")

    # PPO
    learning_rate: float = Field(default=3e-4)
    n_steps: int = Field(default=2048)
    batch_size: int = Field(default=64)
    n_epochs: int = Field(default=10)
    gamma: float = Field(default=0.99)
    gae_lambda: float = Field(default=0.95)
    clip_range: float = Field(default=0.2)

    # Checkpointing & logging
    checkpoint_dir: Path = Field(default=Path("./checkpoints"))
    models_dir: Path = Field(default=Path("./models"))
    logs_dir: Path = Field(default=Path("./logs"))
    tensorboard_dir: Path = Field(default=Path("./logs/tensorboard"))

    # Callbacks
    checkpoint_freq: int = Field(default=10_000)
    eval_freq: int = Field(default=5_000)

    model_config = {"env_prefix": "RL_", "env_file": ".env", "extra": "ignore"}


class RLTrainer:
    """Manages the full PPO training workflow.

    Args:
        config: :class:`RLConfig` instance.  Defaults to values from env / .env.
    """

    def __init__(self, config: Optional[RLConfig] = None):
        self.config = config or RLConfig()
        cfg = self.config

        def _make_train_env():
            return DocumentEnv(dataset_path=cfg.train_data_dir)

        def _make_eval_env():
            return DocumentEnv(dataset_path=cfg.val_data_dir or cfg.train_data_dir)

        self.train_env = make_vec_env(_make_train_env, n_envs=cfg.num_envs)
        self.eval_env = make_vec_env(_make_eval_env, n_envs=1)

        self.model = PPO(
            "CnnPolicy",
            self.train_env,
            learning_rate=cfg.learning_rate,
            n_steps=cfg.n_steps,
            batch_size=cfg.batch_size,
            n_epochs=cfg.n_epochs,
            gamma=cfg.gamma,
            gae_lambda=cfg.gae_lambda,
            clip_range=cfg.clip_range,
            verbose=1,
            tensorboard_log=str(cfg.tensorboard_dir),
        )

    def train(self, total_timesteps: int = 1_000_000) -> PPO:
        """Run the training loop.

        Args:
            total_timesteps: Total environment steps to train for.

        Returns:
            The trained :class:`stable_baselines3.PPO` model.
        """
        cfg = self.config
        cfg.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        cfg.models_dir.mkdir(parents=True, exist_ok=True)
        cfg.logs_dir.mkdir(parents=True, exist_ok=True)

        checkpoint_cb = CheckpointCallback(
            save_freq=cfg.checkpoint_freq,
            save_path=str(cfg.checkpoint_dir),
            name_prefix="ppo_document",
        )
        eval_cb = EvalCallback(
            self.eval_env,
            best_model_save_path=str(cfg.models_dir),
            log_path=str(cfg.logs_dir),
            eval_freq=cfg.eval_freq,
            deterministic=True,
            render=False,
        )
        callbacks = CallbackList([checkpoint_cb, eval_cb])

        self.model.learn(
            total_timesteps=total_timesteps,
            callback=callbacks,
            progress_bar=True,
        )
        return self.model

    def save(self, path: Optional[Path] = None) -> Path:
        """Save the current model to *path* (defaults to models_dir/final_model.zip).

        Returns:
            Path where the model was saved.
        """
        save_path = path or (self.config.models_dir / "final_model.zip")
        save_path.parent.mkdir(parents=True, exist_ok=True)
        self.model.save(str(save_path))
        return save_path

    def load(self, path: Path) -> None:
        """Load a previously saved model.

        Args:
            path: Path to the ``.zip`` model file.
        """
        self.model = PPO.load(str(path), env=self.train_env)
