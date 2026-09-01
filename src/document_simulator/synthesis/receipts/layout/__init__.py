"""Layout specifications sampled from the ReceiptFaker visual taxonomy.

A :class:`LayoutSpec` says what a receipt should look like -- which blocks it
stacks, in what order, and with what styling -- independently of what it says.
Specs are drawn from a prior distilled from 979 real receipt templates, so the
combinations the synthesiser produces reflect how receipts actually vary rather
than a hand-picked handful of layouts.
"""

from document_simulator.synthesis.receipts.layout.prior import (
    Prior,
    load_prior,
    sample_spec,
)
from document_simulator.synthesis.receipts.layout.sampler import stratified_specs
from document_simulator.synthesis.receipts.layout.spec import (
    STYLE_FIELDS,
    BlockType,
    LayoutSpec,
    MoneyRole,
    ReceiptStyle,
)

__all__ = [
    "STYLE_FIELDS",
    "BlockType",
    "LayoutSpec",
    "MoneyRole",
    "Prior",
    "ReceiptStyle",
    "load_prior",
    "sample_spec",
    "stratified_specs",
]
