"""LLM-backed schema extractor for document images.

Supported backends:
- ``mock``     — deterministic fake response, no API key needed (default)
- ``openai``   — uses OpenAI vision API (requires ``OPENAI_API_KEY`` env var)
- ``anthropic`` — uses Anthropic Claude vision API (requires ``ANTHROPIC_API_KEY`` env var)
"""

from __future__ import annotations

import base64
import io
import json
import os
from typing import Literal

from loguru import logger
from PIL import Image

from document_simulator.synthesis.field_schema import (
    DocumentSchema,
    FieldDataType,
    FieldSchema,
)

Backend = Literal["mock", "openai", "anthropic"]

_SYSTEM_PROMPT = """\
You are a document analysis assistant. Given one or more sample document images,
identify every distinct fillable/data field present across the documents.

Return ONLY a valid JSON object with this exact structure:
{
  "document_type": "<string>",
  "fields": [
    {
      "field_name": "<string>",
      "data_type": "<one of: text, name, date, time, datetime, number, currency, phone, email, address, company, id, checkbox, signature, other>",
      "description": "<string>",
      "example_values": ["<string>", ...],
      "faker_provider": "<string or null>",
      "required": <true|false>
    },
    ...
  ],
  "notes": "<string>"
}

Do not include any explanation outside the JSON object.
"""

_USER_PROMPT = (
    "Analyse the document image(s) attached and return the schema JSON as instructed."
)

# ── Mock backend ──────────────────────────────────────────────────────────────


def _mock_schema(n_images: int) -> DocumentSchema:
    """Return a plausible receipt schema without calling any external API."""
    fields = [
        FieldSchema(
            field_name="Vendor Name",
            data_type=FieldDataType.COMPANY,
            description="Name of the merchant or issuing organisation",
            example_values=["Quick Mart", "Acme Corp", "City Grocery"],
            faker_provider="company",
            required=True,
        ),
        FieldSchema(
            field_name="Date",
            data_type=FieldDataType.DATE,
            description="Date the transaction or document was issued",
            example_values=["2024-03-15", "15/03/2024", "March 15, 2024"],
            faker_provider="date",
            required=True,
        ),
        FieldSchema(
            field_name="Total Amount",
            data_type=FieldDataType.CURRENCY,
            description="Total amount due or paid",
            example_values=["$42.50", "€18.99", "RM 120.00"],
            faker_provider="pricetag",
            required=True,
        ),
        FieldSchema(
            field_name="Receipt Number",
            data_type=FieldDataType.ID,
            description="Unique identifier for this receipt or invoice",
            example_values=["INV-00123", "RCP-4582", "2024-00456"],
            faker_provider="bothify(text='INV-#####')",
            required=False,
        ),
        FieldSchema(
            field_name="Customer Name",
            data_type=FieldDataType.NAME,
            description="Name of the customer (if present)",
            example_values=["John Smith", "Maria Garcia", "Wei Chen"],
            faker_provider="name",
            required=False,
        ),
        FieldSchema(
            field_name="Address",
            data_type=FieldDataType.ADDRESS,
            description="Billing or delivery address",
            example_values=["123 Main St, Springfield, IL 62701"],
            faker_provider="address",
            required=False,
        ),
    ]
    return DocumentSchema(
        document_type="receipt",
        fields=fields,
        notes=f"Mock schema generated from {n_images} sample image(s). Switch to openai or anthropic backend for real extraction.",
        backend_used="mock",
    )


# ── OpenAI backend ────────────────────────────────────────────────────────────


def _openai_schema(images_b64: list[str]) -> DocumentSchema:
    try:
        from openai import OpenAI  # type: ignore[import-untyped]
    except ImportError as exc:
        raise RuntimeError("openai package not installed. Run: uv add openai") from exc

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set.")

    client = OpenAI(api_key=api_key)

    content: list[dict] = [{"type": "text", "text": _USER_PROMPT}]
    for b64 in images_b64:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{b64}", "detail": "high"},
        })

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ],
        max_tokens=2048,
        temperature=0,
    )

    raw = response.choices[0].message.content or "{}"
    return _parse_llm_response(raw, backend="openai")


# ── Anthropic backend ─────────────────────────────────────────────────────────


def _anthropic_schema(images_b64: list[str]) -> DocumentSchema:
    try:
        import anthropic as anthropic_sdk  # type: ignore[import-untyped]
    except ImportError as exc:
        raise RuntimeError("anthropic package not installed. Run: uv add anthropic") from exc

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY environment variable is not set.")

    client = anthropic_sdk.Anthropic(api_key=api_key)

    content: list[dict] = []
    for b64 in images_b64:
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": "image/png", "data": b64},
        })
    content.append({"type": "text", "text": _USER_PROMPT})

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2048,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": content}],
    )

    raw = response.content[0].text if response.content else "{}"
    return _parse_llm_response(raw, backend="anthropic")


# ── Response parser ───────────────────────────────────────────────────────────


def _parse_llm_response(raw: str, backend: str) -> DocumentSchema:
    """Parse a raw LLM JSON response into a DocumentSchema."""
    # Strip markdown code fences if present
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        logger.warning(f"LLM returned invalid JSON: {exc}. Raw: {text[:200]}")
        data = {}

    # Normalise fields
    raw_fields = data.get("fields", [])
    fields: list[FieldSchema] = []
    for f in raw_fields:
        try:
            fields.append(FieldSchema.model_validate(f))
        except Exception as e:
            logger.warning(f"Skipping malformed field {f!r}: {e}")

    return DocumentSchema(
        document_type=data.get("document_type", "document"),
        fields=fields,
        notes=data.get("notes", ""),
        backend_used=backend,
    )


# ── Public API ────────────────────────────────────────────────────────────────


class SchemaExtractor:
    """Extract a DocumentSchema from one or more document scan images."""

    def __init__(self, backend: Backend = "mock") -> None:
        self.backend: Backend = backend

    def extract(self, images: list[Image.Image]) -> DocumentSchema:
        """Run schema extraction on a list of PIL images.

        Args:
            images: 1–10 document scan images (PIL RGB).

        Returns:
            DocumentSchema describing the detected fields.
        """
        if not images:
            raise ValueError("At least one image is required.")
        if len(images) > 10:
            images = images[:10]
            logger.warning("More than 10 images supplied; only the first 10 will be used.")

        logger.info(f"SchemaExtractor: backend={self.backend!r}, n_images={len(images)}")

        if self.backend == "mock":
            return _mock_schema(len(images))

        # Convert images to PNG base64 for vision APIs
        images_b64: list[str] = []
        for img in images:
            buf = io.BytesIO()
            img.convert("RGB").save(buf, format="PNG")
            images_b64.append(base64.b64encode(buf.getvalue()).decode())

        if self.backend == "openai":
            return _openai_schema(images_b64)
        if self.backend == "anthropic":
            return _anthropic_schema(images_b64)

        raise ValueError(f"Unknown backend: {self.backend!r}")
