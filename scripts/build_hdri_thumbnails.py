"""Build 128x128 PNG thumbnails for every HDRI in ``data/hdri/``.

Pre-computed at build time so the v0.3d ``GET /api/receipt-synthesis/
hdri-thumbnails`` endpoint can ship them straight from disk without a
runtime tone-mapping cost.

Usage:
    uv run python scripts/build_hdri_thumbnails.py
"""

from __future__ import annotations

from pathlib import Path

import imageio.v3 as iio
from PIL import Image

_REPO_ROOT = Path(__file__).resolve().parent.parent
_HDRI_DIR = _REPO_ROOT / "data" / "hdri"
_THUMB_SIZE = (128, 128)


def build_thumbnails() -> list[Path]:
    """Generate one ``<id>.thumbnail.png`` per ``<id>.hdr`` in ``data/hdri/``.

    Returns:
        List of paths to the generated thumbnail files.
    """
    if not _HDRI_DIR.exists():
        raise FileNotFoundError(f"HDRI directory not found: {_HDRI_DIR}")

    written: list[Path] = []
    for hdr_path in sorted(_HDRI_DIR.glob("*.hdr")):
        img = iio.imread(hdr_path)
        # imageio decodes Radiance HDR as uint8 with the default plugin.
        pil = Image.fromarray(img).convert("RGB")

        # Center-crop the 2:1 panorama to 1:1 before downsizing.
        w, h = pil.size
        if w > h:
            offset = (w - h) // 2
            pil = pil.crop((offset, 0, offset + h, h))
        elif h > w:
            offset = (h - w) // 2
            pil = pil.crop((0, offset, w, offset + w))

        pil = pil.resize(_THUMB_SIZE, Image.LANCZOS)

        out_path = hdr_path.with_suffix(".thumbnail.png")
        pil.save(out_path, optimize=True)
        written.append(out_path)
        print(f"  {hdr_path.name} -> {out_path.name} ({_THUMB_SIZE[0]}x{_THUMB_SIZE[1]})")

    return written


if __name__ == "__main__":
    paths = build_thumbnails()
    print(f"Wrote {len(paths)} thumbnails to {_HDRI_DIR}")
