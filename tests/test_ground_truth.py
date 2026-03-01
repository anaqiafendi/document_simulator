"""Tests for ground truth data models and loaders."""

import json
import textwrap

import pytest

from document_simulator.data.ground_truth import (
    GroundTruth,
    GroundTruthLoader,
    TextRegion,
)

VALID_BOX = [[0.0, 0.0], [100.0, 0.0], [100.0, 20.0], [0.0, 20.0]]


# ---------------------------------------------------------------------------
# TextRegion model
# ---------------------------------------------------------------------------

def test_text_region_valid():
    r = TextRegion(box=VALID_BOX, text="Hello", confidence=0.95)
    assert r.text == "Hello"
    assert r.confidence == pytest.approx(0.95)


def test_text_region_invalid_box_wrong_points():
    with pytest.raises(ValueError):
        TextRegion(box=[[0, 0], [1, 1]], text="x")


def test_text_region_invalid_confidence():
    with pytest.raises(ValueError):
        TextRegion(box=VALID_BOX, text="x", confidence=1.5)


def test_text_region_default_confidence():
    r = TextRegion(box=VALID_BOX, text="hi")
    assert r.confidence == 1.0


# ---------------------------------------------------------------------------
# GroundTruth model
# ---------------------------------------------------------------------------

def test_ground_truth_full_text_from_regions():
    gt = GroundTruth(
        image_path="img.jpg",
        text="",
        regions=[
            TextRegion(box=VALID_BOX, text="Line 1"),
            TextRegion(box=VALID_BOX, text="Line 2"),
        ],
    )
    assert "Line 1" in gt.full_text
    assert "Line 2" in gt.full_text


def test_ground_truth_full_text_fallback():
    gt = GroundTruth(image_path="img.jpg", text="Fallback text", regions=[])
    assert gt.full_text == "Fallback text"


# ---------------------------------------------------------------------------
# GroundTruthLoader — JSON
# ---------------------------------------------------------------------------

def test_load_json_ground_truth(tmp_path):
    data = {
        "image_path": "doc.jpg",
        "text": "Hello World",
        "regions": [
            {"box": VALID_BOX, "text": "Hello World", "confidence": 0.98}
        ],
    }
    p = tmp_path / "gt.json"
    p.write_text(json.dumps(data))
    gt = GroundTruthLoader.load_json(p)
    assert gt.image_path == "doc.jpg"
    assert gt.text == "Hello World"
    assert len(gt.regions) == 1
    assert gt.regions[0].text == "Hello World"


def test_load_json_no_regions(tmp_path):
    data = {"image_path": "x.jpg", "text": "Simple", "regions": []}
    p = tmp_path / "gt.json"
    p.write_text(json.dumps(data))
    gt = GroundTruthLoader.load_json(p)
    assert gt.regions == []


# ---------------------------------------------------------------------------
# GroundTruthLoader — XML
# ---------------------------------------------------------------------------

def test_load_xml_ground_truth(tmp_path):
    xml_content = textwrap.dedent("""\
        <document image="form.jpg">
            <text_region>
                <coords x1="0" y1="0" x2="100" y2="0" x3="100" y3="20" x4="0" y4="20"/>
                <text>Invoice</text>
            </text_region>
            <text_region confidence="0.9">
                <coords x1="0" y1="30" x2="80" y2="30" x3="80" y3="50" x4="0" y4="50"/>
                <text>Total: $42</text>
            </text_region>
        </document>
    """)
    p = tmp_path / "gt.xml"
    p.write_text(xml_content)
    gt = GroundTruthLoader.load_xml(p)
    assert gt.image_path == "form.jpg"
    assert len(gt.regions) == 2
    assert gt.regions[0].text == "Invoice"
    assert gt.regions[1].confidence == pytest.approx(0.9)


# ---------------------------------------------------------------------------
# GroundTruthLoader — auto-detect
# ---------------------------------------------------------------------------

def test_detect_and_load_json(tmp_path):
    data = {"image_path": "x.jpg", "text": "hi", "regions": []}
    p = tmp_path / "gt.json"
    p.write_text(json.dumps(data))
    gt = GroundTruthLoader.detect_and_load(p)
    assert isinstance(gt, GroundTruth)


def test_detect_and_load_xml(tmp_path):
    xml_content = '<document image="x.jpg"></document>'
    p = tmp_path / "gt.xml"
    p.write_text(xml_content)
    gt = GroundTruthLoader.detect_and_load(p)
    assert isinstance(gt, GroundTruth)


def test_detect_and_load_unknown_extension(tmp_path):
    p = tmp_path / "gt.txt"
    p.write_text("unknown")
    with pytest.raises(ValueError):
        GroundTruthLoader.detect_and_load(p)
