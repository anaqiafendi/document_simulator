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
            use_gpu: Whether to use GPU acceleration
            lang: OCR language (e.g., 'en', 'ch')
            det_model_dir: Custom detection model directory
            rec_model_dir: Custom recognition model directory
            cls_model_dir: Custom classification model directory
        """
        self.use_gpu = use_gpu or settings.paddleocr_use_gpu
        self.lang = lang or settings.paddleocr_lang

        logger.info(f"Initializing PaddleOCR (GPU={self.use_gpu}, lang={self.lang})")

        # Initialize PaddleOCR
        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang=self.lang,
            use_gpu=self.use_gpu,
            det_model_dir=det_model_dir or settings.paddleocr_det_model_dir,
            rec_model_dir=rec_model_dir or settings.paddleocr_rec_model_dir,
            cls_model_dir=cls_model_dir or settings.paddleocr_cls_model_dir,
            show_log=False,
        )

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

        # Run OCR
        result = self.ocr.ocr(image_path, cls=True)

        if not result or not result[0]:
            logger.warning("No text detected in image")
            return {
                "text": "",
                "boxes": [],
                "scores": [],
                "raw": result,
            }

        # Parse results
        boxes = []
        texts = []
        scores = []

        for line in result[0]:
            box, (text, score) = line
            boxes.append(box)
            texts.append(text)
            scores.append(score)

        # Concatenate text
        full_text = "\n".join(texts)

        return {
            "text": full_text,
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
