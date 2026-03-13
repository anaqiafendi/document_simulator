"""AnnotationBuilder — builds GroundTruth objects from rendered zone data and saves them as JSON."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from document_simulator.data.ground_truth import GroundTruth, TextRegion


class AnnotationBuilder:
    """Construct and persist GroundTruth annotations for synthetic documents."""

    @staticmethod
    def build(
        image_path: str,
        rendered_regions: list[dict],
        seed: Optional[int] = None,
    ) -> GroundTruth:
        """Build a GroundTruth from a list of rendered region dicts.

        Each dict in *rendered_regions* should contain:
        - ``"box"``           — list of 4 [x, y] corner points
        - ``"text"``          — the rendered text string
        - ``"page"``          — 0-indexed PDF page (default 0)
        - ``"label"``         — zone label
        - ``"faker_provider"``— data category (name, address, …)
        - ``"respondent"``    — respondent_id
        - ``"field_type"``    — field_type_id
        - ``"font_family"``   — resolved font category
        - ``"font_size"``     — resolved font size in px
        - ``"font_color"``    — CSS hex colour
        - ``"alignment"``     — left | center | right
        - ``"fill_style"``    — typed | form-fill | handwritten-font | stamp
        """
        regions = [
            TextRegion(
                box=r["box"],
                text=r["text"],
                confidence=1.0,
                page=r.get("page", 0),
                label=r.get("label", ""),
                faker_provider=r.get("faker_provider", ""),
                respondent_id=r.get("respondent", ""),
                field_type_id=r.get("field_type", ""),
                font_family=r.get("font_family", ""),
                font_size=r.get("font_size", 0),
                font_color=r.get("font_color", ""),
                alignment=r.get("alignment", "left"),
                fill_style=r.get("fill_style", "typed"),
            )
            for r in rendered_regions
        ]
        full_text = "\n".join(r.text for r in regions)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return GroundTruth(
            image_path=image_path,
            text=full_text,
            regions=regions,
            synthetic=True,
            seed=seed,
            generation_timestamp=timestamp,
        )

    @staticmethod
    def save(gt: GroundTruth, path: str | Path) -> None:
        """Serialise *gt* to a JSON file at *path* in the standard GroundTruth format."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(gt.model_dump(), f, indent=2, ensure_ascii=False)
