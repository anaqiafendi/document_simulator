"""Visual overlay tool: draw token polygons over an image for inspection.

Used for v0.1's manual validation gate (FDD §Tests, AC-7) and reused by every
later phase to inspect any intermediate ``CoordSnapshot`` over its corresponding
intermediate render.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from loguru import logger
from PIL import Image, ImageDraw

from document_simulator.synthesis.receipts.schema import ImageGroundTruth

# 8-color palette cycled per token to make overlapping rects distinguishable.
_PALETTE: tuple[tuple[int, int, int], ...] = (
    (220, 20, 60),  # crimson
    (30, 144, 255),  # dodger blue
    (50, 205, 50),  # lime green
    (255, 140, 0),  # dark orange
    (138, 43, 226),  # blue violet
    (0, 191, 191),  # dark cyan
    (255, 105, 180),  # hot pink
    (184, 134, 11),  # dark goldenrod
)


def draw_overlay(image: Image.Image, gt: ImageGroundTruth, stage: str = "raster") -> Image.Image:
    """Return a copy of ``image`` annotated with each token's polygon outline.

    Args:
        image: Source PIL image (any mode; converted to RGB internally).
        gt: Ground truth carrying token polygons across stages.
        stage: Which CoordSnapshot stage to draw. Defaults to ``"raster"``.

    Returns:
        A new PIL.Image (same size as the input) with colored polygon outlines.

    Notes:
        Tokens missing the requested stage are silently skipped and logged.
    """
    out = image.convert("RGB").copy()
    draw = ImageDraw.Draw(out)

    skipped = 0
    for idx, token in enumerate(gt.tokens):
        snapshot = next((c for c in token.coords if c.stage == stage), None)
        if snapshot is None:
            skipped += 1
            continue
        polygon = [(float(x), float(y)) for x, y in snapshot.polygon]
        if len(polygon) < 3:
            skipped += 1
            continue
        color = _PALETTE[idx % len(_PALETTE)]
        # Use polygon outline (no fill) at 2-px width.
        draw.polygon(polygon, outline=color)
        # ImageDraw.polygon outline is 1 px on Pillow; trace a line over edges
        # for a visible 2-px stroke.
        n = len(polygon)
        for i in range(n):
            p0 = polygon[i]
            p1 = polygon[(i + 1) % n]
            draw.line([p0, p1], fill=color, width=2)

    if skipped:
        logger.debug(f"draw_overlay: skipped {skipped} tokens missing stage={stage!r}")
    return out


def _cli_main(argv: list[str] | None = None) -> int:
    """CLI entry point: ``python -m document_simulator.synthesis.receipts.overlay``."""
    parser = argparse.ArgumentParser(
        prog="document_simulator.synthesis.receipts.overlay",
        description="Draw colored polygons of one CoordSnapshot stage over an image.",
    )
    parser.add_argument("image", type=Path, help="Input image PNG path")
    parser.add_argument("gt", type=Path, help="Input ground-truth JSON path")
    parser.add_argument(
        "--stage", default="raster", help="CoordSnapshot stage to draw (default: raster)"
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output PNG path (default: <image stem>.overlay.png alongside the input)",
    )
    args = parser.parse_args(argv)

    image = Image.open(args.image)
    gt = ImageGroundTruth.model_validate_json(args.gt.read_text(encoding="utf-8"))
    overlay = draw_overlay(image, gt, stage=args.stage)

    out_path = args.out or args.image.with_suffix(".overlay.png")
    overlay.save(out_path, format="PNG")
    print(f"Wrote overlay: {out_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_cli_main())
