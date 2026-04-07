"""Synthesis package — synthetic document generation.

Public API::

    from document_simulator.synthesis import (
        SyntheticDocumentGenerator,
        DocumentTemplate,
        TemplateRegistry,
        StaticSection,
        RepeatingSection,
    )
"""

from document_simulator.synthesis.document_template import DocumentTemplate
from document_simulator.synthesis.generator import SyntheticDocumentGenerator
from document_simulator.synthesis.sections import RepeatingSection, Section, StaticSection
from document_simulator.synthesis.template_registry import TemplateRegistry

__all__ = [
    "DocumentTemplate",
    "RepeatingSection",
    "Section",
    "StaticSection",
    "SyntheticDocumentGenerator",
    "TemplateRegistry",
]
