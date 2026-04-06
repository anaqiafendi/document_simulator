"""FastAPI router for OCR endpoints."""

from __future__ import annotations

import base64
import io
from typing import Annotated, Optional

from fastapi import APIRouter, Form, HTTPException, UploadFile
from loguru import logger
from PIL import Image

router = APIRouter(prefix="/api/ocr", tags=["ocr"])

# Lazy singleton — OCREngine is expensive to initialise (~2-5s).
# Created on first request, reused for the lifetime of the server process.
_ocr_engine = None
_ocr_engine_lang: Optional[str] = None
_ocr_engine_gpu: Optional[bool] = None


def _get_ocr_engine(lang: str = "en", use_gpu: bool = False):
    """Return the cached OCREngine, creating it on first call."""
    global _ocr_engine, _ocr_engine_lang, _ocr_engine_gpu
    if _ocr_engine is None or _ocr_engine_lang != lang or _ocr_engine_gpu != use_gpu:
        from document_simulator.ocr import OCREngine

        _ocr_engine = OCREngine(use_gpu=use_gpu, lang=lang)
        _ocr_engine_lang = lang
        _ocr_engine_gpu = use_gpu
        logger.info(f"OCREngine initialised: lang={lang!r} gpu={use_gpu}")
    return _ocr_engine


def _pil_to_png_b64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def _overlay_bboxes(img: Image.Image, boxes: list, scores: list) -> Image.Image:
    """Draw bounding boxes on *img* and return the annotated copy."""
    try:
        from document_simulator.ui.components.image_display import overlay_bboxes

        return overlay_bboxes(img, boxes, scores)
    except Exception:
        # If Streamlit UI components are unavailable, return image as-is
        return img


@router.post("/recognize")
async def recognize(
    file: UploadFile,
    lang: Annotated[str, Form()] = "en",
    use_gpu: Annotated[bool, Form()] = False,
) -> dict:
    """Run OCR on an uploaded document image.

    Args:
        file: Document image (PNG, JPG, BMP, TIFF, PDF).
        lang: PaddleOCR language code (e.g. ``en``, ``ch``, ``fr``).
        use_gpu: Whether to use GPU inference (requires CUDA).

    Returns:
        JSON with ``text``, ``boxes``, ``scores``, ``mean_confidence``, ``annotated_b64``.
    """
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=422, detail="Uploaded file is empty.")

    filename = file.filename or ""

    # Handle PDF: render first page via PyMuPDF
    if filename.lower().endswith(".pdf"):
        try:
            import fitz

            doc = fitz.open(stream=contents, filetype="pdf")
            pix = doc[0].get_pixmap(matrix=fitz.Matrix(150 / 72, 150 / 72))
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        except ImportError as exc:
            raise HTTPException(status_code=500, detail="PyMuPDF not installed.") from exc
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"Cannot render PDF: {exc}") from exc
    else:
        try:
            img = Image.open(io.BytesIO(contents)).convert("RGB")
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"Cannot decode image: {exc}") from exc

    engine = _get_ocr_engine(lang=lang, use_gpu=use_gpu)

    try:
        result = engine.recognize(img)
    except Exception as exc:
        logger.error(f"OCR failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"OCR error: {exc}") from exc

    text = result.get("text", "")
    boxes = result.get("boxes", [])
    scores = result.get("scores", [])

    # Compute mean confidence
    if scores:
        mean_conf = float(sum(float(s) for s in scores) / len(scores))
    else:
        mean_conf = 0.0

    # Annotated image with bbox overlays
    annotated = _overlay_bboxes(img, boxes, scores)

    logger.info(
        f"OCR: {filename!r} lang={lang!r} regions={len(boxes)} conf={mean_conf:.3f}"
    )

    # Convert boxes to serialisable lists
    serialisable_boxes = []
    for box in boxes:
        try:
            serialisable_boxes.append([[float(p[0]), float(p[1])] for p in box])
        except Exception:
            serialisable_boxes.append(box)

    return {
        "text": text,
        "boxes": serialisable_boxes,
        "scores": [float(s) for s in scores],
        "mean_confidence": mean_conf,
        "n_regions": len(boxes),
        "annotated_b64": _pil_to_png_b64(annotated),
    }
