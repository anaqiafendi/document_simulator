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


# Shear factor used when simulating italic via affine transform
_ITALIC_SHEAR = 0.25


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
    def _render_italic_text(
        canvas: Image.Image,
        text: str,
        position: tuple[float, float],
        font: object,
        color: tuple,
        draw: ImageDraw.ImageDraw,
    ) -> None:
        """Render italic text by drawing to a temporary RGBA layer then shearing it.

        The sheared layer is then composited onto the canvas in-place via
        ``Image.alpha_composite``.  If anything goes wrong the text is drawn
        normally without shearing.
        """
        try:
            w, h = canvas.size
            # Draw onto a transparent temp image the same size as the canvas
            tmp = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            tmp_draw = ImageDraw.Draw(tmp)
            tmp_draw.text(position, text, font=font, fill=(*color, 255) if len(color) == 3 else color)

            # Affine shear on x-axis: x' = x + shear * y, y' = y
            # PIL AFFINE transform maps OUTPUT pixel (x,y) to INPUT pixel via
            # (a*x + b*y + c, d*x + e*y + f), so shear in the forward direction
            # means a=1, b=-shear, c=shear*h (approx), d=0, e=1, f=0.
            shear = _ITALIC_SHEAR
            affine = (1, -shear, shear * h * 0.5, 0, 1, 0)
            sheared = tmp.transform((w, h), Image.AFFINE, affine, resample=Image.BILINEAR)

            # Composite onto the canvas (canvas must be RGBA for alpha_composite)
            if canvas.mode == "RGBA":
                canvas.alpha_composite(sheared)
            else:
                # Convert, composite, convert back
                base = canvas.convert("RGBA")
                base.alpha_composite(sheared)
                canvas.paste(base.convert(canvas.mode))
        except Exception:
            # Fallback: draw without shear
            draw.text(position, text, font=font, fill=color)

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

        Bold is simulated via ``stroke_width=1`` when no bold TTF variant is
        available.  Italic is simulated via affine shear when no italic TTF
        variant is available.  Alignment (left/center/right) adjusts the x
        starting position based on measured text width.
        """
        result = canvas.copy()
        draw = ImageDraw.Draw(result)

        rng = random.Random(hash((seed, zone.zone_id)) & 0xFFFFFFFF)

        # Resolve font — pass bold/italic so FontResolver can pick a variant TTF
        font = FontResolver.resolve(
            style.font_family,
            size=style.font_size,
            bold=style.bold,
            italic=style.italic,
        )

        # Jitter position (x used only for "left" alignment)
        x_jittered, y = ZoneRenderer._apply_jitter(zone.box, style.jitter_x, style.jitter_y, rng)

        # Parse colour
        try:
            color = ImageColor.getrgb(style.font_color)
        except (ValueError, AttributeError):
            color = (0, 0, 0)

        # Apply fill-style transforms
        display_text = text
        if style.fill_style == "stamp":
            display_text = text.upper()

        # --- Alignment ---
        x1 = zone.box[0][0]
        x2 = zone.box[2][0]
        alignment = getattr(zone, "alignment", "left")

        if alignment == "center":
            try:
                text_width = draw.textlength(display_text, font=font)
            except Exception:
                text_width = 0.0
            x = (x1 + x2) / 2 - text_width / 2
        elif alignment == "right":
            try:
                text_width = draw.textlength(display_text, font=font)
            except Exception:
                text_width = 0.0
            right_margin = 4
            x = x2 - text_width - right_margin
        else:
            # "left" — use jittered x position
            x = x_jittered

        position = (x, y)

        stroke_width = 1 if style.bold else 0

        # --- Per-character rendering for baseline_wander / char_spacing_jitter ---
        # Only engaged when at least one of these is non-zero; falls back to the
        # fast single-call path otherwise.  Italic affine-shear is skipped in this
        # path for simplicity — the font variant (if available) handles italics.
        use_char_draw = (style.baseline_wander > 0 or style.char_spacing_jitter > 0) and not style.italic

        if use_char_draw:
            cursor_x = float(x)
            baseline_y = float(y)
            wander_y = 0.0
            for ch in display_text:
                try:
                    ch_w = draw.textlength(ch, font=font)
                except Exception:
                    ch_w = style.font_size * 0.55

                # Baseline wander: smooth random walk, clamped to ±40% of font size
                if style.baseline_wander > 0:
                    delta = rng.gauss(0, style.baseline_wander * style.font_size * 0.3)
                    limit = style.font_size * 0.4
                    wander_y = max(-limit, min(limit, wander_y + delta))

                ch_pos = (cursor_x, baseline_y + wander_y)
                if style.bold:
                    draw.text(ch_pos, ch, font=font, fill=color,
                              stroke_width=stroke_width, stroke_fill=color)
                else:
                    draw.text(ch_pos, ch, font=font, fill=color)

                # Char spacing jitter: Gaussian offset on the advance width
                if style.char_spacing_jitter > 0:
                    spacing_delta = rng.gauss(0, style.char_spacing_jitter * style.font_size * 0.15)
                else:
                    spacing_delta = 0.0
                cursor_x += ch_w + spacing_delta

        # --- Italic rendering (affine-shear path) ---
        elif style.italic:
            ZoneRenderer._render_italic_text(result, display_text, position, font, color, draw)
            if style.bold:
                draw2 = ImageDraw.Draw(result)
                draw2.text(position, display_text, font=font, fill=color,
                           stroke_width=stroke_width, stroke_fill=color)

        # --- Normal path ---
        else:
            if style.bold:
                draw.text(position, display_text, font=font, fill=color,
                          stroke_width=stroke_width, stroke_fill=color)
            else:
                draw.text(position, display_text, font=font, fill=color)

        return result
