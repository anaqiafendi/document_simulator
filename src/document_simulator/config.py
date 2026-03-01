"""Configuration management for Document Simulator."""

from pathlib import Path
from typing import Optional

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
    paddleocr_det_model_dir: Optional[Path] = Field(default=None)
    paddleocr_rec_model_dir: Optional[Path] = Field(default=None)
    paddleocr_cls_model_dir: Optional[Path] = Field(default=None)

    # Stable-Baselines3 settings
    sb3_tensorboard_log: Path = Field(default=Path("./logs/tensorboard"))
    sb3_checkpoint_dir: Path = Field(default=Path("./checkpoints"))

    # Training settings
    batch_size: int = Field(default=32)
    num_epochs: int = Field(default=100)
    learning_rate: float = Field(default=0.001)
    random_seed: int = Field(default=42)

    # Weights & Biases (optional)
    wandb_api_key: Optional[str] = Field(default=None)
    wandb_project: Optional[str] = Field(default=None)
    wandb_entity: Optional[str] = Field(default=None)

    # PyTorch settings
    pytorch_cuda_alloc_conf: str = Field(default="expandable_segments:True")
    torch_home: Path = Field(default=Path("./cache/torch"))

    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="text")

    # Performance
    num_workers: int = Field(default=4)
    prefetch_factor: int = Field(default=2)
    pin_memory: bool = Field(default=True)


# Global settings instance
settings = Settings()
