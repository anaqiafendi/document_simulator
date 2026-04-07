"""Tests for variable-length multi-template document generation (Feature #27).

TDD: these tests were written before the implementation. They cover all 10 ACs
listed in the FDD (feature_variable_length_templates.md).
"""

from __future__ import annotations

import pytest
from PIL import Image

from document_simulator.synthesis.document_template import DocumentTemplate
from document_simulator.synthesis.generator import SyntheticDocumentGenerator
from document_simulator.synthesis.sections import RepeatingSection, StaticSection
from document_simulator.synthesis.template_registry import TemplateRegistry
from document_simulator.synthesis.templates.receipt_a4 import receipt_a4_template
from document_simulator.synthesis.templates.receipt_thermal import receipt_thermal_template
from document_simulator.synthesis.zones import (
    FieldTypeConfig,
    GeneratorConfig,
    RespondentConfig,
    SynthesisConfig,
    ZoneConfig,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_zone(zone_id: str, y0: float = 0.0, y1: float = 20.0) -> ZoneConfig:
    """Create a minimal ZoneConfig at the given Y positions."""
    return ZoneConfig(
        zone_id=zone_id,
        label=zone_id,
        box=[[10, y0], [200, y0], [200, y1], [10, y1]],
        faker_provider="name",
    )


def _make_row_template() -> list[ZoneConfig]:
    """A two-column row template with relative Y=0."""
    return [
        _make_zone("item_name", y0=0, y1=20),
        _make_zone("item_price", y0=0, y1=20),
    ]


# ---------------------------------------------------------------------------
# AC-1 + AC-2: StaticSection
# ---------------------------------------------------------------------------


def test_static_section_materialises_same_zone_count():
    """AC-2: StaticSection with 3 zones → 3 materialised zones."""
    zones = [_make_zone(f"z{i}", y0=i * 30, y1=i * 30 + 20) for i in range(3)]
    sec = StaticSection(section_id="header", zones=zones, top_y=0)
    result = sec.materialise()
    assert len(result) == 3


def test_static_section_applies_top_y_offset():
    """AC-2: zones are shifted down by top_y."""
    zones = [_make_zone("z0", y0=0, y1=20)]
    sec = StaticSection(section_id="header", zones=zones, top_y=100)
    result = sec.materialise()
    # y-coordinates should all be shifted by 100
    assert result[0].box[0][1] == pytest.approx(100)
    assert result[0].box[1][1] == pytest.approx(100)
    assert result[0].box[2][1] == pytest.approx(120)
    assert result[0].box[3][1] == pytest.approx(120)


def test_static_section_zone_ids_preserved():
    """Zone IDs are kept intact after materialisation."""
    zones = [_make_zone("header_name")]
    sec = StaticSection(section_id="hdr", zones=zones, top_y=0)
    result = sec.materialise()
    assert result[0].zone_id == "header_name"


def test_static_section_height():
    """StaticSection.height equals the Y extent of its zones."""
    zones = [_make_zone("z0", y0=0, y1=25), _make_zone("z1", y0=25, y1=50)]
    sec = StaticSection(section_id="hdr", zones=zones, top_y=0)
    assert sec.height == pytest.approx(50)


# ---------------------------------------------------------------------------
# AC-1: RepeatingSection
# ---------------------------------------------------------------------------


def test_repeating_section_materialises_correct_row_count():
    """AC-1: 5 rows × 2-column template → 10 zone configs."""
    row_template = _make_row_template()
    sec = RepeatingSection(
        section_id="line_items",
        row_template=row_template,
        row_height=25,
        num_rows_range=(5, 5),  # fixed at 5 for determinism
        top_y=0,
    )
    result = sec.materialise(seed=0)
    assert len(result) == 5 * len(row_template)


def test_repeating_section_y_offsets_are_correct():
    """AC-1: second row starts at top_y + row_height."""
    row_template = _make_row_template()
    sec = RepeatingSection(
        section_id="line_items",
        row_template=row_template,
        row_height=30,
        num_rows_range=(3, 3),
        top_y=50,
    )
    result = sec.materialise(seed=0)
    # Row 0 → top_y = 50
    assert result[0].box[0][1] == pytest.approx(50)
    # Row 1 → top_y + row_height = 80
    assert result[2].box[0][1] == pytest.approx(80)
    # Row 2 → top_y + 2 * row_height = 110
    assert result[4].box[0][1] == pytest.approx(110)


def test_repeating_section_zone_ids_are_unique():
    """Each materialised zone has a unique zone_id (row suffix added)."""
    row_template = _make_row_template()
    sec = RepeatingSection(
        section_id="items",
        row_template=row_template,
        row_height=20,
        num_rows_range=(3, 3),
        top_y=0,
    )
    result = sec.materialise(seed=0)
    ids = [z.zone_id for z in result]
    assert len(ids) == len(set(ids)), "All zone_ids must be unique"


def test_repeating_section_num_rows_respects_range():
    """num_rows is sampled within the declared range."""
    row_template = _make_row_template()
    sec = RepeatingSection(
        section_id="items",
        row_template=row_template,
        row_height=20,
        num_rows_range=(2, 8),
        top_y=0,
    )
    counts = set()
    for seed in range(50):
        result = sec.materialise(seed=seed)
        num_rows = len(result) // len(row_template)
        counts.add(num_rows)
        assert 2 <= num_rows <= 8

    # With 50 seeds, we expect more than one distinct count
    assert len(counts) > 1, "num_rows should vary across seeds"


def test_repeating_section_height():
    """RepeatingSection.height(num_rows) == num_rows * row_height."""
    row_template = _make_row_template()
    sec = RepeatingSection(
        section_id="items",
        row_template=row_template,
        row_height=25,
        num_rows_range=(4, 4),
        top_y=0,
    )
    result = sec.materialise(seed=0)
    num_rows = len(result) // len(row_template)
    assert sec.computed_height(num_rows) == pytest.approx(100)


# ---------------------------------------------------------------------------
# AC-3 + AC-4: DocumentTemplate
# ---------------------------------------------------------------------------


def _simple_template() -> DocumentTemplate:
    """A minimal two-section template: static header + repeating items."""
    default_respondent = RespondentConfig(
        respondent_id="default",
        display_name="Default",
        field_types=[FieldTypeConfig(field_type_id="standard", display_name="Standard")],
    )
    header_section = StaticSection(
        section_id="header",
        zones=[_make_zone("merchant_name", y0=0, y1=30)],
        top_y=0,
    )
    items_section = RepeatingSection(
        section_id="line_items",
        row_template=_make_row_template(),
        row_height=25,
        num_rows_range=(2, 5),
        top_y=30,
    )
    return DocumentTemplate(
        document_type="receipt",
        style_name="simple",
        sections=[header_section, items_section],
        respondents=[default_respondent],
        image_width=300,
    )


def test_document_template_image_height_equals_sum_of_sections():
    """AC-3: generated SynthesisConfig image_height == total section heights."""
    tpl = _simple_template()
    config = tpl.to_synthesis_config(seed=42)
    # header = 30, items = num_rows * 25
    header_sec = tpl.sections[0]
    items_sec = tpl.sections[1]
    materialized_items = items_sec.materialise(seed=42)
    num_rows = len(materialized_items) // len(items_sec.row_template)
    expected_height = header_sec.height + items_sec.computed_height(num_rows)
    assert config.generator.image_height == pytest.approx(expected_height)


def test_document_template_is_deterministic():
    """AC-4: same seed → same zones, same height, same text content."""
    tpl = _simple_template()
    config_a = tpl.to_synthesis_config(seed=99)
    config_b = tpl.to_synthesis_config(seed=99)
    assert config_a.generator.image_height == config_b.generator.image_height
    assert len(config_a.zones) == len(config_b.zones)
    assert [z.zone_id for z in config_a.zones] == [z.zone_id for z in config_b.zones]


def test_document_template_different_seeds_may_differ():
    """Different seeds can produce different heights (when num_rows_range > 1)."""
    tpl = _simple_template()
    heights = {tpl.to_synthesis_config(seed=s).generator.image_height for s in range(30)}
    assert len(heights) > 1, "Expected height to vary with seed"


def test_document_template_num_line_items_override():
    """When num_line_items is passed explicitly it overrides sampling."""
    tpl = _simple_template()
    config = tpl.to_synthesis_config(num_line_items=4, seed=0)
    items_section = tpl.sections[1]
    cols = len(items_section.row_template)
    item_zones = [z for z in config.zones if "line_items" in z.zone_id]
    assert len(item_zones) == 4 * cols


# ---------------------------------------------------------------------------
# AC-5 + AC-6: TemplateRegistry
# ---------------------------------------------------------------------------


def test_registry_register_and_get():
    """AC-5: register then get retrieves the same template object."""
    reg = TemplateRegistry()
    tpl = _simple_template()
    reg.register("receipt", "simple", tpl)
    assert reg.get("receipt", "simple") is tpl


def test_registry_list_styles():
    """AC-5: list_styles returns registered style names for a document type."""
    reg = TemplateRegistry()
    reg.register("receipt", "thermal", _simple_template())
    reg.register("receipt", "a4", _simple_template())
    styles = reg.list_styles("receipt")
    assert "thermal" in styles
    assert "a4" in styles


def test_registry_list_types():
    """AC-5: list_types returns all registered document types."""
    reg = TemplateRegistry()
    reg.register("receipt", "thermal", _simple_template())
    reg.register("invoice", "standard", _simple_template())
    types = reg.list_types()
    assert "receipt" in types
    assert "invoice" in types


def test_registry_get_unknown_raises_key_error():
    """AC-6: unknown (type, style) raises KeyError."""
    reg = TemplateRegistry()
    with pytest.raises(KeyError):
        reg.get("receipt", "nonexistent_style")


def test_registry_list_styles_unknown_type_returns_empty():
    """list_styles for an unregistered type returns an empty list."""
    reg = TemplateRegistry()
    assert reg.list_styles("nonexistent") == []


# ---------------------------------------------------------------------------
# AC-7 + AC-8: Bundled templates
# ---------------------------------------------------------------------------


def test_receipt_thermal_template_valid_config():
    """AC-7: thermal template generates a SynthesisConfig with 2–12 line items."""
    for seed in range(10):
        config = receipt_thermal_template.to_synthesis_config(seed=seed)
        assert isinstance(config, SynthesisConfig)
        assert config.generator.image_height is not None
        assert config.generator.image_height > 0
        item_zones = [z for z in config.zones if "line_item" in z.zone_id]
        # Each row has at least 1 zone; num_rows in [2, 12]
        assert len(item_zones) >= 2


def test_receipt_a4_template_valid_config():
    """AC-8: A4 template generates a SynthesisConfig with 2–20 line items."""
    for seed in range(10):
        config = receipt_a4_template.to_synthesis_config(seed=seed)
        assert isinstance(config, SynthesisConfig)
        assert config.generator.image_height is not None
        assert config.generator.image_height > 0
        item_zones = [z for z in config.zones if "line_item" in z.zone_id]
        assert len(item_zones) >= 2


def test_receipt_thermal_num_line_items_override():
    """Explicit num_line_items=6 respected by thermal template."""
    config = receipt_thermal_template.to_synthesis_config(num_line_items=6, seed=0)
    # Count unique row indices from zone IDs
    item_zone_ids = [z.zone_id for z in config.zones if "line_item" in z.zone_id]
    # Check at least 6 row-tagged zones present (may have multiple cols per row)
    row_indices = {zid.rsplit("_row", 1)[-1] for zid in item_zone_ids if "_row" in zid}
    assert len(row_indices) == 6


# ---------------------------------------------------------------------------
# AC-9: Generator consumes template-derived SynthesisConfig
# ---------------------------------------------------------------------------


def test_generator_consumes_template_config():
    """AC-9: SyntheticDocumentGenerator produces an image with the correct height."""
    tpl = _simple_template()
    config = tpl.to_synthesis_config(num_line_items=3, seed=7)
    gen = SyntheticDocumentGenerator(template="blank", synthesis_config=config)
    img, gt = gen.generate_one(seed=7)
    assert isinstance(img, Image.Image)
    expected_h = config.generator.image_height
    assert img.height == expected_h


def test_generator_consumes_thermal_template():
    """AC-9 (bundled template): thermal receipt generates a valid image."""
    config = receipt_thermal_template.to_synthesis_config(num_line_items=4, seed=42)
    gen = SyntheticDocumentGenerator(template="blank", synthesis_config=config)
    img, gt = gen.generate_one(seed=42)
    assert isinstance(img, Image.Image)
    assert img.height == config.generator.image_height
    assert len(gt.regions) > 0


# ---------------------------------------------------------------------------
# AC-10: Backward compatibility — existing flat zones still work
# ---------------------------------------------------------------------------


def test_existing_flat_zones_still_work():
    """AC-10: a plain SynthesisConfig (no sections) works unchanged."""
    ft = FieldTypeConfig(field_type_id="standard", display_name="Standard")
    respondent = RespondentConfig(
        respondent_id="default",
        display_name="Default",
        field_types=[ft],
    )
    zones = [
        ZoneConfig(
            zone_id="name_field",
            label="name",
            box=[[10, 10], [200, 10], [200, 35], [10, 35]],
            faker_provider="name",
        ),
    ]
    config = SynthesisConfig(
        respondents=[respondent],
        zones=zones,
        generator=GeneratorConfig(n=1, seed=0),
    )
    gen = SyntheticDocumentGenerator(template="blank", synthesis_config=config)
    img, gt = gen.generate_one(seed=0)
    assert isinstance(img, Image.Image)
    assert len(gt.regions) == 1
