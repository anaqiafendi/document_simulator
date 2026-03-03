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
}


class FontResolver:
    """Resolves a font category name to a PIL ImageFont at the requested size."""

    CATALOG: dict[str, str] = _CATALOG

    @classmethod
    def resolve(cls, category: str, size: int = 12) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        """Return a PIL font for *category* at *size* points.

        Falls back to PIL's built-in bitmap font when the TTF file is not found,
        so callers always receive a usable font object.
        """
        filename = cls.CATALOG.get(category, cls.CATALOG.get("sans-serif", ""))
        if filename:
            ttf_path = _FONTS_DIR / filename
            if ttf_path.exists():
                return ImageFont.truetype(str(ttf_path), size=size)
        # Fallback: PIL default bitmap font (no size control, but always available)
        return ImageFont.load_default()
