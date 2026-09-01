"""Models describing a receipt's visual layout, independent of its content."""

from __future__ import annotations

import hashlib
import json
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, computed_field


class _StrEnum(str, Enum):
    """``enum.StrEnum`` semantics on Python 3.10.

    ``StrEnum`` is 3.11+, but this project supports 3.10 (``requires-python``,
    the trove classifiers and the mypy target all say so). A plain ``str, Enum``
    is not equivalent: its ``__str__`` returns ``"BlockType.HEADER"``, which
    would leak the class name into rendered HTML and into any f-string. The
    override restores the value-returning behaviour templates rely on.
    """

    __slots__ = ()

    def __str__(self) -> str:
        return str(self.value)


class BlockType(_StrEnum):
    """A stacked band of a receipt.

    These are the seven block types observed across the corpus. ReceiptFaker's
    ``RESTAURANT`` (two-column metadata) is renamed ``META`` here because the
    layout is not restaurant-specific -- retail receipts use it for cashier and
    lane numbers just as often.
    """

    HEADER = "HEADER"
    ITEMS = "ITEMS"
    PAYMENT = "PAYMENT"
    CUSTOM = "CUSTOM"
    DATE = "DATE"
    BARCODE = "BARCODE"
    META = "META"


class MoneyRole(_StrEnum):
    """A semantic money row. Order and presence vary per receipt."""

    ITEM = "ITEM"
    SUBTOTAL = "SUBTOTAL"
    DISCOUNT = "DISCOUNT"
    TAX = "TAX"
    TIP = "TIP"
    TOTAL = "TOTAL"
    TENDER = "TENDER"
    CHANGE = "CHANGE"
    META = "META"
    AUTH = "AUTH"


class ReceiptStyle(BaseModel):
    """The eight independently-perturbable presentation axes.

    Values are the taxonomy's own vocabulary rather than CSS, so a spec stays
    comparable against the corpus it was drawn from. Translation to CSS happens
    in the renderer.
    """

    model_config = ConfigDict(frozen=True)

    font_type: str = "MERCHANT_COPY"
    divider_style: str = "DASHES"
    total_divider_style: str = "NONE"
    total_emphasis: str = "NONE"
    number_format: str = "LEFT"
    header_alignment: str = "CENTER"
    background_type: str = "CRUMPLED_1"
    quantity_column: str = "PRESENT"


#: Field order used when perturbing style axes. Declared once so the sampler,
#: the prior loader and the tests cannot drift apart.
STYLE_FIELDS: tuple[str, ...] = tuple(ReceiptStyle.model_fields)


class LayoutSpec(BaseModel):
    """A complete recipe for how one receipt should be laid out."""

    model_config = ConfigDict(frozen=True)

    blocks: tuple[BlockType, ...]
    money_rows: tuple[MoneyRole, ...]
    style: ReceiptStyle = Field(default_factory=ReceiptStyle)

    merchant_block_position: str = "TOP"
    logo_placement: str = "TOP"
    barcode_placement: str = "NONE"

    #: Which style axes were re-rolled away from the replayed combination.
    #: Recorded so a generated dataset can be filtered back to purely observed
    #: layouts if a downstream experiment needs that.
    perturbed: tuple[str, ...] = ()

    @computed_field  # type: ignore[prop-decorator]
    @property
    def spec_id(self) -> str:
        """Stable short hash of the spec, used to key output filenames.

        Content-derived rather than random so the same spec always maps to the
        same id across processes in a batch.
        """
        payload = json.dumps(
            {
                "blocks": [b.value for b in self.blocks],
                "money_rows": [r.value for r in self.money_rows],
                "style": self.style.model_dump(),
                "merchant_block_position": self.merchant_block_position,
                "logo_placement": self.logo_placement,
                "barcode_placement": self.barcode_placement,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode()).hexdigest()[:12]

    @property
    def has_items(self) -> bool:
        """True when the layout stacks at least one ITEMS block."""
        return BlockType.ITEMS in self.blocks
