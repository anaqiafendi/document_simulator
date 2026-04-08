"""Integration tests for enhanced generator ground truth output."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image

from document_simulator.synthesis.batch_integrity import BatchIntegrityChecker
from document_simulator.synthesis.generator import SyntheticDocumentGenerator
from document_simulator.synthesis.zones import (
    FieldTypeConfig,
    GeneratorConfig,
    RespondentConfig,
    SynthesisConfig,
    ZoneConfig,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_config(output_dir: str, n: int = 2) -> SynthesisConfig:
    field_type = FieldTypeConfig(field_type_id="standard", display_name="Standard")
    respondent = RespondentConfig(
        respondent_id="default",
        display_name="Default",
        field_types=[field_type],
    )
    zone = ZoneConfig(
        zone_id="z1",
        label="merchant_name",
        box=[[10.0, 20.0], [200.0, 20.0], [200.0, 50.0], [10.0, 50.0]],
        respondent_id="default",
        field_type_id="standard",
        faker_provider="company",
    )
    generator_cfg = GeneratorConfig(n=n, seed=42, output_dir=output_dir, image_width=200, image_height=200)
    return SynthesisConfig(
        respondents=[respondent],
        zones=[zone],
        generator=generator_cfg,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_generate_write_produces_enhanced_sidecar(tmp_path):
    config = _make_config(str(tmp_path), n=2)
    gen = SyntheticDocumentGenerator(template="blank", synthesis_config=config)
    gen.generate(n=2, write=True)

    json_files = list(tmp_path.glob("*.json"))
    # Exclude synthesis_config.json
    gt_files = [f for f in json_files if f.stem.startswith("doc_")]
    assert len(gt_files) == 2

    for gt_file in gt_files:
        with open(gt_file) as f:
            data = json.load(f)
        assert "schema_version" in data
        assert data["schema_version"] == "2.0"
        assert "fields" in data
        assert "image_width" in data
        assert "image_height" in data


def test_generate_write_manifest_creates_jsonl(tmp_path):
    config = _make_config(str(tmp_path), n=2)
    gen = SyntheticDocumentGenerator(template="blank", synthesis_config=config)
    gen.generate(n=2, write=True, write_manifest=True)

    manifest = tmp_path / "batch_manifest.jsonl"
    assert manifest.exists()
    lines = [l for l in manifest.read_text().splitlines() if l.strip()]
    assert len(lines) == 2
    for line in lines:
        obj = json.loads(line)
        assert "schema_version" in obj


def test_generate_write_coco_creates_coco_json(tmp_path):
    config = _make_config(str(tmp_path), n=2)
    gen = SyntheticDocumentGenerator(template="blank", synthesis_config=config)
    gen.generate(n=2, write=True, write_coco=True)

    coco_file = tmp_path / "coco_annotations.json"
    assert coco_file.exists()
    with open(coco_file) as f:
        data = json.load(f)
    assert "images" in data
    assert "annotations" in data
    assert len(data["images"]) == 2


def test_batch_integrity_passes_after_generate(tmp_path):
    config = _make_config(str(tmp_path), n=3)
    gen = SyntheticDocumentGenerator(template="blank", synthesis_config=config)
    gen.generate(n=3, write=True)

    report = BatchIntegrityChecker.check(tmp_path, expected_n=3, ext=".png")
    assert report.ok is True


def test_generate_no_write_returns_pairs(tmp_path):
    """generate() without write=True still returns (image, gt) pairs."""
    config = _make_config(str(tmp_path), n=2)
    gen = SyntheticDocumentGenerator(template="blank", synthesis_config=config)
    pairs = gen.generate(n=2, write=False)
    assert len(pairs) == 2
    for img, gt in pairs:
        assert isinstance(img, Image.Image)
