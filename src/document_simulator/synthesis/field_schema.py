"""Pydantic models for LLM-extracted document field schemas."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class FieldDataType(str, Enum):
    """Semantic data type of a document field."""

    TEXT = "text"
    NAME = "name"
    DATE = "date"
    TIME = "time"
    DATETIME = "datetime"
    NUMBER = "number"
    CURRENCY = "currency"
    PHONE = "phone"
    EMAIL = "email"
    ADDRESS = "address"
    COMPANY = "company"
    ID = "id"
    CHECKBOX = "checkbox"
    SIGNATURE = "signature"
    OTHER = "other"


class FieldSchema(BaseModel):
    """Schema for a single document field detected by the extractor."""

    field_name: str = Field(..., description="Human-readable field label (e.g. 'Invoice Date')")
    data_type: FieldDataType = Field(default=FieldDataType.TEXT, description="Semantic data type")
    description: str = Field(default="", description="Brief description of what this field contains")
    example_values: list[str] = Field(
        default_factory=list,
        description="Example values extracted from the sample images",
    )
    faker_provider: Optional[str] = Field(
        default=None,
        description="Suggested Faker provider string (e.g. 'name', 'date', 'company')",
    )
    required: bool = Field(default=True, description="Whether this field is typically present")


class DocumentSchema(BaseModel):
    """Full schema describing the fields in a class of documents."""

    document_type: str = Field(
        default="document",
        description="Inferred document type (e.g. 'invoice', 'receipt', 'form')",
    )
    fields: list[FieldSchema] = Field(default_factory=list)
    notes: str = Field(
        default="",
        description="Free-form notes from the extractor about the document layout",
    )
    backend_used: str = Field(
        default="mock",
        description="Which LLM backend was used to extract this schema",
    )
