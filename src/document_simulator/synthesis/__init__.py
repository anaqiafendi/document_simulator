"""Synthesis package — synthetic document generation pipeline."""

from document_simulator.synthesis.batch_integrity import (
    BatchIntegrityChecker,
    BatchIntegrityError,
    BatchIntegrityReport,
)
from document_simulator.synthesis.generator import SyntheticDocumentGenerator
from document_simulator.synthesis.ground_truth_writer import (
    EnhancedGroundTruth,
    GroundTruthRecord,
    GroundTruthWriter,
)

__all__ = [
    "SyntheticDocumentGenerator",
    "GroundTruthRecord",
    "EnhancedGroundTruth",
    "GroundTruthWriter",
    "BatchIntegrityChecker",
    "BatchIntegrityError",
    "BatchIntegrityReport",
]
