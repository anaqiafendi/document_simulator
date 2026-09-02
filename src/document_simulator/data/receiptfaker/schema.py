"""Pydantic models mirroring the ReceiptFaker template payload.

The payload is embedded in each ``/generate/<slug>`` page as part of the Next.js
RSC flight stream. Field value spaces (font names, divider styles, background
types) are treated as open strings rather than closed enums: the discrete
category set for each dimension is discovered empirically in
:mod:`document_simulator.data.receiptfaker.taxonomy`.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, field_validator

# Section types observed in the catalogue. Kept as a permissive str so an
# unseen type surfaces in the taxonomy report rather than failing the parse.
SectionType = str

Alignment = Literal["LEFT", "CENTER", "RIGHT"]


def _as_text(value: Any) -> Any:
    """Coerce numeric JSON values to text.

    The site stores money and quantity fields as strings, but unquoted numbers
    leak through for some templates (``"total": 274.18``, ``"quantity": 1``).
    """
    if value is None:
        return ""
    if isinstance(value, (int, float)):
        return str(value)
    return value


Text = Annotated[str, BeforeValidator(_as_text)]


def _drop_rsc_sentinels(value: Any) -> Any:
    """Normalise Next.js flight sentinels (``$undefined``, ``$D<iso>``) to Python."""
    if isinstance(value, str):
        if value == "$undefined":
            return None
        if value.startswith("$D"):  # RSC date marker
            return value[2:]
    return value


class PaymentField(BaseModel):
    """A single title/value row inside a PAYMENT section."""

    model_config = ConfigDict(extra="allow")

    title: Text = ""
    value: Text = ""


class LineItem(BaseModel):
    """A purchased-goods row inside an ITEMS section."""

    model_config = ConfigDict(extra="allow")

    quantity: Text = ""
    description: Text = ""
    total: Text = ""


class ReceiptSection(BaseModel):
    """One stacked block of a receipt template."""

    model_config = ConfigDict(extra="allow")

    id: str = ""
    type: SectionType
    alignment: Alignment | None = None
    logo: str | None = None
    size: int | None = None
    business_details: str | None = Field(default=None, alias="businessDetails")
    custom: str | None = None
    is_cash: bool | None = Field(default=None, alias="isCash")
    cash_fields: list[PaymentField] = Field(default_factory=list, alias="cashFields")
    card_fields: list[PaymentField] = Field(default_factory=list, alias="cardFields")

    # ITEMS blocks
    items: list[LineItem] = Field(default_factory=list)
    total_lines: list[PaymentField] = Field(default_factory=list, alias="totalLines")
    total: Text = ""
    total_text: Text = Field(default="", alias="totalText")
    total_divider: bool = Field(default=False, alias="totalDivider")
    total_divider_type: str | None = Field(default=None, alias="totalDividerType")
    total_size_increased: str | None = Field(default=None, alias="totalSizeIncreased")

    # RESTAURANT blocks (two-column metadata)
    left_fields: list[PaymentField] = Field(default_factory=list, alias="leftFields")
    right_fields: list[PaymentField] = Field(default_factory=list, alias="rightFields")

    # BARCODE blocks
    length: int | None = None

    bottom_divider: bool = Field(default=False, alias="bottomDivider")
    bottom_divider_type: str | None = Field(default=None, alias="bottomDividerType")
    date: str | None = None

    @field_validator("*", mode="before")
    @classmethod
    def _normalise(cls, value: Any) -> Any:
        return _drop_rsc_sentinels(value)

    @property
    def has_logo(self) -> bool:
        """True when this section carries a non-empty logo image."""
        return bool(self.logo)

    @property
    def payment_fields(self) -> list[PaymentField]:
        """Whichever payment field list is active for this section."""
        return self.cash_fields if self.is_cash else self.card_fields


class ReceiptTemplate(BaseModel):
    """A complete ReceiptFaker template as served by the site."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    id: str
    slug: str
    name: str
    description: str = ""
    created_by: str | None = Field(default=None, alias="createdBy")
    created_at: str | None = Field(default=None, alias="createdAt")
    published: bool = True
    is_parent: bool = Field(default=False, alias="isParent")
    image_url: str = Field(default="", alias="imageUrl")

    # --- visual / styling dimensions ---
    font_type: str | None = Field(default=None, alias="fontType")
    text_color: str | None = Field(default=None, alias="textColor")
    currency: str | None = None
    number_format: str | None = Field(default=None, alias="numberFormat")
    background_type: str | None = Field(default=None, alias="backgroundType")
    background_crumpled: bool = Field(default=False, alias="backgroundCrumpled")

    sections: list[ReceiptSection] = Field(default_factory=list)

    @field_validator("*", mode="before")
    @classmethod
    def _normalise(cls, value: Any) -> Any:
        return _drop_rsc_sentinels(value)

    @property
    def section_types(self) -> list[SectionType]:
        """Ordered block types, i.e. the template's layout signature."""
        return [section.type for section in self.sections]
