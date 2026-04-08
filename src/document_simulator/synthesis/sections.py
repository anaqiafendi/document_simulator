"""Section models for variable-length document layout.

A *Section* is a vertical block of a document that can contain a fixed set of
zones (StaticSection) or a dynamically repeating row (RepeatingSection).

Sections are composed into a DocumentTemplate, which computes the total document
height and materialises a flat list[ZoneConfig] that the existing rendering
engine can consume unchanged.
"""

from __future__ import annotations

import copy
import random
from abc import ABC, abstractmethod

from document_simulator.synthesis.zones import ZoneConfig


class Section(ABC):
    """Abstract base for a vertical block of a document layout."""

    def __init__(self, section_id: str, top_y: float = 0.0) -> None:
        self.section_id = section_id
        self.top_y = top_y

    @property
    @abstractmethod
    def height(self) -> float:
        """Fixed height of this section in document pixels.

        For RepeatingSection, use computed_height(num_rows) instead.
        This property returns the per-row height * min_rows as a safe lower bound
        so height is always defined.
        """

    @abstractmethod
    def materialise(self, seed: int = 0) -> list[ZoneConfig]:
        """Return a flat list of ZoneConfig with absolute document coordinates."""


# ---------------------------------------------------------------------------
# StaticSection
# ---------------------------------------------------------------------------


def _offset_zone(zone: ZoneConfig, dy: float) -> ZoneConfig:
    """Return a copy of *zone* with all Y coordinates shifted by *dy*."""
    new_box = [[pt[0], pt[1] + dy] for pt in zone.box]
    return zone.model_copy(update={"box": new_box})


class StaticSection(Section):
    """A section with a fixed set of pre-defined zones.

    Zones are stored with Y coordinates relative to the section top (y=0).
    When materialised, each zone is offset by ``top_y`` to produce absolute
    document coordinates.

    Args:
        section_id: Unique identifier for this section.
        zones:      List of ZoneConfig with Y coordinates starting from 0.
        top_y:      Absolute Y position of the top of this section in the document.

    Example::

        header = StaticSection(
            section_id="header",
            zones=[
                ZoneConfig(zone_id="merchant", label="merchant",
                           box=[[10,0],[300,0],[300,25],[10,25]],
                           faker_provider="company"),
            ],
            top_y=0,
        )
        zones = header.materialise()
    """

    def __init__(
        self,
        section_id: str,
        zones: list[ZoneConfig],
        top_y: float = 0.0,
    ) -> None:
        super().__init__(section_id=section_id, top_y=top_y)
        self._zones = zones

    @property
    def height(self) -> float:
        """Height of the section = max Y2 of any zone (relative to section top)."""
        if not self._zones:
            return 0.0
        max_y = 0.0
        for zone in self._zones:
            for pt in zone.box:
                if pt[1] > max_y:
                    max_y = pt[1]
        return max_y

    def materialise(self, seed: int = 0) -> list[ZoneConfig]:
        """Return zones with Y coordinates offset by top_y.

        Args:
            seed: Unused for static sections; accepted for API uniformity.

        Returns:
            List of ZoneConfig with absolute document Y coordinates.
        """
        return [_offset_zone(z, self.top_y) for z in self._zones]


# ---------------------------------------------------------------------------
# RepeatingSection
# ---------------------------------------------------------------------------


class RepeatingSection(Section):
    """A section that repeats a row template N times vertically.

    N is sampled from ``num_rows_range`` at materialise-time using the provided
    seed (reproducible). Each repeated row has its Y coordinates offset by
    ``top_y + row_index * row_height``, and each zone_id is suffixed with
    ``_row{row_index}`` to ensure uniqueness.

    Args:
        section_id:      Unique identifier for this section.
        row_template:    List of ZoneConfig forming one row, with Y starting at 0.
        row_height:      Height of one row in document pixels.
        num_rows_range:  (min_rows, max_rows) inclusive range for row count sampling.
        top_y:           Absolute Y position of the section top in the document.

    Example::

        items = RepeatingSection(
            section_id="line_items",
            row_template=[
                ZoneConfig(zone_id="item_name_row", label="item",
                           box=[[10,0],[180,0],[180,20],[10,20]],
                           faker_provider="word"),
                ZoneConfig(zone_id="item_price_row", label="price",
                           box=[[190,0],[280,0],[280,20],[190,20]],
                           faker_provider="price_short"),
            ],
            row_height=22,
            num_rows_range=(2, 10),
            top_y=80,
        )
        zones = items.materialise(seed=42)
    """

    def __init__(
        self,
        section_id: str,
        row_template: list[ZoneConfig],
        row_height: float,
        num_rows_range: tuple[int, int] = (1, 10),
        top_y: float = 0.0,
    ) -> None:
        super().__init__(section_id=section_id, top_y=top_y)
        self.row_template = row_template
        self.row_height = row_height
        self.num_rows_range = num_rows_range

    @property
    def height(self) -> float:
        """Lower-bound height: min_rows * row_height."""
        return self.num_rows_range[0] * self.row_height

    def computed_height(self, num_rows: int) -> float:
        """Exact height for a specific row count."""
        return num_rows * self.row_height

    def _sample_num_rows(self, seed: int, override: int | None = None) -> int:
        """Sample num_rows from range using seeded RNG, or use override."""
        if override is not None:
            lo, hi = self.num_rows_range
            return max(lo, min(hi, override))
        lo, hi = self.num_rows_range
        if lo == hi:
            return lo
        rng = random.Random(hash((seed, self.section_id, "num_rows")) & 0xFFFFFFFF)
        return rng.randint(lo, hi)

    def materialise(
        self,
        seed: int = 0,
        num_rows_override: int | None = None,
        top_y_override: float | None = None,
    ) -> list[ZoneConfig]:
        """Materialise all rows as a flat list of ZoneConfig.

        Args:
            seed:             Controls num_rows sampling and zone_id uniqueness suffix.
            num_rows_override: If provided, use this row count instead of sampling.
            top_y_override:   If provided, use this as the section top Y instead of
                              ``self.top_y``.  Used by DocumentTemplate when stacking
                              sections to avoid double-counting the section's stored top_y.

        Returns:
            Flat list of ZoneConfig with absolute document coordinates and unique IDs.
        """
        effective_top_y = self.top_y if top_y_override is None else top_y_override
        num_rows = self._sample_num_rows(seed, override=num_rows_override)
        result: list[ZoneConfig] = []
        for row_idx in range(num_rows):
            dy = effective_top_y + row_idx * self.row_height
            for zone in self.row_template:
                offset_zone = _offset_zone(zone, dy)
                # Make zone_id unique per row
                unique_id = f"{self.section_id}_{zone.zone_id}_row{row_idx}"
                offset_zone = offset_zone.model_copy(update={"zone_id": unique_id})
                result.append(offset_zone)
        return result
