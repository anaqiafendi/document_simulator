"""FastAPI router for RL training endpoints."""

from __future__ import annotations

import threading
import tempfile
import zipfile
from pathlib import Path
from typing import Annotated, Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from loguru import logger
from pydantic import BaseModel

from document_simulator.api.jobs import create_job, get_job, update_job

router = APIRouter(prefix="/api/rl", tags=["rl_training"])

# Keep temp dirs alive while jobs are running
_temp_dirs: dict[str, tempfile.TemporaryDirectory] = {}

# Track running training threads to support stop
_stop_events: dict[str, threading.Event] = {}


class RlTrainRequest(BaseModel):
    """Request body for POST /api/rl/train."""

    learning_rate: float = 3e-4
    batch_size: int = 64
    n_steps: int = 2048
    num_envs: int = 4
    total_timesteps: int = 100_000
    checkpoint_freq: int = 10_000
    dataset_dir: Optional[str] = None


def _run_rl_training(
    job_id: str,
    config_kwargs: Dict[str, Any],
    stop_event: threading.Event,
    checkpoint_freq: int,
    total_timesteps: int,
) -> None:
    """Background daemon thread: run PPO training and log reward to job store."""
    try:
        update_job(job_id, status="running")

        from document_simulator.rl import RLConfig, RLTrainer
        from stable_baselines3.common.callbacks import BaseCallback

        config = RLConfig(**config_kwargs)
        trainer = RLTrainer(config)

        job = get_job(job_id)
        if job:
            job.training_log = []  # type: ignore[attr-defined]

        class _LogCallback(BaseCallback):
            def __init__(self):
                super().__init__()
                self._last_step = 0

            def _on_step(self) -> bool:
                if stop_event.is_set():
                    return False
                if self.num_timesteps - self._last_step >= checkpoint_freq:
                    self._last_step = self.num_timesteps
                    ep_rew = self.locals.get("infos", [{}])
                    mean_rew = float(
                        sum(i.get("episode", {}).get("r", 0.0) for i in ep_rew)
                        / max(len(ep_rew), 1)
                    )
                    entry: Dict[str, Any] = {
                        "step": self.num_timesteps,
                        "reward": mean_rew,
                    }
                    j = get_job(job_id)
                    if j:
                        log = getattr(j, "training_log", [])
                        log.append(entry)
                        j.training_log = log  # type: ignore[attr-defined]
                        update_job(
                            job_id,
                            progress=min(self.num_timesteps / max(total_timesteps, 1), 1.0),
                        )
                return True

        trainer.model.learn(
            total_timesteps=total_timesteps,
            callback=_LogCallback(),
            reset_num_timesteps=True,
        )

        saved_path = trainer.save()
        j = get_job(job_id)
        if j:
            j.model_path = str(saved_path)  # type: ignore[attr-defined]

        update_job(job_id, status="done", progress=1.0)
        logger.info(f"RL training job {job_id}: done, model saved to {saved_path}")

    except Exception as exc:
        logger.error(f"RL training job {job_id} failed: {exc}", exc_info=True)
        update_job(job_id, status="failed", error=str(exc))
    finally:
        _stop_events.pop(job_id, None)
        tmp = _temp_dirs.pop(job_id, None)
        if tmp:
            try:
                tmp.cleanup()
            except Exception:
                pass


@router.post("/train", status_code=202)
def start_training(body: RlTrainRequest) -> dict:
    """Start an RL (PPO) training job in a background daemon thread.

    Returns:
        ``{"job_id": str}``
    """
    dataset_dir: Optional[Path] = None
    if body.dataset_dir:
        p = Path(body.dataset_dir)
        if not p.exists():
            raise HTTPException(
                status_code=422, detail=f"dataset_dir not found: {body.dataset_dir}"
            )
        dataset_dir = p

    config_kwargs: Dict[str, Any] = {
        "learning_rate": body.learning_rate,
        "batch_size": body.batch_size,
        "n_steps": body.n_steps,
        "num_envs": body.num_envs,
        "checkpoint_freq": body.checkpoint_freq,
    }
    if dataset_dir is not None:
        config_kwargs["train_data_dir"] = dataset_dir

    job_id = create_job()
    stop_event = threading.Event()
    _stop_events[job_id] = stop_event

    t = threading.Thread(
        target=_run_rl_training,
        args=(job_id, config_kwargs, stop_event, body.checkpoint_freq, body.total_timesteps),
        daemon=True,
        name=f"RLTraining-{job_id[:8]}",
    )
    t.start()
    logger.info(
        f"RL training job {job_id} started: "
        f"lr={body.learning_rate} steps={body.total_timesteps}"
    )
    return {"job_id": job_id}


@router.post("/jobs/{job_id}/stop")
def stop_training(job_id: str) -> dict:
    """Request graceful stop of a running RL training job."""
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    event = _stop_events.get(job_id)
    if event:
        event.set()
        logger.info(f"RL training job {job_id}: stop requested")
        return {"message": "Stop requested."}
    return {"message": "Job is not running or already stopped."}


@router.get("/jobs/{job_id}/status")
def get_rl_status(job_id: str) -> dict:
    """Return status and latest training metrics for an RL job."""
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")

    log: list = getattr(job, "training_log", [])
    latest = log[-1] if log else {}

    return {
        "job_id": job.job_id,
        "status": job.status,
        "progress": job.progress,
        "error": job.error,
        "step": latest.get("step", 0),
        "reward": latest.get("reward", 0.0),
        "model_path": getattr(job, "model_path", None),
    }


@router.get("/jobs/{job_id}/metrics")
def get_rl_metrics(job_id: str) -> dict:
    """Return the full reward curve for an RL job."""
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")

    reward_curve: list = getattr(job, "training_log", [])
    return {
        "job_id": job.job_id,
        "reward_curve": reward_curve,
    }
