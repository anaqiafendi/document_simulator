"""Persist a rendered receipt sample to disk.

Writes:
- images/{image_id}.png
- ground_truth/{image_id}.gt.json
- manifest.jsonl  (one appended line per sample)

All file writes are atomic (write-to-temp + rename). The manifest line uses
``open(..., "a")`` so concurrent appends from a future ProcessPoolExecutor stay
safe (POSIX guarantees atomicity for writes ≤ PIPE_BUF, well above one
manifest line).
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from loguru import logger
from PIL import Image

from document_simulator.synthesis.receipts.schema import ImageGroundTruth


def _atomic_write_bytes(path: Path, data: bytes) -> None:
    """Write `data` to `path` atomically via a sibling tempfile + os.replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        os.replace(tmp_name, path)
    except Exception:
        # Best-effort cleanup
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise


def _atomic_write_text(path: Path, text: str) -> None:
    """Write `text` to `path` atomically (UTF-8 encoded)."""
    _atomic_write_bytes(path, text.encode("utf-8"))


def persist_sample(image: Image.Image, gt: ImageGroundTruth, dataset_root: Path) -> None:
    """Persist one rendered sample (image + GT JSON) and append to the manifest.

    Args:
        image: Rendered PIL image.
        gt: Per-image ground truth.
        dataset_root: Output dataset directory; created if missing along with
            its ``images/`` and ``ground_truth/`` subdirectories.

    Side effects:
        Writes::
            {dataset_root}/images/{image_id}.png
            {dataset_root}/ground_truth/{image_id}.gt.json
        and appends one JSON line to::
            {dataset_root}/manifest.jsonl
    """
    dataset_root = Path(dataset_root)
    images_dir = dataset_root / "images"
    gt_dir = dataset_root / "ground_truth"
    images_dir.mkdir(parents=True, exist_ok=True)
    gt_dir.mkdir(parents=True, exist_ok=True)

    image_path = images_dir / f"{gt.image_id}.png"
    gt_path = gt_dir / f"{gt.image_id}.gt.json"
    manifest_path = dataset_root / "manifest.jsonl"

    # Image: write to temp file then rename for atomicity.
    tmp_image = image_path.with_suffix(image_path.suffix + ".tmp")
    image.save(tmp_image, format="PNG")
    os.replace(tmp_image, image_path)

    # Ground truth: pretty-printed JSON, atomically.
    gt_json = gt.model_dump_json(indent=2)
    _atomic_write_text(gt_path, gt_json)

    # Manifest: append-only one-line entry.
    entry = {
        "image_id": gt.image_id,
        "image_path": str(image_path.relative_to(dataset_root)),
        "gt_path": str(gt_path.relative_to(dataset_root)),
        "n_tokens": len(gt.tokens),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pipeline_version": gt.pipeline_version,
    }
    line = json.dumps(entry, sort_keys=True) + "\n"
    with open(manifest_path, "a", encoding="utf-8") as fh:
        fh.write(line)

    logger.debug(
        f"Persisted sample image_id={gt.image_id} " f"image_path={image_path} gt_path={gt_path}"
    )
