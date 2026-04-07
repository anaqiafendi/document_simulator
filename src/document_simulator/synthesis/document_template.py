"""DocumentTemplate — encapsulates a named document layout with variable-length sections.

A DocumentTemplate knows how to:
1. Materialise all its sections (resolving repeating row counts).
2. Compute the total document height dynamically.
3. Return a SynthesisConfig that the existing SyntheticDocumentGenerator can consume.

Usage::

    from document_simulator.synthesis.templates.receipt_thermal import receipt_thermal_template

    config = receipt_thermal_template.to_synthesis_config(num_line_items=7, seed=42)
    gen = SyntheticDocumentGenerator(template="blank", synthesis_config=config)
    img, gt = gen.generate_one(seed=42)
"""

from __future__ import annotations

from document_simulator.synthesis.sections import RepeatingSection, Section, StaticSection
from document_simulator.synthesis.zones import (
    GeneratorConfig,
    RespondentConfig,
    SynthesisConfig,
    ZoneConfig,
)


class DocumentTemplate:
    """A named document layout composed of ordered sections.

    Args:
        document_type: Logical document category (e.g. "receipt", "invoice").
        style_name:    Visual variant within the category (e.g. "thermal", "a4").
        sections:      Ordered list of Section objects (StaticSection or
                       RepeatingSection).  Top-Y positions on each section are
                       used as relative offsets; the template recomputes absolute
                       Y positions when materialising.
        respondents:   RespondentConfig list to include in the SynthesisConfig.
        image_width:   Canvas width in pixels.
        base_seed:     Optional default seed offset.

    Note:
        The sections should be defined with ``top_y=0`` for each; the template
        stacks them vertically and recalculates absolute top_y values at
        materialise time.  If a section was defined with a non-zero top_y it is
        treated as a pre-set offset *from* the previous section's bottom — i.e.
        it acts as extra vertical padding.
    """

    def __init__(
        self,
        document_type: str,
        style_name: str,
        sections: list[Section],
        respondents: list[RespondentConfig],
        image_width: int = 794,
        base_seed: int = 0,
    ) -> None:
        self.document_type = document_type
        self.style_name = style_name
        self.sections = sections
        self.respondents = respondents
        self.image_width = image_width
        self.base_seed = base_seed

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _materialise_all(
        self,
        seed: int,
        num_line_items: int | None = None,
    ) -> tuple[list[ZoneConfig], float]:
        """Materialise all sections, stacking them vertically.

        Returns:
            (flat_zones, total_height) — all zones with absolute Y coordinates
            and the computed total document height.
        """
        flat_zones: list[ZoneConfig] = []
        cursor_y: float = 0.0

        for section in self.sections:
            # Determine how many rows for RepeatingSection
            if isinstance(section, RepeatingSection):
                # Pass top_y_override=cursor_y so that the section places rows
                # starting at cursor_y regardless of section.top_y.
                materialized = section.materialise(
                    seed=seed,
                    num_rows_override=num_line_items,
                    top_y_override=cursor_y,
                )
                num_rows = len(materialized) // max(len(section.row_template), 1)
                section_h = section.computed_height(num_rows)
            elif isinstance(section, StaticSection):
                # Create a temporary offset-aware copy at cursor_y
                tmp = StaticSection(
                    section_id=section.section_id,
                    zones=section._zones,
                    top_y=cursor_y,
                )
                materialized = tmp.materialise(seed=seed)
                section_h = section.height
            else:
                # Generic fallback
                materialized = section.materialise(seed=seed)
                section_h = section.height

            flat_zones.extend(materialized)
            cursor_y += section_h

        return flat_zones, cursor_y

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def to_synthesis_config(
        self,
        num_line_items: int | None = None,
        seed: int = 42,
    ) -> SynthesisConfig:
        """Build a SynthesisConfig from this template.

        Args:
            num_line_items: Override the number of line items in any
                            RepeatingSection. When None, the count is sampled
                            from each section's num_rows_range using *seed*.
            seed:           Controls both zone content (passed to ZoneDataSampler)
                            and dynamic row count sampling.

        Returns:
            A SynthesisConfig with dynamic image_height, all zones materialised,
            and respondents from this template.
        """
        flat_zones, total_height = self._materialise_all(
            seed=seed,
            num_line_items=num_line_items,
        )
        gen_config = GeneratorConfig(
            n=1,
            seed=seed,
            image_width=self.image_width,
            image_height=int(round(total_height)),
        )
        return SynthesisConfig(
            respondents=self.respondents,
            zones=flat_zones,
            generator=gen_config,
        )
