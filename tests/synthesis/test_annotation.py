"""Unit tests for AnnotationBuilder (annotation.py)."""

import json
import tempfile
from pathlib import Path

import pytest

from document_simulator.data.ground_truth import GroundTruth, GroundTruthLoader, TextRegion
from document_simulator.synthesis.annotation import AnnotationBuilder


def _make_regions() -> list[dict]:
    return [
        {
            "box": [[10, 20], [200, 20], [200, 50], [10, 50]],
            "text": "Jane Doe",
            "respondent": "person_a",
            "field_type": "standard",
        },
        {
            "box": [[10, 100], [300, 100], [300, 140], [10, 140]],
            "text": "J.D.",
            "respondent": "person_a",
            "field_type": "signature",
        },
    ]


def test_annotation_builder_returns_ground_truth():
    regions = _make_regions()
    gt = AnnotationBuilder.build(image_path="doc_000001.png", rendered_regions=regions)
    assert isinstance(gt, GroundTruth)


def test_annotation_builder_regions_match_input():
    regions = _make_regions()
    gt = AnnotationBuilder.build(image_path="doc_000001.png", rendered_regions=regions)
    assert len(gt.regions) == 2
    assert gt.regions[0].text == "Jane Doe"
    assert gt.regions[1].text == "J.D."


def test_annotation_builder_full_text_joins_regions():
    regions = _make_regions()
    gt = AnnotationBuilder.build(image_path="doc_000001.png", rendered_regions=regions)
    assert "Jane Doe" in gt.full_text
    assert "J.D." in gt.full_text


def test_annotation_builder_save_creates_json(tmp_path):
    regions = _make_regions()
    gt = AnnotationBuilder.build(image_path="doc_000001.png", rendered_regions=regions)
    json_path = tmp_path / "doc_000001.json"
    AnnotationBuilder.save(gt, json_path)
    assert json_path.exists()


def test_annotation_builder_saved_json_readable_by_loader(tmp_path):
    regions = _make_regions()
    gt = AnnotationBuilder.build(image_path="doc_000001.png", rendered_regions=regions)
    json_path = tmp_path / "doc_000001.json"
    AnnotationBuilder.save(gt, json_path)
    loaded = GroundTruthLoader.load_json(json_path)
    assert isinstance(loaded, GroundTruth)
    assert loaded.regions[0].text == "Jane Doe"


def test_annotation_builder_region_boxes_preserved(tmp_path):
    regions = _make_regions()
    gt = AnnotationBuilder.build(image_path="doc_000001.png", rendered_regions=regions)
    assert gt.regions[0].box == [[10, 20], [200, 20], [200, 50], [10, 50]]
