"""FastAPI router for augmentation endpoints."""

from __future__ import annotations

import base64
import io
from typing import Annotated

import numpy as np
from fastapi import APIRouter, Form, HTTPException, UploadFile
from loguru import logger
from PIL import Image

router = APIRouter(prefix="/api/augmentation", tags=["augmentation"])

_PRESET_NAMES = ["light", "medium", "heavy", "default"]


@router.get("/catalogue")
def list_catalogue() -> dict:
    """Return all catalogue entries with metadata (for the React catalogue UI).

    Returns:
        JSON with ``entries`` list — each item has ``name``, ``display_name``,
        ``phase``, ``description``, ``slow``, and ``default_params``.
    """
    from document_simulator.augmentation.catalogue import CATALOGUE

    entries = []
    for name, info in CATALOGUE.items():
        # Serialise default_params: convert tuples to lists for JSON
        serialised_params = {}
        for k, v in info["default_params"].items():
            serialised_params[k] = list(v) if isinstance(v, tuple) else v
        entries.append({
            "name": name,
            "display_name": info["display_name"],
            "phase": info["phase"],
            "description": info["description"],
            "slow": info["slow"],
            "default_params": serialised_params,
        })
    return {"entries": entries}


@router.post("/catalogue/augment")
async def augment_catalogue(
    file: UploadFile,
    aug_name: Annotated[str, Form()],
) -> dict:
    """Apply a single catalogue augmentation by name.

    Args:
        file: The document image (PNG, JPG, BMP, TIFF).
        aug_name: Key in the CATALOGUE dict (e.g. ``"InkBleed"``).

    Returns:
        JSON with ``original_b64``, ``augmented_b64``, ``aug_name``,
        ``display_name``, and ``phase``.
    """
    from document_simulator.augmentation.catalogue import CATALOGUE, apply_single

    if aug_name not in CATALOGUE:
        raise HTTPException(status_code=422, detail=f"Unknown augmentation '{aug_name}'.")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=422, detail="Uploaded file is empty.")

    original = _file_to_pil(file, contents)

    try:
        result_raw = apply_single(aug_name, original)
        result = Image.fromarray(np.array(result_raw)) if not isinstance(result_raw, Image.Image) else result_raw
    except Exception as exc:
        logger.error(f"Catalogue augment failed: {aug_name} — {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Augmentation error: {exc}") from exc

    entry = CATALOGUE[aug_name]
    logger.info(f"Catalogue: {aug_name!r} {original.width}x{original.height}px")

    return {
        "original_b64": _pil_to_png_b64(original),
        "augmented_b64": _pil_to_png_b64(result),
        "aug_name": aug_name,
        "display_name": entry["display_name"],
        "phase": entry["phase"],
    }


def _pil_to_png_b64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def _file_to_pil(upload: UploadFile, contents: bytes) -> Image.Image:
    """Decode uploaded image bytes to a PIL Image (RGB)."""
    try:
        img = Image.open(io.BytesIO(contents)).convert("RGB")
        return img
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Cannot decode image: {exc}") from exc


@router.get("/presets")
def list_presets() -> dict:
    """Return the list of available augmentation preset names."""
    return {"presets": _PRESET_NAMES}


@router.post("/augment")
async def augment_image(
    file: UploadFile,
    preset: Annotated[str, Form()] = "medium",
) -> dict:
    """Augment an uploaded image with the selected preset.

    Args:
        file: The document image to augment (PNG, JPG, BMP, TIFF).
        preset: Preset name — one of ``light``, ``medium``, ``heavy``, ``default``.

    Returns:
        JSON with ``original_b64``, ``augmented_b64``, and ``metadata`` fields.
    """
    if preset not in _PRESET_NAMES:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown preset '{preset}'. Choose from {_PRESET_NAMES}.",
        )

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=422, detail="Uploaded file is empty.")

    original = _file_to_pil(file, contents)

    from document_simulator.augmentation import DocumentAugmenter

    try:
        augmenter = DocumentAugmenter(pipeline=preset)
        result = augmenter.augment(original)
        if not isinstance(result, Image.Image):
            result = Image.fromarray(np.array(result))
    except Exception as exc:
        logger.error(f"Augmentation failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Augmentation error: {exc}") from exc

    logger.info(
        f"Augmented: {file.filename!r} preset={preset!r} "
        f"{original.width}x{original.height}px"
    )

    return {
        "original_b64": _pil_to_png_b64(original),
        "augmented_b64": _pil_to_png_b64(result),
        "metadata": {
            "preset": preset,
            "width": original.width,
            "height": original.height,
            "filename": file.filename or "",
        },
    }
