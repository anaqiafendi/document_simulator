"""StyleResolver and ZoneRenderer — PIL text drawing with per-(respondent, field_type) style caching."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from PIL import Image, ImageColor, ImageDraw

from document_simulator.synthesis.fonts import FontResolver
from document_simulator.synthesis.zones import SynthesisConfig, ZoneConfig


@dataclass
class ResolvedStyle:
    """Fully resolved rendering style for one (respondent, field_type) combination."""

    font_color: str
    font_size: int
    fill_style: str
    font_family: str
    bold: bool
    italic: bool
    jitter_x: float
    jitter_y: float
    baseline_wander: float
    char_spacing_jitter: float


class StyleResolver:
    """Resolves and caches style per (respondent_id, field_type_id) for one document."""

    def __init__(self, config: SynthesisConfig, seed: int) -> None:
        self._config = config
        self._seed = seed
        self._cache: dict[tuple[str, str], ResolvedStyle] = {}

    def resolve(self, respondent_id: str, field_type_id: str) -> ResolvedStyle:
        key = (respondent_id, field_type_id)
        if key not in self._cache:
            respondent = self._config.get_respondent(respondent_id)
            ft = respondent.get_field_type(field_type_id)
            rng = random.Random(hash((self._seed, respondent_id, field_type_id)) & 0xFFFFFFFF)
            lo, hi = ft.font_size_range
            size = rng.randint(lo, hi)
            self._cache[key] = ResolvedStyle(
                font_color=ft.font_color,
                font_size=size,
                fill_style=ft.fill_style,
                font_family=ft.font_family,
                bold=ft.bold,
                italic=ft.italic,
                jitter_x=ft.jitter_x,
                jitter_y=ft.jitter_y,
                baseline_wander=ft.baseline_wander,
                char_spacing_jitter=ft.char_spacing_jitter,
            )
        return self._cache[key]


class ZoneRenderer:
    """Draws text onto a PIL canvas for a given zone with resolved style."""

    @staticmethod
    def _apply_jitter(
        box: list[list[float]], jitter_x: float, jitter_y: float, rng: random.Random
    ) -> tuple[float, float]:
        """Compute jittered (x, y) starting position within the zone box.

        Uses a truncated-Gaussian-like approach: mean near the left edge,
        clamped to zone bounds. Falls back to uniform if jitter values are 0.
        """
        x1, y1 = box[0][0], box[0][1]
        x2, y2 = box[2][0], box[2][1]
        w = max(x2 - x1, 1)
        h = max(y2 - y1, 1)

        if jitter_x > 0:
            mean_x = x1 + 0.12 * w
            sigma_x = jitter_x * w
            for _ in range(20):
                v = rng.gauss(mean_x, sigma_x)
                if x1 <= v <= x2:
                    x = v
                    break
            else:
                x = x1 + 0.12 * w
        else:
            x = x1 + 0.05 * w  # small left margin

        if jitter_y > 0:
            mean_y = (y1 + y2) / 2
            sigma_y = jitter_y * h
            for _ in range(20):
                v = rng.gauss(mean_y, sigma_y)
                if y1 <= v <= y2:
                    y = v
                    break
            else:
                y = y1 + 0.1 * h
        else:
            y = y1 + 0.1 * h  # small top margin

        return x, y

    @staticmethod
    def draw(
        canvas: Image.Image,
        text: str,
        style: ResolvedStyle,
        zone: ZoneConfig,
        seed: int = 0,
    ) -> Image.Image:
        """Draw *text* onto a copy of *canvas* and return the new image.

        The original *canvas* is never mutated.
        """
        result = canvas.copy()
        draw = ImageDraw.Draw(result)

        rng = random.Random(hash((seed, zone.zone_id)) & 0xFFFFFFFF)

        # Resolve font
        font = FontResolver.resolve(style.font_family, size=style.font_size)

        # Jitter position
        x, y = ZoneRenderer._apply_jitter(zone.box, style.jitter_x, style.jitter_y, rng)

        # Parse colour
        try:
            color = ImageColor.getrgb(style.font_color)
        except (ValueError, AttributeError):
            color = (0, 0, 0)

        # Apply fill-style transforms
        display_text = text
        if style.fill_style == "stamp":
            display_text = text.upper()

        # Draw text
        draw.text((x, y), display_text, font=font, fill=color)

        return result
