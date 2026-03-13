"""FastAPI router for augmentation endpoints."""

from __future__ import annotations

import asyncio
import base64
import functools
import hashlib
import io
import json
from collections import OrderedDict
from pathlib import Path
from typing import Annotated

import numpy as np
from fastapi import APIRouter, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from loguru import logger
from PIL import Image

router = APIRouter(prefix="/api/augmentation", tags=["augmentation"])

_PRESET_NAMES = ["light", "medium", "heavy", "default"]
_AUG_SAMPLES_DIR = Path(__file__).resolve().parents[4] / "data" / "samples" / "augmentation_lab"
_THUMB_SIZE = 256  # px — for per-card preview thumbnails

# ── In-memory preview cache ───────────────────────────────────────────────────
# Key: (image_sha256, aug_name, params_json) → {"original_b64": ..., "augmented_b64": ...}
# LRU eviction: keeps at most _PREVIEW_CACHE_SIZE entries (one full set of previews ≈ 50 entries)
_PREVIEW_CACHE_SIZE = 200
_preview_cache: OrderedDict[tuple, dict] = OrderedDict()


def _cache_key(image_bytes: bytes, aug_name: str, params_json: str) -> tuple:
    sha = hashlib.sha256(image_bytes).hexdigest()[:16]
    return (sha, aug_name, params_json)


def _cache_get(key: tuple) -> dict | None:
    if key in _preview_cache:
        _preview_cache.move_to_end(key)
        return _preview_cache[key]
    return None


def _cache_set(key: tuple, value: dict) -> None:
    _preview_cache[key] = value
    _preview_cache.move_to_end(key)
    while len(_preview_cache) > _PREVIEW_CACHE_SIZE:
        _preview_cache.popitem(last=False)


# ── Sample templates for augmentation lab ────────────────────────────────────

@router.get("/samples")
def list_aug_samples() -> dict:
    """List sample files available for the Augmentation Lab."""
    if not _AUG_SAMPLES_DIR.exists():
        return {"samples": []}
    files = sorted(
        f.name for f in _AUG_SAMPLES_DIR.iterdir()
        if f.suffix.lower() in {".pdf", ".png", ".jpg", ".jpeg", ".bmp", ".tiff"}
        and not f.name.startswith(".")
    )
    return {"samples": files}


@router.get("/samples/{filename}")
def load_aug_sample(filename: str, dpi: int = 150, page: int = 0) -> dict:
    """Render a sample augmentation-lab file and return as base64 PNG."""
    safe_name = Path(filename).name
    sample_path = _AUG_SAMPLES_DIR / safe_name
    if not sample_path.exists():
        raise HTTPException(status_code=404, detail=f"Sample '{safe_name}' not found.")

    file_bytes = sample_path.read_bytes()
    img = _bytes_to_pil(file_bytes, safe_name, dpi=dpi, page=page)
    return {
        "image_b64": _pil_to_png_b64(img),
        "width_px": img.width,
        "height_px": img.height,
        "filename": safe_name,
    }


# ── Catalogue listing ──────────────────────────────────────────────────────────

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
        if info.get("disabled"):
            continue  # skip entries with known fatal crashes
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


# ── Single catalogue augmentation ─────────────────────────────────────────────

@router.post("/catalogue/augment")
async def augment_catalogue(
    file: UploadFile,
    aug_name: Annotated[str, Form()],
    params_json: Annotated[str, Form()] = "{}",
) -> dict:
    """Apply a single catalogue augmentation by name with optional param overrides.

    Args:
        file: The document image (PNG, JPG, BMP, TIFF).
        aug_name: Key in the CATALOGUE dict (e.g. ``"InkBleed"``).
        params_json: JSON string of param overrides (e.g. ``{"intensity_range": [0.1, 0.3]}``).

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
        params_override = json.loads(params_json) if params_json else {}
        # Convert JSON lists back to tuples where needed
        params_override = _lists_to_tuples(params_override)
    except json.JSONDecodeError:
        params_override = {}

    try:
        result_raw = await _run_in_thread(apply_single, aug_name, original, params_override if params_override else None)
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


# ── Per-card thumbnail preview ─────────────────────────────────────────────────

@router.post("/catalogue/preview")
async def preview_catalogue(
    file: UploadFile,
    aug_name: Annotated[str, Form()],
    params_json: Annotated[str, Form()] = "{}",
    nocache: Annotated[str, Form()] = "",
) -> dict:
    """Apply a catalogue augmentation to a thumbnail for quick per-card preview.

    Resizes the source image to at most 256×256 px before augmenting for speed.

    Returns:
        JSON with ``aug_name``, ``original_b64``, ``augmented_b64`` (both thumbnail-sized).
    """
    from document_simulator.augmentation.catalogue import CATALOGUE, apply_single

    if aug_name not in CATALOGUE:
        raise HTTPException(status_code=422, detail=f"Unknown augmentation '{aug_name}'.")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=422, detail="Uploaded file is empty.")

    # Check cache first — skip if nocache nonce is set (refresh re-roll)
    cache_key = _cache_key(contents, aug_name, params_json)
    cached = None if nocache else _cache_get(cache_key)
    if cached:
        logger.debug(f"Preview cache hit: {aug_name!r}")
        return cached

    original = _file_to_pil(file, contents)

    # Downscale large images for fast previews — max 900px on longest side.
    # This keeps DepthSimulatedBlur (and similar slow augs) under ~2s instead of 40s+.
    preview_img = _resize_for_preview(original, max_px=900)

    try:
        params_override = json.loads(params_json) if params_json else {}
        params_override = _lists_to_tuples(params_override)
    except json.JSONDecodeError:
        params_override = {}

    try:
        result_raw = await _run_in_thread(apply_single, aug_name, preview_img, params_override if params_override else None)
        result = Image.fromarray(np.array(result_raw)) if not isinstance(result_raw, Image.Image) else result_raw
    except Exception as exc:
        logger.error(f"Preview failed: {aug_name} — {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Preview error: {exc}") from exc

    logger.info(f"Preview: {aug_name!r} {preview_img.width}x{preview_img.height}px (downscaled from {original.width}x{original.height})")

    response = {
        "aug_name": aug_name,
        "original_b64": _pil_to_png_b64(preview_img),
        "augmented_b64": _pil_to_png_b64(result),
    }
    _cache_set(cache_key, response)
    return response


# ── Multi-augmentation pipeline ───────────────────────────────────────────────

@router.post("/catalogue/pipeline")
async def apply_pipeline(
    file: UploadFile,
    aug_names_json: Annotated[str, Form()],
    all_params_json: Annotated[str, Form()] = "{}",
) -> dict:
    """Apply a sequence of catalogue augmentations in order (pipeline mode).

    Args:
        file: The document image.
        aug_names_json: JSON array of aug names in order (e.g. ``["InkBleed","Blur"]``).
        all_params_json: JSON object keyed by aug_name → param overrides dict.

    Returns:
        JSON with ``original_b64``, ``augmented_b64``, ``applied`` (list of aug names).
    """
    from document_simulator.augmentation.catalogue import CATALOGUE, apply_single

    try:
        aug_names: list[str] = json.loads(aug_names_json)
        if not isinstance(aug_names, list):
            raise ValueError
    except (json.JSONDecodeError, ValueError):
        raise HTTPException(status_code=422, detail="aug_names_json must be a JSON array.")

    try:
        all_params: dict[str, dict] = json.loads(all_params_json) if all_params_json else {}
    except json.JSONDecodeError:
        all_params = {}

    unknown = [n for n in aug_names if n not in CATALOGUE]
    if unknown:
        raise HTTPException(status_code=422, detail=f"Unknown augmentation(s): {unknown}")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=422, detail="Uploaded file is empty.")

    original = _file_to_pil(file, contents)
    current = original.copy()

    applied: list[str] = []
    for aug_name in aug_names:
        params_override = _lists_to_tuples(all_params.get(aug_name, {}))
        try:
            result_raw = await _run_in_thread(apply_single, aug_name, current, params_override if params_override else None)
            current = Image.fromarray(np.array(result_raw)) if not isinstance(result_raw, Image.Image) else result_raw
            applied.append(aug_name)
        except Exception as exc:
            logger.warning(f"Pipeline: skipping {aug_name} — {exc}")

    logger.info(f"Pipeline: applied {applied} to {original.width}×{original.height}px image")

    return {
        "original_b64": _pil_to_png_b64(original),
        "augmented_b64": _pil_to_png_b64(current),
        "applied": applied,
    }


# ── Presets ───────────────────────────────────────────────────────────────────

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


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _run_in_thread(fn, *args):
    """Run a CPU-bound function in the default thread pool so async endpoints stay responsive."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, functools.partial(fn, *args))


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


def _bytes_to_pil(file_bytes: bytes, filename: str, dpi: int = 150, page: int = 0) -> Image.Image:
    """Render image or PDF bytes to a PIL Image."""
    if filename.lower().endswith(".pdf"):
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise HTTPException(status_code=500, detail="PDF support requires PyMuPDF.")
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        if page >= len(doc):
            page = 0
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = doc[page].get_pixmap(matrix=mat, alpha=False)
        return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    else:
        try:
            return Image.open(io.BytesIO(file_bytes)).convert("RGB")
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"Cannot decode image: {exc}") from exc


def _resize_for_preview(img: Image.Image, max_px: int = 900) -> Image.Image:
    """Downscale image so its longest side is at most max_px, preserving aspect ratio.

    Returns the original image unchanged if it is already within the limit.
    """
    w, h = img.size
    longest = max(w, h)
    if longest <= max_px:
        return img
    scale = max_px / longest
    return img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)


def _lists_to_tuples(params: dict) -> dict:
    """Convert JSON lists back to tuples for augraphy range params."""
    result = {}
    for k, v in params.items():
        if isinstance(v, list) and len(v) == 2 and all(isinstance(x, (int, float)) for x in v):
            result[k] = tuple(v)
        else:
            result[k] = v
    return result
