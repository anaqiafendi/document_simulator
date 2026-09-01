"""ReceiptFaker template acquisition and visual-feature taxonomy.

Scrapes the public ReceiptFaker template catalogue and derives a categorical
taxonomy over the visual/structural dimensions of each receipt template so
templates can be grouped by layout similarity for synthetic document generation.
"""

from document_simulator.data.receiptfaker.schema import (
    LineItem,
    ReceiptSection,
    ReceiptTemplate,
    SectionType,
)
from document_simulator.data.receiptfaker.taxonomy import (
    TemplateLabels,
    build_taxonomy,
    label_template,
)

__all__ = [
    "LineItem",
    "ReceiptSection",
    "ReceiptTemplate",
    "SectionType",
    "TemplateLabels",
    "build_taxonomy",
    "label_template",
]
