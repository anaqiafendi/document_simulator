"""In-memory job store for background generation tasks."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class JobState:
    job_id: str
    status: str = "pending"  # pending | running | done | failed
    progress: float = 0.0
    result_bytes: Optional[bytes] = None
    error: Optional[str] = None


_store: dict[str, JobState] = {}


def create_job() -> str:
    """Create a new job, store it, and return its ID."""
    job_id = str(uuid.uuid4())
    _store[job_id] = JobState(job_id=job_id)
    return job_id


def get_job(job_id: str) -> Optional[JobState]:
    """Return job state or None if not found."""
    return _store.get(job_id)


def update_job(job_id: str, **kwargs) -> None:
    """Update job state fields by keyword argument."""
    job = _store.get(job_id)
    if job:
        for k, v in kwargs.items():
            setattr(job, k, v)
