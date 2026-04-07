"""Unit tests for BatchIntegrityChecker (synthesis/batch_integrity.py)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from document_simulator.synthesis.batch_integrity import (
    BatchIntegrityChecker,
    BatchIntegrityError,
    BatchIntegrityReport,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_image(path: Path) -> None:
    """Create a minimal PNG-like placeholder file."""
    path.write_bytes(b"\x89PNG\r\n\x1a\n")  # PNG magic bytes


def _create_gt(path: Path, image_path: str) -> None:
    """Create a minimal GT JSON sidecar."""
    data = {
        "image_path": image_path,
        "schema_version": "2.0",
        "fields": [],
    }
    path.write_text(json.dumps(data))


def _setup_valid_batch(output_dir: Path, n: int, ext: str = ".png") -> None:
    """Create n image + n GT pairs in output_dir."""
    for i in range(n):
        stem = f"doc_{i + 1:06d}"
        img_path = output_dir / f"{stem}{ext}"
        gt_path = output_dir / f"{stem}.json"
        _create_image(img_path)
        _create_gt(gt_path, str(img_path))


# ---------------------------------------------------------------------------
# Tests: successful check
# ---------------------------------------------------------------------------


def test_check_passes_when_all_pairs_present(tmp_path):
    _setup_valid_batch(tmp_path, 5)
    report = BatchIntegrityChecker.check(tmp_path, expected_n=5)
    assert report.ok is True


def test_check_returns_batch_integrity_report(tmp_path):
    _setup_valid_batch(tmp_path, 3)
    report = BatchIntegrityChecker.check(tmp_path, expected_n=3)
    assert isinstance(report, BatchIntegrityReport)


def test_check_zero_documents(tmp_path):
    report = BatchIntegrityChecker.check(tmp_path, expected_n=0)
    assert report.ok is True


def test_check_pdf_extension(tmp_path):
    _setup_valid_batch(tmp_path, 2, ext=".pdf")
    report = BatchIntegrityChecker.check(tmp_path, expected_n=2, ext=".pdf")
    assert report.ok is True


# ---------------------------------------------------------------------------
# Tests: count mismatch
# ---------------------------------------------------------------------------


def test_check_fails_when_gt_missing(tmp_path):
    _setup_valid_batch(tmp_path, 5)
    # Remove one GT file
    (tmp_path / "doc_000003.json").unlink()
    with pytest.raises(BatchIntegrityError):
        BatchIntegrityChecker.check(tmp_path, expected_n=5)


def test_check_fails_when_fewer_images_than_expected(tmp_path):
    _setup_valid_batch(tmp_path, 3)
    with pytest.raises(BatchIntegrityError):
        BatchIntegrityChecker.check(tmp_path, expected_n=5)


def test_check_report_lists_missing_gt(tmp_path):
    _setup_valid_batch(tmp_path, 3)
    (tmp_path / "doc_000002.json").unlink()
    try:
        BatchIntegrityChecker.check(tmp_path, expected_n=3)
    except BatchIntegrityError as exc:
        assert exc.report is not None
        assert len(exc.report.missing_gt) == 1
        assert "doc_000002" in exc.report.missing_gt[0]


# ---------------------------------------------------------------------------
# Tests: orphaned GT (GT exists but image path in GT is missing)
# ---------------------------------------------------------------------------


def test_check_fails_when_image_path_in_gt_missing(tmp_path):
    _setup_valid_batch(tmp_path, 3)
    # Overwrite one GT so its image_path points to a non-existent file
    gt_path = tmp_path / "doc_000001.json"
    data = json.loads(gt_path.read_text())
    data["image_path"] = str(tmp_path / "nonexistent.png")
    gt_path.write_text(json.dumps(data))
    with pytest.raises(BatchIntegrityError):
        BatchIntegrityChecker.check(tmp_path, expected_n=3)


def test_check_report_lists_missing_images(tmp_path):
    _setup_valid_batch(tmp_path, 3)
    gt_path = tmp_path / "doc_000001.json"
    data = json.loads(gt_path.read_text())
    data["image_path"] = "/nonexistent/path/doc.png"
    gt_path.write_text(json.dumps(data))
    try:
        BatchIntegrityChecker.check(tmp_path, expected_n=3)
    except BatchIntegrityError as exc:
        assert exc.report is not None
        assert len(exc.report.missing_images) >= 1


# ---------------------------------------------------------------------------
# Tests: orphaned GT (GT file with no matching image file)
# ---------------------------------------------------------------------------


def test_check_report_lists_orphaned_gt(tmp_path):
    _setup_valid_batch(tmp_path, 3)
    # Delete the image file for doc_000002 — GT still exists
    (tmp_path / "doc_000002.png").unlink()
    try:
        BatchIntegrityChecker.check(tmp_path, expected_n=3)
    except BatchIntegrityError as exc:
        assert exc.report is not None
        # Either missing_images or orphaned_gt should capture this
        has_orphan = (
            any("doc_000002" in p for p in exc.report.orphaned_gt)
            or any("doc_000002" in p for p in exc.report.missing_images)
        )
        assert has_orphan


# ---------------------------------------------------------------------------
# Tests: report structure
# ---------------------------------------------------------------------------


def test_report_has_all_fields(tmp_path):
    _setup_valid_batch(tmp_path, 2)
    report = BatchIntegrityChecker.check(tmp_path, expected_n=2)
    assert hasattr(report, "ok")
    assert hasattr(report, "missing_gt")
    assert hasattr(report, "missing_images")
    assert hasattr(report, "orphaned_gt")
    assert hasattr(report, "expected_n")
    assert hasattr(report, "found_images")
    assert hasattr(report, "found_gt")
