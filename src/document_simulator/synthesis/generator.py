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

    PDF output
    ----------
    Pass ``pdf_bytes`` to preserve the original PDF structure with text written
    as native PDF text objects (via PyMuPDF) rather than rasterised pixels::

        with open("form.pdf", "rb") as f:
            pdf_bytes = f.read()

        gen = SyntheticDocumentGenerator(
            template=rendered_pil_image,
            synthesis_config=config,
            pdf_bytes=pdf_bytes,
        )
        img, gt, pdf_out = gen.generate_one_pdf(seed=42)
    """

    def __init__(
        self,
        template: str | Image.Image,
        synthesis_config: SynthesisConfig,
        template_kwargs: dict | None = None,
        pdf_bytes: bytes | None = None,
    ) -> None:
        self._template_source = template
        self._template_kwargs = template_kwargs or {}
        self._config = synthesis_config
        self._pdf_bytes = pdf_bytes  # original PDF for write-back (None = PNG output only)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_canvas(self) -> Image.Image:
        """Load or copy the base template image."""
        if isinstance(self._template_source, Image.Image):
            return self._template_source.copy().convert("RGB")
        return TemplateLoader.load(self._template_source, **self._template_kwargs)

    def _generate_internal(self, seed: int) -> tuple[Image.Image, list[dict]]:
        """Run the rendering pipeline.

        Returns:
            A ``(canvas, rendered_regions)`` pair where *rendered_regions* contains
            per-zone dicts with ``box``, ``text``, ``font_family``, ``font_size``,
            ``font_color``, ``respondent``, and ``field_type`` keys.
        """
        canvas = self._load_canvas()
        resolver = StyleResolver(self._config, seed=seed)

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
                    # Style info needed for PDF write-back
                    "font_family": style.font_family,
                    "font_size": style.font_size,
                    "font_color": style.font_color,
                }
            )

        return canvas, rendered_regions

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_one(self, seed: int) -> tuple[Image.Image, GroundTruth]:
        """Generate a single document image and its annotation."""
        canvas, rendered_regions = self._generate_internal(seed)
        image_path = f"doc_{seed:06d}.png"
        gt = AnnotationBuilder.build(image_path=image_path, rendered_regions=rendered_regions)
        return canvas, gt

    def generate_one_pdf(self, seed: int) -> tuple[Image.Image, GroundTruth, bytes]:
        """Generate a single document and also produce a PDF with native text.

        Text is written into the PDF as real text objects (searchable,
        copy-pasteable) rather than rasterised pixels.  When no original PDF
        was supplied (``pdf_bytes=None``), a new blank PDF sized to match the
        canvas is created from scratch.

        Returns:
            ``(pil_image, ground_truth, pdf_bytes)`` — the raster preview,
            annotation, and the filled PDF bytes.
        """
        from document_simulator.synthesis.pdf_writer import PDFZoneWriter

        canvas, rendered_regions = self._generate_internal(seed)
        image_path = f"doc_{seed:06d}.pdf"
        gt = AnnotationBuilder.build(image_path=image_path, rendered_regions=rendered_regions)

        dpi = self._template_kwargs.get("dpi", 150)
        # When there is no original PDF, pass the clean template image so the
        # writer can embed it as the page background instead of a blank page.
        canvas_image = self._load_canvas() if self._pdf_bytes is None else None
        pdf_out = PDFZoneWriter.write(
            pdf_bytes=self._pdf_bytes,
            rendered_regions=rendered_regions,
            dpi=dpi,
            canvas_size=(canvas.width, canvas.height),
            canvas_image=canvas_image,
        )
        return canvas, gt, pdf_out

    @property
    def has_pdf_template(self) -> bool:
        """True when an original PDF was supplied for write-back."""
        return self._pdf_bytes is not None

    def generate(
        self,
        n: int | None = None,
        write: bool = False,
        output_pdf: bool = False,
    ) -> list[tuple[Image.Image, GroundTruth]]:
        """Generate *n* documents and optionally write output to disk.

        Args:
            n:          Number of documents.  Falls back to
                        ``synthesis_config.generator.n`` when ``None``.
            write:      If ``True``, save files under
                        ``synthesis_config.generator.output_dir``.
            output_pdf: If ``True`` and either *pdf_bytes* was supplied or a
                        blank PDF can be created, write ``.pdf`` files instead
                        of PNG files.

        Returns:
            List of ``(PIL Image, GroundTruth)`` pairs (unchanged signature).
        """
        count = n if n is not None else self._config.generator.n
        base_seed = self._config.generator.seed
        output_dir = Path(self._config.generator.output_dir)

        produce_pdf = output_pdf

        pairs: list[tuple[Image.Image, GroundTruth]] = []
        for i in range(count):
            seed = base_seed + i

            if produce_pdf:
                img, gt, pdf_out = self.generate_one_pdf(seed=seed)
            else:
                img, gt = self.generate_one(seed=seed)
                pdf_out = None

            pairs.append((img, gt))

            if write:
                output_dir.mkdir(parents=True, exist_ok=True)
                stem = f"doc_{i + 1:06d}"

                if pdf_out is not None:
                    pdf_path = output_dir / f"{stem}.pdf"
                    pdf_path.write_bytes(pdf_out)
                    gt_with_path = gt.model_copy(update={"image_path": str(pdf_path)})
                else:
                    img_path = output_dir / f"{stem}.png"
                    img.save(img_path)
                    gt_with_path = gt.model_copy(update={"image_path": str(img_path)})

                json_path = output_dir / f"{stem}.json"
                AnnotationBuilder.save(gt_with_path, json_path)

        if write:
            config_path = output_dir / "synthesis_config.json"
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(self._config.model_dump_json(indent=2))

        return pairs
