"""OCR engine using PaddleOCR."""

from pathlib import Path
from typing import Any, Dict, List, Union

import numpy as np
from loguru import logger
from paddleocr import PaddleOCR
from PIL import Image

from document_simulator.config import settings


class OCREngine:
    """OCR engine powered by PaddleOCR."""

    def __init__(
        self,
        use_gpu: bool = False,
        lang: str = "en",
        det_model_dir: str = None,
        rec_model_dir: str = None,
        cls_model_dir: str = None,
    ):
        """Initialize the OCR engine.

        Args:
            use_gpu: Whether to use GPU acceleration.
            lang: OCR language code (e.g. 'en', 'ch').
            det_model_dir: Custom text detection model directory
                (maps to ``text_detection_model_dir`` in PaddleOCR 3.x).
            rec_model_dir: Custom text recognition model directory
                (maps to ``text_recognition_model_dir`` in PaddleOCR 3.x).
            cls_model_dir: Unused in PaddleOCR 3.x (kept for API compatibility).
        """
        self.use_gpu = use_gpu or settings.paddleocr_use_gpu
        self.lang = lang or settings.paddleocr_lang

        logger.info(f"Initializing PaddleOCR (GPU={self.use_gpu}, lang={self.lang})")

        # PaddleOCR 3.x constructor — GPU is set via device="gpu"/"cpu".
        # Removed 2.x-only args: use_angle_cls, use_gpu, show_log, cls_model_dir.
        # Only pass model dirs when they exist on disk; PaddleOCR 3.x asserts
        # existence and will not auto-download to a missing path like 2.x did.
        paddle_kwargs: dict = {
            "lang": self.lang,
            "device": "gpu" if self.use_gpu else "cpu",
        }
        det_dir = det_model_dir or settings.paddleocr_det_model_dir
        rec_dir = rec_model_dir or settings.paddleocr_rec_model_dir
        if det_dir and Path(str(det_dir)).exists():
            paddle_kwargs["text_detection_model_dir"] = str(det_dir)
        if rec_dir and Path(str(rec_dir)).exists():
            paddle_kwargs["text_recognition_model_dir"] = str(rec_dir)

        self.ocr = PaddleOCR(**paddle_kwargs)

        logger.success("PaddleOCR initialized successfully")

    def recognize(
        self, image: Union[np.ndarray, Image.Image, str, Path]
    ) -> Dict[str, Any]:
        """Run OCR on an image.

        Args:
            image: Input image (numpy array, PIL Image, or file path)

        Returns:
            Dictionary containing OCR results with keys:
                - text: Extracted text (concatenated)
                - boxes: List of bounding boxes
                - scores: List of confidence scores
                - raw: Raw PaddleOCR output
        """
        # Handle different input types
        if isinstance(image, (str, Path)):
            image_path = str(image)
        elif isinstance(image, Image.Image):
            image_path = np.array(image)
        else:
            image_path = image

        # Run OCR — PaddleOCR 3.x returns a list of OCRResult dicts (one per image).
        result = self.ocr.predict(image_path)

        if not result:
            logger.warning("No text detected in image")
            return {"text": "", "boxes": [], "scores": [], "raw": result}

        # result[0] is an OCRResult (dict-like) with keys:
        #   rec_texts   — list[str]
        #   rec_scores  — list[float]
        #   rec_polys   — list of polygon point arrays [[x,y], ...]
        ocr_result = result[0]
        texts: list = list(ocr_result.get("rec_texts", []))
        scores: list = [float(s) for s in ocr_result.get("rec_scores", [])]
        # rec_polys is a list of numpy arrays; convert each to a plain list of [x,y] pairs
        raw_polys = ocr_result.get("rec_polys", [])
        boxes: list = [
            [[float(pt[0]), float(pt[1])] for pt in poly] for poly in raw_polys
        ]

        if not texts:
            logger.warning("No text detected in image")
            return {"text": "", "boxes": [], "scores": [], "raw": result}

        return {
            "text": "\n".join(texts),
            "boxes": boxes,
            "scores": scores,
            "raw": result,
        }

    def recognize_file(self, input_path: Path) -> Dict[str, Any]:
        """Run OCR on an image file.

        Args:
            input_path: Path to input image

        Returns:
            Dictionary containing OCR results
        """
        logger.info(f"Running OCR on {input_path}")
        result = self.recognize(str(input_path))
        logger.info(f"Detected {len(result['boxes'])} text regions")
        return result

    def recognize_batch(
        self, images: List[Union[np.ndarray, Image.Image, str, Path]]
    ) -> List[Dict[str, Any]]:
        """Run OCR on multiple images.

        Args:
            images: List of input images

        Returns:
            List of OCR results
        """
        results = []
        for image in images:
            result = self.recognize(image)
            results.append(result)
        return results
