"""Unit tests for GroundTruthWriter (synthesis/ground_truth_writer.py)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from document_simulator.data.ground_truth import GroundTruth, TextRegion
from document_simulator.synthesis.ground_truth_writer import (
    EnhancedGroundTruth,
    GroundTruthRecord,
    GroundTruthWriter,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_text_region(
    box=None,
    text="Jane Doe",
    label="customer_name",
    confidence=1.0,
    font_family="sans-serif",
    font_size=12,
    font_color="#000000",
    fill_style="typed",
    page=0,
) -> TextRegion:
    if box is None:
        box = [[10.0, 20.0], [200.0, 20.0], [200.0, 50.0], [10.0, 50.0]]
    return TextRegion(
        box=box,
        text=text,
        confidence=confidence,
        label=label,
        font_family=font_family,
        font_size=font_size,
        font_color=font_color,
        fill_style=fill_style,
        page=page,
    )


def _make_ground_truth(regions=None, image_path="doc_000001.png") -> GroundTruth:
    if regions is None:
        regions = [_make_text_region()]
    return GroundTruth(
        image_path=image_path,
        text="\n".join(r.text for r in regions),
        regions=regions,
        synthetic=True,
        seed=42,
        generation_timestamp="2026-04-06T12:00:00Z",
    )


# ---------------------------------------------------------------------------
# GroundTruthWriter.from_ground_truth
# ---------------------------------------------------------------------------


def test_from_ground_truth_returns_enhanced_ground_truth():
    gt = _make_ground_truth()
    egt = GroundTruthWriter.from_ground_truth(gt, image_width=794, image_height=1123)
    assert isinstance(egt, EnhancedGroundTruth)


def test_from_ground_truth_computes_bbox_pixels():
    # box: [[10,20],[200,20],[200,50],[10,50]]
    # axis-aligned: x=10, y=20, w=190, h=30
    gt = _make_ground_truth()
    egt = GroundTruthWriter.from_ground_truth(gt, image_width=794, image_height=1123)
    bbox = egt.fields[0].bbox_pixels
    assert len(bbox) == 4
    assert bbox[0] == pytest.approx(10.0)
    assert bbox[1] == pytest.approx(20.0)
    assert bbox[2] == pytest.approx(190.0)
    assert bbox[3] == pytest.approx(30.0)


def test_from_ground_truth_computes_bbox_normalized():
    gt = _make_ground_truth()
    egt = GroundTruthWriter.from_ground_truth(gt, image_width=794, image_height=1123)
    nb = egt.fields[0].bbox_normalized
    assert len(nb) == 4
    assert nb[0] == pytest.approx(10.0 / 794, rel=1e-4)
    assert nb[1] == pytest.approx(20.0 / 1123, rel=1e-4)
    assert nb[2] == pytest.approx(190.0 / 794, rel=1e-4)
    assert nb[3] == pytest.approx(30.0 / 1123, rel=1e-4)


def test_from_ground_truth_sets_schema_version_2():
    gt = _make_ground_truth()
    egt = GroundTruthWriter.from_ground_truth(gt, image_width=794, image_height=1123)
    assert egt.schema_version == "2.0"


def test_from_ground_truth_maps_label_to_field_name():
    region = _make_text_region(label="merchant_name", text="Acme Corp")
    gt = _make_ground_truth(regions=[region])
    egt = GroundTruthWriter.from_ground_truth(gt, image_width=794, image_height=1123)
    assert egt.fields[0].field_name == "merchant_name"


def test_from_ground_truth_preserves_confidence():
    region = _make_text_region(confidence=0.85)
    gt = _make_ground_truth(regions=[region])
    egt = GroundTruthWriter.from_ground_truth(gt, image_width=794, image_height=1123)
    assert egt.fields[0].confidence == pytest.approx(0.85)


def test_from_ground_truth_includes_font_info():
    region = _make_text_region(font_family="handwriting", font_size=14, font_color="#1a1a1a")
    gt = _make_ground_truth(regions=[region])
    egt = GroundTruthWriter.from_ground_truth(gt, image_width=794, image_height=1123)
    fi = egt.fields[0].font_info
    assert fi["family"] == "handwriting"
    assert fi["size"] == 14
    assert fi["color"] == "#1a1a1a"


def test_from_ground_truth_preserves_quad():
    box = [[5.0, 10.0], [100.0, 10.0], [100.0, 40.0], [5.0, 40.0]]
    region = _make_text_region(box=box)
    gt = _make_ground_truth(regions=[region])
    egt = GroundTruthWriter.from_ground_truth(gt, image_width=794, image_height=1123)
    assert egt.fields[0].quad_pixels == box


def test_from_ground_truth_multiple_regions():
    r1 = _make_text_region(text="Jane Doe", label="name")
    r2 = _make_text_region(
        box=[[10.0, 100.0], [300.0, 100.0], [300.0, 140.0], [10.0, 140.0]],
        text="2026-04-06",
        label="date",
    )
    gt = _make_ground_truth(regions=[r1, r2])
    egt = GroundTruthWriter.from_ground_truth(gt, image_width=794, image_height=1123)
    assert len(egt.fields) == 2


# ---------------------------------------------------------------------------
# GroundTruthWriter.write_sidecar
# ---------------------------------------------------------------------------


def test_write_sidecar_creates_json_file(tmp_path):
    gt = _make_ground_truth()
    egt = GroundTruthWriter.from_ground_truth(gt, image_width=794, image_height=1123)
    out = tmp_path / "doc_000001_gt.json"
    GroundTruthWriter.write_sidecar(egt, out)
    assert out.exists()


def test_write_sidecar_readable_back(tmp_path):
    gt = _make_ground_truth()
    egt = GroundTruthWriter.from_ground_truth(gt, image_width=794, image_height=1123)
    out = tmp_path / "doc_000001_gt.json"
    GroundTruthWriter.write_sidecar(egt, out)
    with open(out) as f:
        data = json.load(f)
    assert data["schema_version"] == "2.0"
    assert "fields" in data


def test_write_sidecar_fields_contain_bbox_pixels(tmp_path):
    gt = _make_ground_truth()
    egt = GroundTruthWriter.from_ground_truth(gt, image_width=794, image_height=1123)
    out = tmp_path / "doc.json"
    GroundTruthWriter.write_sidecar(egt, out)
    with open(out) as f:
        data = json.load(f)
    assert "bbox_pixels" in data["fields"][0]
    assert len(data["fields"][0]["bbox_pixels"]) == 4


def test_write_sidecar_confidence_round_trips(tmp_path):
    region = _make_text_region(confidence=0.7)
    gt = _make_ground_truth(regions=[region])
    egt = GroundTruthWriter.from_ground_truth(gt, image_width=794, image_height=1123)
    out = tmp_path / "doc.json"
    GroundTruthWriter.write_sidecar(egt, out)
    with open(out) as f:
        data = json.load(f)
    assert data["fields"][0]["confidence"] == pytest.approx(0.7)


# ---------------------------------------------------------------------------
# GroundTruthWriter.write_jsonl
# ---------------------------------------------------------------------------


def test_write_jsonl_creates_file(tmp_path):
    records = [
        GroundTruthWriter.from_ground_truth(_make_ground_truth(image_path=f"doc_{i}.png"), 794, 1123)
        for i in range(3)
    ]
    out = tmp_path / "manifest.jsonl"
    GroundTruthWriter.write_jsonl(records, out)
    assert out.exists()


def test_write_jsonl_creates_one_line_per_record(tmp_path):
    n = 5
    records = [
        GroundTruthWriter.from_ground_truth(_make_ground_truth(image_path=f"doc_{i}.png"), 794, 1123)
        for i in range(n)
    ]
    out = tmp_path / "manifest.jsonl"
    GroundTruthWriter.write_jsonl(records, out)
    lines = [l for l in out.read_text().splitlines() if l.strip()]
    assert len(lines) == n


def test_write_jsonl_each_line_is_valid_json(tmp_path):
    records = [
        GroundTruthWriter.from_ground_truth(_make_ground_truth(image_path=f"doc_{i}.png"), 794, 1123)
        for i in range(3)
    ]
    out = tmp_path / "manifest.jsonl"
    GroundTruthWriter.write_jsonl(records, out)
    for line in out.read_text().splitlines():
        if line.strip():
            obj = json.loads(line)
            assert "schema_version" in obj


def test_write_jsonl_empty_list_creates_empty_file(tmp_path):
    out = tmp_path / "manifest.jsonl"
    GroundTruthWriter.write_jsonl([], out)
    assert out.exists()
    assert out.read_text().strip() == ""


# ---------------------------------------------------------------------------
# GroundTruthWriter.write_coco
# ---------------------------------------------------------------------------


def test_write_coco_creates_file(tmp_path):
    records = [
        GroundTruthWriter.from_ground_truth(_make_ground_truth(image_path=f"doc_{i}.png"), 794, 1123)
        for i in range(2)
    ]
    out = tmp_path / "coco.json"
    GroundTruthWriter.write_coco(records, out)
    assert out.exists()


def test_write_coco_has_images_and_annotations_keys(tmp_path):
    records = [
        GroundTruthWriter.from_ground_truth(_make_ground_truth(), 794, 1123)
    ]
    out = tmp_path / "coco.json"
    GroundTruthWriter.write_coco(records, out)
    with open(out) as f:
        data = json.load(f)
    assert "images" in data
    assert "annotations" in data
    assert "categories" in data
    assert "info" in data


def test_write_coco_annotation_count_matches_fields(tmp_path):
    r1 = _make_text_region(text="Jane Doe", label="name")
    r2 = _make_text_region(
        box=[[10.0, 100.0], [300.0, 100.0], [300.0, 140.0], [10.0, 140.0]],
        text="2026-04-06",
        label="date",
    )
    gt = _make_ground_truth(regions=[r1, r2])
    records = [GroundTruthWriter.from_ground_truth(gt, 794, 1123)]
    out = tmp_path / "coco.json"
    GroundTruthWriter.write_coco(records, out)
    with open(out) as f:
        data = json.load(f)
    assert len(data["annotations"]) == 2


def test_write_coco_bbox_is_xywh(tmp_path):
    records = [GroundTruthWriter.from_ground_truth(_make_ground_truth(), 794, 1123)]
    out = tmp_path / "coco.json"
    GroundTruthWriter.write_coco(records, out)
    with open(out) as f:
        data = json.load(f)
    bbox = data["annotations"][0]["bbox"]
    assert len(bbox) == 4
    # x, y, w, h — w and h must be positive
    assert bbox[2] > 0
    assert bbox[3] > 0


def test_write_coco_image_ids_match_annotation_image_ids(tmp_path):
    records = [
        GroundTruthWriter.from_ground_truth(_make_ground_truth(image_path=f"doc_{i}.png"), 794, 1123)
        for i in range(2)
    ]
    out = tmp_path / "coco.json"
    GroundTruthWriter.write_coco(records, out)
    with open(out) as f:
        data = json.load(f)
    image_ids = {img["id"] for img in data["images"]}
    annotation_image_ids = {ann["image_id"] for ann in data["annotations"]}
    assert annotation_image_ids.issubset(image_ids)


def test_write_coco_text_field_present(tmp_path):
    records = [GroundTruthWriter.from_ground_truth(_make_ground_truth(), 794, 1123)]
    out = tmp_path / "coco.json"
    GroundTruthWriter.write_coco(records, out)
    with open(out) as f:
        data = json.load(f)
    assert "text" in data["annotations"][0]
    assert data["annotations"][0]["text"] == "Jane Doe"
