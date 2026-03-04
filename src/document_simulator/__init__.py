"""Document Simulator - Document image augmentation and OCR training system."""

__version__ = "0.1.0"
__author__ = "Your Name"
__license__ = "MIT"


def __getattr__(name: str):
    if name == "DocumentAugmenter":
        from document_simulator.augmentation import DocumentAugmenter

        return DocumentAugmenter
    if name == "OCREngine":
        from document_simulator.ocr import OCREngine

        return OCREngine
    if name == "PipelineOptimizer":
        from document_simulator.rl import PipelineOptimizer

        return PipelineOptimizer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "DocumentAugmenter",
    "OCREngine",
    "PipelineOptimizer",
]
