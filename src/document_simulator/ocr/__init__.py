"""OCR module using PaddleOCR."""

from document_simulator.ocr.engine import OCREngine
from document_simulator.ocr.metrics import (
    aggregate_confidence,
    calculate_cer,
    calculate_levenshtein,
    calculate_wer,
)

__all__ = [
    "OCREngine",
    "aggregate_confidence",
    "calculate_cer",
    "calculate_levenshtein",
    "calculate_wer",
]
