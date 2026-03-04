"""Ground truth data models and loaders."""

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, field_validator


class TextRegion(BaseModel):
    """A single detected text region with bounding box."""

    # Quadrilateral: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    box: List[List[float]]
    text: str
    confidence: float = 1.0

    @field_validator("box")
    @classmethod
    def validate_box(cls, v: List[List[float]]) -> List[List[float]]:
        if len(v) != 4:
            raise ValueError("box must contain exactly 4 points")
        for pt in v:
            if len(pt) != 2:
                raise ValueError("Each point must have exactly 2 coordinates (x, y)")
        return v

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"confidence must be in [0, 1], got {v}")
        return v


class GroundTruth(BaseModel):
    """Ground truth annotation for a single document image."""

    image_path: str
    text: str
    regions: List[TextRegion] = []

    @property
    def full_text(self) -> str:
        """All region texts joined by newlines (falls back to .text)."""
        if self.regions:
            return "\n".join(r.text for r in self.regions)
        return self.text


class GroundTruthLoader:
    """Load ground truth annotations from JSON or ICDAR XML."""

    @staticmethod
    def load_json(path: Path) -> GroundTruth:
        """Load ground truth from a JSON file.

        Expected schema::

            {
              "image_path": "path/to/image.jpg",
              "text": "full document text",
              "regions": [
                {"box": [[x1,y1],[x2,y2],[x3,y3],[x4,y4]], "text": "...", "confidence": 1.0}
              ]
            }

        Args:
            path: Path to the JSON file.

        Returns:
            :class:`GroundTruth` instance.
        """
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        return GroundTruth(**data)

    @staticmethod
    def load_xml(path: Path) -> GroundTruth:
        """Load ground truth from an ICDAR-style XML file.

        Expected root element ``<document>`` with optional ``image`` attribute
        and ``<text_region>`` children containing ``<coords>`` and ``<text>``::

            <document image="img.jpg">
              <text_region>
                <coords x1="0" y1="0" x2="100" y2="0" x3="100" y3="20" x4="0" y4="20"/>
                <text>Hello</text>
              </text_region>
            </document>

        Args:
            path: Path to the XML file.

        Returns:
            :class:`GroundTruth` instance.
        """
        tree = ET.parse(path)
        root = tree.getroot()
        image_path = root.get("image", "")
        regions: List[TextRegion] = []

        for region_el in root.findall("text_region"):
            coords_el = region_el.find("coords")
            text_el = region_el.find("text")
            if coords_el is None or text_el is None:
                continue

            box = [
                [float(coords_el.get("x1", 0)), float(coords_el.get("y1", 0))],
                [float(coords_el.get("x2", 0)), float(coords_el.get("y2", 0))],
                [float(coords_el.get("x3", 0)), float(coords_el.get("y3", 0))],
                [float(coords_el.get("x4", 0)), float(coords_el.get("y4", 0))],
            ]
            text = text_el.text or ""
            confidence = float(region_el.get("confidence", 1.0))
            regions.append(TextRegion(box=box, text=text, confidence=confidence))

        full_text = "\n".join(r.text for r in regions)
        return GroundTruth(image_path=image_path, text=full_text, regions=regions)

    @staticmethod
    def detect_and_load(path: Path) -> GroundTruth:
        """Auto-detect format from file extension and load.

        Args:
            path: Path to a ``.json`` or ``.xml`` file.

        Returns:
            :class:`GroundTruth` instance.

        Raises:
            ValueError: If the format cannot be determined.
        """
        suffix = path.suffix.lower()
        if suffix == ".json":
            return GroundTruthLoader.load_json(path)
        if suffix == ".xml":
            return GroundTruthLoader.load_xml(path)
        raise ValueError(
            f"Cannot determine ground truth format from extension '{suffix}'. "
            "Expected '.json' or '.xml'."
        )
