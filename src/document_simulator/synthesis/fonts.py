"""FontResolver — maps font category names to PIL ImageFont instances.

Bundled TTF files live under src/document_simulator/fonts/.
If a TTF file is absent (not yet downloaded), falls back to PIL's built-in
bitmap font so tests and basic usage work without manual font installation.
"""

from __future__ import annotations

from pathlib import Path

from PIL import ImageFont

# Directory where bundled .ttf files are stored
_FONTS_DIR = Path(__file__).parent.parent / "fonts"

# Catalog: category → filename (relative to _FONTS_DIR)
# Download OFL-licensed fonts and place them here:
#   Caveat-Regular.ttf      → https://fonts.google.com/specimen/Caveat
#   SourceCodePro-Regular.ttf → https://fonts.google.com/specimen/Source+Code+Pro
#   Merriweather-Regular.ttf  → https://fonts.google.com/specimen/Merriweather
#   NotoSans-Regular.ttf      → https://fonts.google.com/specimen/Noto+Sans
_CATALOG: dict[str, str] = {
    "handwriting": "Caveat[wght].ttf",
    "handwriting-alt": "IndieFlower-Regular.ttf",
    "monospace": "SourceCodePro[wght].ttf",
    "serif": "Merriweather[opsz,wdth,wght].ttf",
    "sans-serif": "NotoSans[wdth,wght].ttf",
    # Bold variants — fall back to regular + stroke simulation if absent
    "handwriting-bold": "Caveat-Bold.ttf",
    "monospace-bold": "SourceCodePro-Bold.ttf",
    "serif-bold": "Merriweather-Bold.ttf",
    "sans-serif-bold": "NotoSans-Bold.ttf",
    # Italic variants — fall back to regular + shear simulation if absent
    "handwriting-italic": "Caveat-Italic.ttf",
    "monospace-italic": "SourceCodePro-Italic.ttf",
    "serif-italic": "Merriweather-Italic.ttf",
    "sans-serif-italic": "NotoSans-Italic.ttf",
    # Bold+italic variants
    "handwriting-bold-italic": "Caveat-BoldItalic.ttf",
    "monospace-bold-italic": "SourceCodePro-BoldItalic.ttf",
    "serif-bold-italic": "Merriweather-BoldItalic.ttf",
    "sans-serif-bold-italic": "NotoSans-BoldItalic.ttf",
}


class FontResolver:
    """Resolves a font category name to a PIL ImageFont at the requested size."""

    CATALOG: dict[str, str] = _CATALOG

    @classmethod
    def resolve(
        cls,
        category: str,
        size: int = 12,
        bold: bool = False,
        italic: bool = False,
    ) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        """Return a PIL font for *category* at *size* points.

        When *bold* or *italic* are True, the resolver first tries a dedicated
        variant filename (e.g. ``NotoSans-Bold.ttf``).  If that file is absent
        it falls back to the regular variant so that stroke-width simulation
        (for bold) and affine-shear simulation (for italic) can handle the
        effect at draw time.

        Falls back to PIL's built-in bitmap font when no TTF file is found,
        so callers always receive a usable font object.
        """
        # Build lookup key with variant suffix
        if bold and italic:
            variant_key = f"{category}-bold-italic"
        elif bold:
            variant_key = f"{category}-bold"
        elif italic:
            variant_key = f"{category}-italic"
        else:
            variant_key = category

        # Try variant first, then regular category, then sans-serif fallback
        for key in (variant_key, category, "sans-serif"):
            filename = cls.CATALOG.get(key, "")
            if filename:
                ttf_path = _FONTS_DIR / filename
                if ttf_path.exists():
                    return ImageFont.truetype(str(ttf_path), size=size)

        # Fallback: PIL default bitmap font (no size control, but always available)
        return ImageFont.load_default()
