"""AnnotationBuilder — builds GroundTruth objects from rendered zone data and saves them as JSON."""

from __future__ import annotations

import json
from pathlib import Path

from document_simulator.data.ground_truth import GroundTruth, TextRegion


class AnnotationBuilder:
    """Construct and persist GroundTruth annotations for synthetic documents."""

    @staticmethod
    def build(
        image_path: str,
        rendered_regions: list[dict],
    ) -> GroundTruth:
        """Build a GroundTruth from a list of rendered region dicts.

        Each dict in *rendered_regions* must contain:
        - ``"box"``      — list of 4 [x, y] corner points
        - ``"text"``     — the rendered text string
        - ``"respondent"`` (optional) — respondent_id
        - ``"field_type"`` (optional) — field_type_id
        """
        regions = [
            TextRegion(box=r["box"], text=r["text"], confidence=1.0)
            for r in rendered_regions
        ]
        full_text = "\n".join(r.text for r in regions)
        return GroundTruth(image_path=image_path, text=full_text, regions=regions)

    @staticmethod
    def save(gt: GroundTruth, path: str | Path) -> None:
        """Serialise *gt* to a JSON file at *path* in the standard GroundTruth format."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(gt.model_dump(), f, indent=2, ensure_ascii=False)
