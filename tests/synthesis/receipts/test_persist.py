"""Unit tests for synthesis.receipts.persist (AC-5 layout, AC-6 determinism)."""

import json

from document_simulator.synthesis.receipts import (
    persist_sample,
    render_receipt,
)
from document_simulator.synthesis.receipts.content import make_minimal_receipt


def test_persist_writes_three_paths(tmp_path):
    """AC-5: persist writes images/{id}.png, ground_truth/{id}.gt.json, manifest.jsonl."""
    image, gt = render_receipt(make_minimal_receipt(seed=42), seed=42)
    persist_sample(image, gt, tmp_path)

    image_path = tmp_path / "images" / f"{gt.image_id}.png"
    gt_path = tmp_path / "ground_truth" / f"{gt.image_id}.gt.json"
    manifest_path = tmp_path / "manifest.jsonl"

    assert image_path.is_file()
    assert gt_path.is_file()
    assert manifest_path.is_file()


def test_persist_manifest_line_shape(tmp_path):
    """AC-5: manifest line has the 6 required keys."""
    image, gt = render_receipt(make_minimal_receipt(seed=42), seed=42)
    persist_sample(image, gt, tmp_path)

    manifest_lines = (tmp_path / "manifest.jsonl").read_text().splitlines()
    assert len(manifest_lines) == 1

    entry = json.loads(manifest_lines[0])
    expected_keys = {
        "image_id",
        "image_path",
        "gt_path",
        "n_tokens",
        "generated_at",
        "pipeline_version",
    }
    assert set(entry.keys()) == expected_keys
    assert entry["image_id"] == gt.image_id
    assert entry["n_tokens"] == len(gt.tokens)
    assert entry["pipeline_version"] == gt.pipeline_version


def test_persist_determinism_byte_identical(tmp_path):
    """AC-6: same seed -> byte-identical .gt.json across two render+persist runs."""
    root_a = tmp_path / "run_a"
    root_b = tmp_path / "run_b"

    image_a, gt_a = render_receipt(make_minimal_receipt(seed=42), seed=42)
    persist_sample(image_a, gt_a, root_a)

    image_b, gt_b = render_receipt(make_minimal_receipt(seed=42), seed=42)
    persist_sample(image_b, gt_b, root_b)

    bytes_a = (root_a / "ground_truth" / f"{gt_a.image_id}.gt.json").read_bytes()
    bytes_b = (root_b / "ground_truth" / f"{gt_b.image_id}.gt.json").read_bytes()
    assert bytes_a == bytes_b
