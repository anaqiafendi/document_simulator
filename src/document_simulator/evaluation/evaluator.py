"""Evaluation framework for document augmentation + OCR pipelines."""

from typing import Any, Dict, List, Optional

import numpy as np
from loguru import logger
from tqdm import tqdm

from document_simulator.augmentation.augmenter import DocumentAugmenter
from document_simulator.data.datasets import DocumentDataset
from document_simulator.ocr.metrics import aggregate_confidence, calculate_cer, calculate_wer


class Evaluator:
    """Evaluate an augmentation + OCR pipeline over a dataset.

    Args:
        augmenter: :class:`~document_simulator.augmentation.DocumentAugmenter`
            instance to use for document degradation.
        ocr_engine: An initialized OCR engine (e.g.
            :class:`~document_simulator.ocr.OCREngine`) that exposes
            ``recognize(image) -> {"text": str, "scores": list}``.
        show_progress: Whether to display a progress bar.
    """

    def __init__(self, augmenter: DocumentAugmenter, ocr_engine, show_progress: bool = False):
        self.augmenter = augmenter
        self.ocr = ocr_engine
        self.show_progress = show_progress

    def evaluate_dataset(self, dataset: DocumentDataset) -> Dict[str, Any]:
        """Run original and augmented OCR over every sample in *dataset*.

        Args:
            dataset: The :class:`~document_simulator.data.DocumentDataset` to
                evaluate on.

        Returns:
            Aggregated metrics dictionary (see :meth:`_aggregate_results`).
        """
        results: List[Dict[str, float]] = []

        for image, ground_truth in tqdm(
            dataset,
            total=len(dataset),
            disable=not self.show_progress,
            desc="Evaluating",
        ):
            gt_text = ground_truth.text

            # Original
            try:
                orig_result = self.ocr.recognize(image)
                orig_cer = calculate_cer(orig_result["text"], gt_text)
                orig_wer = calculate_wer(orig_result["text"], gt_text)
                orig_conf = aggregate_confidence(orig_result["scores"])
            except Exception as exc:
                logger.warning(f"OCR failed on original image: {exc}")
                orig_cer, orig_wer, orig_conf = 1.0, 1.0, 0.0

            # Augmented
            try:
                aug_image = self.augmenter.augment(image)
                aug_result = self.ocr.recognize(aug_image)
                aug_cer = calculate_cer(aug_result["text"], gt_text)
                aug_wer = calculate_wer(aug_result["text"], gt_text)
                aug_conf = aggregate_confidence(aug_result["scores"])
            except Exception as exc:
                logger.warning(f"OCR failed on augmented image: {exc}")
                aug_cer, aug_wer, aug_conf = 1.0, 1.0, 0.0

            results.append({
                "original_cer": orig_cer,
                "augmented_cer": aug_cer,
                "original_wer": orig_wer,
                "augmented_wer": aug_wer,
                "original_confidence": orig_conf,
                "augmented_confidence": aug_conf,
            })

        return self._aggregate_results(results)

    def evaluate_single(
        self, image, ground_truth_text: str
    ) -> Dict[str, Any]:
        """Evaluate a single image / ground-truth pair.

        Args:
            image: PIL Image or numpy array.
            ground_truth_text: Expected OCR output.

        Returns:
            Per-sample metrics dictionary.
        """
        orig_result = self.ocr.recognize(image)
        aug_image = self.augmenter.augment(image)
        aug_result = self.ocr.recognize(aug_image)

        return {
            "original_cer": calculate_cer(orig_result["text"], ground_truth_text),
            "augmented_cer": calculate_cer(aug_result["text"], ground_truth_text),
            "original_wer": calculate_wer(orig_result["text"], ground_truth_text),
            "augmented_wer": calculate_wer(aug_result["text"], ground_truth_text),
            "original_confidence": aggregate_confidence(orig_result["scores"]),
            "augmented_confidence": aggregate_confidence(aug_result["scores"]),
        }

    @staticmethod
    def _aggregate_results(results: List[Dict[str, float]]) -> Dict[str, Any]:
        """Compute mean and standard deviation for each metric.

        Args:
            results: List of per-sample metric dicts.

        Returns:
            Dictionary with ``mean_*`` and ``std_*`` keys plus ``n_samples``.
        """
        if not results:
            return {"n_samples": 0}

        keys = list(results[0].keys())
        aggregated: Dict[str, Any] = {"n_samples": len(results)}

        for key in keys:
            values = np.array([r[key] for r in results])
            aggregated[f"mean_{key}"] = float(np.mean(values))
            aggregated[f"std_{key}"] = float(np.std(values))

        return aggregated
