"""FastAPI router for evaluation endpoints."""

from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path
from typing import Annotated, Optional

from fastapi import APIRouter, BackgroundTasks, Form, HTTPException, UploadFile
from loguru import logger

from document_simulator.api.jobs import create_job, get_job, update_job

router = APIRouter(prefix="/api/evaluation", tags=["evaluation"])

_VALID_PRESETS = {"light", "medium", "heavy", "default"}

# Keep temp dirs alive until job is done (GC would delete them otherwise)
_temp_dirs: dict[str, tempfile.TemporaryDirectory] = {}


def _run_evaluation_job(
    job_id: str,
    dataset_dir: str,
    preset: str,
    use_gpu: bool,
) -> None:
    """Background task: run evaluation and store results in job store."""
    try:
        update_job(job_id, status="running")

        p = Path(dataset_dir)
        if not p.exists():
            raise FileNotFoundError(f"Dataset directory not found: {p}")

        from document_simulator.augmentation import DocumentAugmenter
        from document_simulator.data import DocumentDataset
        from document_simulator.evaluation import Evaluator
        from document_simulator.ocr import OCREngine

        augmenter = DocumentAugmenter(pipeline=preset)
        engine = OCREngine(use_gpu=use_gpu)
        evaluator = Evaluator(augmenter, engine)
        dataset = DocumentDataset(p)

        if len(dataset) == 0:
            update_job(
                job_id,
                status="failed",
                error=(
                    "No annotated document/ground-truth pairs found in the directory. "
                    "Each document needs a matching .json or .xml annotation file."
                ),
            )
            return

        results = evaluator.evaluate_dataset(dataset)
        update_job(job_id, status="done", progress=1.0, result_bytes=None)

        # Store metrics as extra fields on the job (extend with dynamic attrs)
        job = get_job(job_id)
        if job:
            job.eval_results = results  # type: ignore[attr-defined]

        logger.info(f"Evaluation job {job_id}: n={results.get('n_samples', 0)} → done")

    except Exception as exc:
        logger.error(f"Evaluation job {job_id} failed: {exc}", exc_info=True)
        update_job(job_id, status="failed", error=str(exc))
    finally:
        # Clean up temp dir if it exists for this job
        tmp = _temp_dirs.pop(job_id, None)
        if tmp:
            try:
                tmp.cleanup()
            except Exception:
                pass


@router.post("/run", status_code=202)
async def run_evaluation(
    background_tasks: BackgroundTasks,
    preset: Annotated[str, Form()] = "medium",
    use_gpu: Annotated[bool, Form()] = False,
    dataset_dir: Annotated[Optional[str], Form()] = None,
    zip_file: Optional[UploadFile] = None,
) -> dict:
    """Start an evaluation job.

    Args:
        preset: Augmentation preset to evaluate against.
        use_gpu: Whether to use GPU for OCR inference.
        dataset_dir: Absolute path to a local dataset directory (server-side path).
        zip_file: ZIP archive containing document/annotation pairs.

    Returns:
        ``{"job_id": str}``
    """
    if preset not in _VALID_PRESETS:
        raise HTTPException(status_code=422, detail=f"Invalid preset '{preset}'.")
    if zip_file is None and not dataset_dir:
        raise HTTPException(
            status_code=422, detail="Provide either 'zip_file' or 'dataset_dir'."
        )

    # Resolve the directory we'll pass to the background task
    effective_dir: str
    tmp: Optional[tempfile.TemporaryDirectory] = None

    if zip_file is not None:
        contents = await zip_file.read()
        if not contents:
            raise HTTPException(status_code=422, detail="ZIP file is empty.")
        if not zipfile.is_zipfile(__import__("io").BytesIO(contents)):
            raise HTTPException(status_code=422, detail="Uploaded file is not a valid ZIP.")
        tmp = tempfile.TemporaryDirectory()
        with zipfile.ZipFile(__import__("io").BytesIO(contents)) as zf:
            zf.extractall(tmp.name)
        effective_dir = tmp.name
    else:
        effective_dir = str(dataset_dir)

    job_id = create_job()
    if tmp is not None:
        _temp_dirs[job_id] = tmp

    background_tasks.add_task(
        _run_evaluation_job, job_id, effective_dir, preset, use_gpu
    )
    logger.info(f"Evaluation job {job_id} queued: dir={effective_dir!r} preset={preset!r}")
    return {"job_id": job_id}


@router.get("/jobs/{job_id}/status")
def get_evaluation_status(job_id: str) -> dict:
    """Return the current status of an evaluation job, including results when done."""
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")

    response: dict = {
        "job_id": job.job_id,
        "status": job.status,
        "progress": job.progress,
        "error": job.error,
        "results": None,
    }
    # Attach eval_results if present (set dynamically by background task)
    eval_results = getattr(job, "eval_results", None)
    if eval_results is not None:
        response["results"] = eval_results

    return response
