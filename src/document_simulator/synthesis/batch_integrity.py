"""BatchIntegrityChecker — verify that every generated image has a paired GT file.

Raises :class:`BatchIntegrityError` if any of the following conditions are detected:

- The number of image files does not match ``expected_n``.
- A GT sidecar JSON is missing for any image file.
- The ``image_path`` field inside a GT file points to a non-existent file.
- An image file has no corresponding GT sidecar (orphaned image).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class BatchIntegrityReport:
    """Summary of a batch integrity check.

    Attributes:
        ok: ``True`` if all checks passed.
        expected_n: The expected number of documents.
        found_images: Actual number of image files found.
        found_gt: Actual number of GT JSON files found (excluding ``synthesis_config.json``).
        missing_gt: List of image stems that have no corresponding GT file.
        missing_images: List of GT file paths whose ``image_path`` field points to a missing file.
        orphaned_gt: List of GT stems that have no corresponding image file in the directory.
    """

    ok: bool
    expected_n: int
    found_images: int
    found_gt: int
    missing_gt: list[str] = field(default_factory=list)
    missing_images: list[str] = field(default_factory=list)
    orphaned_gt: list[str] = field(default_factory=list)


class BatchIntegrityError(Exception):
    """Raised when the batch integrity check fails.

    Attributes:
        report: The :class:`BatchIntegrityReport` that describes the failures.
    """

    def __init__(self, message: str, report: BatchIntegrityReport) -> None:
        super().__init__(message)
        self.report = report


class BatchIntegrityChecker:
    """Verify that a generated batch directory is complete and internally consistent."""

    @staticmethod
    def check(
        output_dir: Path | str,
        expected_n: int,
        ext: str = ".png",
    ) -> BatchIntegrityReport:
        """Check the integrity of a batch output directory.

        Verifies:

        1. The number of ``*{ext}`` files equals ``expected_n``.
        2. Every image file ``doc_XXXXXX{ext}`` has a corresponding ``doc_XXXXXX.json``.
        3. Every GT JSON's ``image_path`` field resolves to an existing file.
        4. Every GT JSON has a corresponding image file in the directory.

        Args:
            output_dir: Path to the batch output directory.
            expected_n: Expected number of generated documents.
            ext: Image file extension (default ``".png"``).

        Returns:
            :class:`BatchIntegrityReport` with ``ok=True`` if all checks passed.

        Raises:
            BatchIntegrityError: If any check fails.  The exception carries a
                :class:`BatchIntegrityReport` with details of all failures found.
        """
        output_dir = Path(output_dir)

        # --- collect files -----------------------------------------------
        image_files = sorted(output_dir.glob(f"*{ext}"))
        # Exclude synthesis_config.json
        gt_files = sorted(
            f for f in output_dir.glob("*.json") if f.name != "synthesis_config.json"
        )

        found_images = len(image_files)
        found_gt = len(gt_files)

        image_stems = {f.stem for f in image_files}
        gt_stems = {f.stem for f in gt_files}

        missing_gt: list[str] = []
        missing_images: list[str] = []
        orphaned_gt: list[str] = []

        # --- check 1: count matches expected_n ---------------------------
        count_ok = found_images == expected_n

        # --- check 2: every image has a GT sidecar -----------------------
        for img_file in image_files:
            if img_file.stem not in gt_stems:
                missing_gt.append(str(img_file))

        # --- check 3: GT image_path points to existing file --------------
        for gt_file in gt_files:
            try:
                with open(gt_file, encoding="utf-8") as f:
                    data = json.load(f)
                img_path = data.get("image_path", "")
                if img_path and not Path(img_path).exists():
                    missing_images.append(img_path)
            except (json.JSONDecodeError, OSError):
                # Malformed GT file — treat as missing image reference
                missing_images.append(str(gt_file))

        # --- check 4: every GT has a corresponding image in the dir ------
        for gt_file in gt_files:
            if gt_file.stem not in image_stems:
                orphaned_gt.append(str(gt_file))

        ok = count_ok and not missing_gt and not missing_images and not orphaned_gt

        report = BatchIntegrityReport(
            ok=ok,
            expected_n=expected_n,
            found_images=found_images,
            found_gt=found_gt,
            missing_gt=missing_gt,
            missing_images=missing_images,
            orphaned_gt=orphaned_gt,
        )

        if not ok:
            parts = []
            if not count_ok:
                parts.append(
                    f"expected {expected_n} image files, found {found_images}"
                )
            if missing_gt:
                parts.append(f"{len(missing_gt)} image(s) have no GT sidecar")
            if missing_images:
                parts.append(f"{len(missing_images)} GT file(s) reference missing images")
            if orphaned_gt:
                parts.append(f"{len(orphaned_gt)} GT file(s) have no matching image")
            message = "Batch integrity check failed: " + "; ".join(parts) + "."
            raise BatchIntegrityError(message, report)

        return report
