"""Document Simulator - Document image augmentation and OCR training system."""

__version__ = "0.1.0"
__author__ = "Your Name"
__license__ = "MIT"

from document_simulator.augmentation import DocumentAugmenter
from document_simulator.ocr import OCREngine
from document_simulator.rl import PipelineOptimizer

__all__ = [
    "DocumentAugmenter",
    "OCREngine",
    "PipelineOptimizer",
]
