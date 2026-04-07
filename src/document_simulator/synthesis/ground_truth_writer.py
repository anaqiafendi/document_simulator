"""GroundTruthWriter — enhanced GT schema with bbox normalization and multi-format export.

Adds:
- ``GroundTruthRecord``: per-field record with bbox_pixels, bbox_normalized, font_info, confidence
- ``EnhancedGroundTruth``: document-level record (schema_version="2.0")
- ``GroundTruthWriter``: converts existing GroundTruth → EnhancedGroundTruth and writes
  per-image JSON sidecar, JSONL batch manifest, COCO-format JSON.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from document_simulator.data.ground_truth import GroundTruth


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class GroundTruthRecord(BaseModel):
    """Per-field annotation record with normalized bounding box and font metadata.

    Attributes:
        field_name: Canonical field identifier (maps from zone ``label``).
        text_value: The rendered text string for this field.
        bbox_pixels: Axis-aligned bounding box ``[x, y, w, h]`` in pixel coordinates.
        bbox_normalized: Axis-aligned bounding box ``[x, y, w, h]`` normalised to ``[0, 1]``
            relative to the image width and height.
        font_info: Dictionary with keys ``family``, ``size``, ``color``, ``style``.
        confidence: 1.0 for synthetically generated fields; <1.0 for LLM-inferred fields.
        page: 0-indexed PDF page this field appears on.
        quad_pixels: Original quadrilateral ``[[x1,y1],[x2,y2],[x3,y3],[x4,y4]]`` in pixels.
    """

    field_name: str
    text_value: str
    bbox_pixels: list[float]  # [x, y, w, h]
    bbox_normalized: list[float]  # [x, y, w, h] in [0, 1]
    font_info: dict  # {"family": str, "size": int, "color": str, "style": str}
    confidence: float = 1.0
    page: int = 0
    quad_pixels: list[list[float]]  # [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]


class EnhancedGroundTruth(BaseModel):
    """Document-level ground truth with schema version and image dimensions.

    ``schema_version`` is always ``"2.0"`` for records produced by this module.
    """

    image_path: str
    image_width: int
    image_height: int
    synthetic: bool = True
    seed: Optional[int] = None
    generation_timestamp: Optional[str] = None
    schema_version: str = "2.0"
    fields: list[GroundTruthRecord] = []


# ---------------------------------------------------------------------------
# Writer
# ---------------------------------------------------------------------------


class GroundTruthWriter:
    """Convert :class:`~document_simulator.data.ground_truth.GroundTruth` to enhanced format
    and write per-image JSON sidecars, JSONL manifests, and COCO-format JSON.
    """

    @staticmethod
    def from_ground_truth(
        gt: GroundTruth,
        image_width: int,
        image_height: int,
    ) -> EnhancedGroundTruth:
        """Convert a :class:`GroundTruth` to :class:`EnhancedGroundTruth`.

        Computes ``bbox_pixels`` and ``bbox_normalized`` from the quad ``box`` of each
        :class:`~document_simulator.data.ground_truth.TextRegion`.

        Args:
            gt: Source ground truth produced by :class:`AnnotationBuilder`.
            image_width: Width of the raster image in pixels.
            image_height: Height of the raster image in pixels.

        Returns:
            :class:`EnhancedGroundTruth` with ``schema_version="2.0"``.
        """
        fields: list[GroundTruthRecord] = []
        for region in gt.regions:
            # Compute axis-aligned bounding box from quad
            xs = [pt[0] for pt in region.box]
            ys = [pt[1] for pt in region.box]
            x_min, x_max = min(xs), max(xs)
            y_min, y_max = min(ys), max(ys)
            w = x_max - x_min
            h = y_max - y_min

            bbox_pixels = [x_min, y_min, w, h]
            bbox_normalized = [
                x_min / image_width,
                y_min / image_height,
                w / image_width,
                h / image_height,
            ]

            font_info = {
                "family": region.font_family,
                "size": region.font_size,
                "color": region.font_color,
                "style": region.fill_style,
            }

            fields.append(
                GroundTruthRecord(
                    field_name=region.label,
                    text_value=region.text,
                    bbox_pixels=bbox_pixels,
                    bbox_normalized=bbox_normalized,
                    font_info=font_info,
                    confidence=region.confidence,
                    page=region.page,
                    quad_pixels=region.box,
                )
            )

        return EnhancedGroundTruth(
            image_path=gt.image_path,
            image_width=image_width,
            image_height=image_height,
            synthetic=gt.synthetic,
            seed=gt.seed,
            generation_timestamp=gt.generation_timestamp,
            schema_version="2.0",
            fields=fields,
        )

    @staticmethod
    def write_sidecar(egt: EnhancedGroundTruth, path: Path | str) -> None:
        """Write an :class:`EnhancedGroundTruth` as a JSON sidecar file.

        Args:
            egt: Enhanced ground truth record.
            path: Destination file path (parents are created if needed).
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(egt.model_dump(), f, indent=2, ensure_ascii=False)

    @staticmethod
    def write_jsonl(records: list[EnhancedGroundTruth], path: Path | str) -> None:
        """Write a list of :class:`EnhancedGroundTruth` records as a JSONL manifest.

        Each line in the output file is a complete JSON object for one document.

        Args:
            records: Batch of enhanced ground truth records.
            path: Destination ``.jsonl`` file path (parents are created if needed).
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            for record in records:
                f.write(record.model_dump_json() + "\n")

    @staticmethod
    def write_coco(records: list[EnhancedGroundTruth], path: Path | str) -> None:
        """Write a batch of :class:`EnhancedGroundTruth` records in COCO format.

        COCO structure::

            {
              "info": {...},
              "images": [{"id": int, "file_name": str, "width": int, "height": int}],
              "annotations": [
                {
                  "id": int, "image_id": int, "category_id": 1,
                  "bbox": [x, y, w, h],
                  "segmentation": [[x1,y1,x2,y2,x3,y3,x4,y4]],
                  "text": str,
                  "field_name": str,
                  "confidence": float,
                  "area": float,
                  "iscrowd": 0
                }
              ],
              "categories": [{"id": 1, "name": "text"}]
            }

        Args:
            records: Batch of enhanced ground truth records.
            path: Destination ``.json`` file path (parents are created if needed).
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        images = []
        annotations = []
        ann_id = 1

        for img_id, record in enumerate(records, start=1):
            images.append(
                {
                    "id": img_id,
                    "file_name": Path(record.image_path).name,
                    "width": record.image_width,
                    "height": record.image_height,
                }
            )
            for field in record.fields:
                x, y, w, h = field.bbox_pixels
                # Flatten quad to segmentation polygon [x1,y1,x2,y2,x3,y3,x4,y4]
                seg = [coord for pt in field.quad_pixels for coord in pt]
                annotations.append(
                    {
                        "id": ann_id,
                        "image_id": img_id,
                        "category_id": 1,
                        "bbox": [x, y, w, h],
                        "segmentation": [seg],
                        "text": field.text_value,
                        "field_name": field.field_name,
                        "confidence": field.confidence,
                        "area": w * h,
                        "iscrowd": 0,
                    }
                )
                ann_id += 1

        coco = {
            "info": {
                "description": "Document Simulator synthetic ground truth",
                "version": "1.0",
                "date_created": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
            "images": images,
            "annotations": annotations,
            "categories": [{"id": 1, "name": "text"}],
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(coco, f, indent=2, ensure_ascii=False)
