"""FastAPI router for batch augmentation endpoints."""

from __future__ import annotations

import io
import zipfile
from typing import Annotated, List, Optional

from fastapi import APIRouter, BackgroundTasks, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from loguru import logger
from PIL import Image

from document_simulator.api.jobs import create_job, get_job, update_job

router = APIRouter(prefix="/api/batch", tags=["batch"])

_VALID_MODES = {"single", "per_template", "random_sample"}
_VALID_PRESETS = {"light", "medium", "heavy", "default"}


def _bytes_to_pil(data: bytes) -> Image.Image:
    return Image.open(io.BytesIO(data)).convert("RGB")


def _pil_to_png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


def _run_batch_job(
    job_id: str,
    image_bytes_list: list[bytes],
    labels: list[str],
    preset: str,
    mode: str,
    copies_per_template: int,
    total_outputs: int,
    seed: Optional[int],
    n_workers: int,
) -> None:
    """Background task: run batch augmentation and store ZIP in job store."""
    try:
        update_job(job_id, status="running")
        images = [_bytes_to_pil(b) for b in image_bytes_list]

        from document_simulator.augmentation.batch import BatchAugmenter

        batch = BatchAugmenter(augmenter=preset, num_workers=n_workers)

        if mode == "single":
            results = batch.augment_batch(images, parallel=(n_workers > 1))
            result_pairs = list(zip(results, labels))
        elif mode == "per_template":
            pairs = batch.augment_multi_template(
                images,
                mode="per_template",
                copies_per_template=copies_per_template,
                parallel=(n_workers > 1),
            )
            result_pairs = [(img, stem) for img, stem in pairs]
        else:  # random_sample
            pairs = batch.augment_multi_template(
                images,
                mode="random_sample",
                total_outputs=total_outputs,
                seed=seed,
                parallel=(n_workers > 1),
            )
            result_pairs = [(img, stem) for img, stem in pairs]

        # Build ZIP
        stem_counter: dict = {}
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            n_total = len(result_pairs)
            for i, (img, stem) in enumerate(result_pairs):
                count = stem_counter.get(stem, 0)
                stem_counter[stem] = count + 1
                if mode == "random_sample":
                    filename = f"{stem}_{count:04d}.png"
                else:
                    filename = f"{stem}_{count:03d}.png"
                zf.writestr(filename, _pil_to_png_bytes(img))
                update_job(job_id, progress=(i + 1) / max(n_total, 1))

        buf.seek(0)
        update_job(job_id, status="done", progress=1.0, result_bytes=buf.read())
        logger.info(f"Batch job {job_id}: {len(result_pairs)} images → done")

    except Exception as exc:
        logger.error(f"Batch job {job_id} failed: {exc}", exc_info=True)
        update_job(job_id, status="failed", error=str(exc))


@router.post("/process", status_code=202)
async def process_batch(
    background_tasks: BackgroundTasks,
    files: List[UploadFile],
    preset: Annotated[str, Form()] = "medium",
    mode: Annotated[str, Form()] = "single",
    copies_per_template: Annotated[int, Form()] = 3,
    total_outputs: Annotated[int, Form()] = 20,
    seed: Annotated[int, Form()] = 0,
    n_workers: Annotated[int, Form()] = 4,
) -> dict:
    """Start a batch augmentation job.

    Args:
        files: List of document images to augment.
        preset: Augmentation preset (``light``, ``medium``, ``heavy``, ``default``).
        mode: ``single`` | ``per_template`` | ``random_sample``.
        copies_per_template: Copies per template (N×M mode).
        total_outputs: Total outputs (M-total mode).
        seed: Random seed for reproducible sampling (0 = unseeded).
        n_workers: Number of parallel augmentation workers.

    Returns:
        ``{"job_id": str}``
    """
    if not files:
        raise HTTPException(status_code=422, detail="At least one file is required.")
    if preset not in _VALID_PRESETS:
        raise HTTPException(status_code=422, detail=f"Invalid preset '{preset}'.")
    if mode not in _VALID_MODES:
        raise HTTPException(status_code=422, detail=f"Invalid mode '{mode}'.")

    # Read all file bytes eagerly before entering background task
    image_bytes_list = []
    labels = []
    for f in files:
        data = await f.read()
        if not data:
            raise HTTPException(status_code=422, detail=f"File '{f.filename}' is empty.")
        image_bytes_list.append(data)
        name = f.filename or f"file_{len(labels)}"
        stem = name.rsplit(".", 1)[0] if "." in name else name
        labels.append(stem)

    job_id = create_job()
    seed_arg = seed if seed > 0 else None

    background_tasks.add_task(
        _run_batch_job,
        job_id,
        image_bytes_list,
        labels,
        preset,
        mode,
        copies_per_template,
        total_outputs,
        seed_arg,
        n_workers,
    )
    logger.info(f"Batch job {job_id} queued: {len(files)} files preset={preset!r} mode={mode!r}")
    return {"job_id": job_id}


@router.get("/jobs/{job_id}")
def get_batch_job_status(job_id: str) -> dict:
    """Return the current status of a batch job."""
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    return {
        "job_id": job.job_id,
        "status": job.status,
        "progress": job.progress,
        "error": job.error,
    }


@router.get("/jobs/{job_id}/download")
def download_batch_job(job_id: str) -> StreamingResponse:
    """Download the ZIP archive for a completed batch job."""
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    if job.status != "done" or job.result_bytes is None:
        raise HTTPException(
            status_code=404,
            detail=f"Job '{job_id}' is not done yet (status={job.status}).",
        )
    return StreamingResponse(
        iter([job.result_bytes]),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=augmented_batch.zip"},
    )
