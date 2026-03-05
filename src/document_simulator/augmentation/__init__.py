"""Document augmentation module using Augraphy.

Imports are lazy so that importing this package does not pull in augraphy/cv2
at module load time. cv2 requires libGL.so.1 which may not be present in all
deployment environments. The heavy imports only happen when the classes are
actually accessed.
"""

from document_simulator.augmentation.presets import AugmentationPreset, PresetFactory

__all__ = ["DocumentAugmenter", "BatchAugmenter", "AugmentationPreset", "PresetFactory"]


def __getattr__(name: str):
    if name == "DocumentAugmenter":
        from document_simulator.augmentation.augmenter import DocumentAugmenter

        return DocumentAugmenter
    if name == "BatchAugmenter":
        from document_simulator.augmentation.batch import BatchAugmenter

        return BatchAugmenter
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
