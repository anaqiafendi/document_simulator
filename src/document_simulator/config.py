"""Configuration management for Document Simulator."""

import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Project settings
    project_name: str = Field(default="document-simulator")
    environment: str = Field(default="development")

    # Paths
    data_dir: Path = Field(default=Path("./data"))
    models_dir: Path = Field(default=Path("./models"))
    output_dir: Path = Field(default=Path("./output"))
    logs_dir: Path = Field(default=Path("./logs"))

    # Augraphy settings
    augraphy_cache_dir: Path = Field(default=Path("./cache/augraphy"))
    augraphy_num_workers: int = Field(default=4)

    # PaddleOCR settings
    paddleocr_use_gpu: bool = Field(default=False)
    paddleocr_lang: str = Field(default="en")
    paddleocr_det_model_dir: Path | None = Field(default=None)
    paddleocr_rec_model_dir: Path | None = Field(default=None)
    paddleocr_cls_model_dir: Path | None = Field(default=None)

    # Stable-Baselines3 settings
    sb3_tensorboard_log: Path = Field(default=Path("./logs/tensorboard"))
    sb3_checkpoint_dir: Path = Field(default=Path("./checkpoints"))

    # Training settings
    batch_size: int = Field(default=32)
    num_epochs: int = Field(default=100)
    learning_rate: float = Field(default=0.001)
    random_seed: int = Field(default=42)

    # Weights & Biases (optional)
    wandb_api_key: str | None = Field(default=None)
    wandb_project: str | None = Field(default=None)
    wandb_entity: str | None = Field(default=None)

    # PyTorch settings
    pytorch_cuda_alloc_conf: str = Field(default="expandable_segments:True")
    torch_home: Path = Field(default=Path("./cache/torch"))

    # ReceiptFaker corpus. The scraped brand logos are not in git (third-party
    # trademarks, 28MB of undeltifiable images), so they live outside the repo
    # and survive worktrees being created and deleted. Override with
    # RECEIPTFAKER_LOGO_DIR in .env to share one pool across checkouts.
    receiptfaker_logo_dir: Path | None = Field(default=None)

    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="text")

    # Performance
    num_workers: int = Field(default=4)
    prefetch_factor: int = Field(default=2)
    pin_memory: bool = Field(default=True)


# Global settings instance
settings = Settings()


def _user_cache_root() -> Path:
    """Base directory for machine-wide, repo-independent caches."""
    xdg = os.environ.get("XDG_CACHE_HOME")
    base = Path(xdg) if xdg else Path.home() / ".cache"
    return base / "document_simulator"


#: Where scraped ReceiptFaker logos live when nothing overrides it. Deliberately
#: outside the repository: a git worktree is disposable, and re-scraping 749
#: images on every new branch is wasted time and wasted requests to the origin.
DEFAULT_LOGO_CACHE: Path = _user_cache_root() / "receiptfaker" / "logos"


def resolve_logo_dir(repo_local: Path | None = None) -> Path:
    """Pick the logo pool to read from.

    Order: an explicit ``RECEIPTFAKER_LOGO_DIR`` always wins; then a populated
    repo-local directory, so an existing checkout keeps working untouched; then
    the shared user cache. Returns the shared cache when nothing is populated,
    so callers get a stable path to write into.
    """
    if settings.receiptfaker_logo_dir is not None:
        return settings.receiptfaker_logo_dir
    if repo_local is not None and repo_local.is_dir() and any(repo_local.iterdir()):
        return repo_local
    return DEFAULT_LOGO_CACHE
