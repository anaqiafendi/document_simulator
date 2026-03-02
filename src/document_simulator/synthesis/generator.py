"""SyntheticDocumentGenerator — orchestrates single and batch document generation."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from document_simulator.data.ground_truth import GroundTruth
from document_simulator.synthesis.annotation import AnnotationBuilder
from document_simulator.synthesis.renderer import StyleResolver, ZoneRenderer
from document_simulator.synthesis.sampler import ZoneDataSampler, generate_respondent
from document_simulator.synthesis.template import TemplateLoader
from document_simulator.synthesis.zones import SynthesisConfig


class SyntheticDocumentGenerator:
    """Generate synthetic filled-document images from a template and zone configuration.

    Usage::

        config = SynthesisConfig(respondents=[...], zones=[...])
        gen = SyntheticDocumentGenerator(template="blank", synthesis_config=config)
        pairs = gen.generate(n=100, write=True)
    """

    def __init__(
        self,
        template: str,
        synthesis_config: SynthesisConfig,
        template_kwargs: dict | None = None,
    ) -> None:
        self._template_source = template
        self._template_kwargs = template_kwargs or {}
        self._config = synthesis_config

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_one(self, seed: int) -> tuple[Image.Image, GroundTruth]:
        """Generate a single document image and its annotation."""
        canvas = TemplateLoader.load(self._template_source, **self._template_kwargs)
        resolver = StyleResolver(self._config, seed=seed)

        # Build one Faker identity per respondent (correlated fields)
        respondent_identities = {
            r.respondent_id: generate_respondent(r.respondent_id, global_seed=seed)
            for r in self._config.respondents
        }

        rendered_regions: list[dict] = []
        for zone in self._config.zones:
            style = resolver.resolve(zone.respondent_id, zone.field_type_id)
            identity = respondent_identities.get(
                zone.respondent_id,
                respondent_identities.get("default", {}),
            )
            text = ZoneDataSampler.sample(zone, identity, seed=seed)
            canvas = ZoneRenderer.draw(canvas, text, style, zone, seed=seed)
            rendered_regions.append(
                {
                    "box": zone.box,
                    "text": text,
                    "respondent": zone.respondent_id,
                    "field_type": zone.field_type_id,
                }
            )

        image_path = f"doc_{seed:06d}.png"
        gt = AnnotationBuilder.build(image_path=image_path, rendered_regions=rendered_regions)
        return canvas, gt

    def generate(
        self,
        n: int | None = None,
        write: bool = False,
    ) -> list[tuple[Image.Image, GroundTruth]]:
        """Generate *n* documents and optionally write PNG + JSON pairs to disk.

        If *n* is None, uses ``synthesis_config.generator.n``.
        If *write* is True, images and annotations are saved under
        ``synthesis_config.generator.output_dir``.
        """
        count = n if n is not None else self._config.generator.n
        base_seed = self._config.generator.seed
        output_dir = Path(self._config.generator.output_dir)

        pairs: list[tuple[Image.Image, GroundTruth]] = []
        for i in range(count):
            seed = base_seed + i
            img, gt = self.generate_one(seed=seed)
            pairs.append((img, gt))

            if write:
                output_dir.mkdir(parents=True, exist_ok=True)
                stem = f"doc_{i + 1:06d}"
                img_path = output_dir / f"{stem}.png"
                json_path = output_dir / f"{stem}.json"
                img.save(img_path)
                gt_with_path = gt.model_copy(update={"image_path": str(img_path)})
                AnnotationBuilder.save(gt_with_path, json_path)

        if write:
            config_path = output_dir / "synthesis_config.json"
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(self._config.model_dump_json(indent=2))

        return pairs
