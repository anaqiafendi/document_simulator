"""Synthesis configuration models: FieldTypeConfig, RespondentConfig, ZoneConfig, SynthesisConfig."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator


class FieldTypeConfig(BaseModel):
    """Style profile for one kind of field a respondent fills in.

    e.g. a person might have a "standard" profile (typed, black ink) and a
    "signature" profile (handwriting font, bold, dark blue, larger size).
    """

    field_type_id: str
    display_name: str

    # Typography
    font_family: str = "sans-serif"  # serif | sans-serif | monospace | handwriting
    font_size_range: tuple[int, int] = (10, 14)
    font_color: str = "#000000"
    bold: bool = False
    italic: bool = False

    # Fill style
    fill_style: str = "typed"  # typed | form-fill | handwritten-font | stamp

    # Position variation
    jitter_x: float = 0.0
    jitter_y: float = 0.0
    baseline_wander: float = 0.0
    char_spacing_jitter: float = 0.0

    model_config = {"arbitrary_types_allowed": True}


class RespondentConfig(BaseModel):
    """One person filling in the form. Owns a list of FieldTypeConfig profiles."""

    respondent_id: str
    display_name: str
    field_types: list[FieldTypeConfig] = Field(default_factory=list)

    def get_field_type(self, field_type_id: str) -> FieldTypeConfig:
        for ft in self.field_types:
            if ft.field_type_id == field_type_id:
                return ft
        raise KeyError(f"FieldTypeConfig '{field_type_id}' not found in respondent '{self.respondent_id}'")

    @property
    def default_field_type(self) -> FieldTypeConfig:
        return self.field_types[0]


class ZoneConfig(BaseModel):
    """Lightweight zone — specifies what data goes where and which (respondent, field_type) fills it."""

    zone_id: str
    label: str
    box: list[list[float]]  # [[x1,y1],[x2,y2],[x3,y3],[x4,y4]] in document pixels
    respondent_id: str = "default"
    field_type_id: str = "standard"

    # Data generation
    faker_provider: str = "name"
    custom_values: list[str] = Field(default_factory=list)
    alignment: str = "left"  # left | center | right

    # Multi-page support: which PDF page (0-indexed) this zone belongs to
    page: int = 0


class GeneratorConfig(BaseModel):
    """Batch generation settings."""

    n: int = 1
    seed: int = 42
    output_dir: str = "output"
    image_width: int = 794   # A4 at 96 dpi
    image_height: int | None = 1123
    # When image_height is None the generator computes the canvas height
    # dynamically from the document sections.  Set explicitly by
    # DocumentTemplate.to_synthesis_config() once all sections are resolved.


def _default_respondent() -> RespondentConfig:
    return RespondentConfig(
        respondent_id="default",
        display_name="Default",
        field_types=[FieldTypeConfig(field_type_id="standard", display_name="Standard text")],
    )


class SynthesisConfig(BaseModel):
    """Top-level configuration for a synthetic document generation run."""

    respondents: list[RespondentConfig] = Field(default_factory=list)
    zones: list[ZoneConfig] = Field(default_factory=list)
    generator: GeneratorConfig = Field(default_factory=GeneratorConfig)

    @model_validator(mode="after")
    def ensure_default_respondent(self) -> "SynthesisConfig":
        if not self.respondents:
            self.respondents.append(_default_respondent())
        return self

    def get_respondent(self, respondent_id: str) -> RespondentConfig:
        for r in self.respondents:
            if r.respondent_id == respondent_id:
                return r
        raise KeyError(f"RespondentConfig '{respondent_id}' not found")
