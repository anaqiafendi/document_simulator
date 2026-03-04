"""Data loading and ground truth management."""

from document_simulator.data.datasets import DocumentDataset
from document_simulator.data.ground_truth import (
    GroundTruth,
    GroundTruthLoader,
    TextRegion,
)

__all__ = [
    "DocumentDataset",
    "GroundTruth",
    "GroundTruthLoader",
    "TextRegion",
]
