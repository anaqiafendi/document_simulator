"""SchemaExtractor — LLM-powered field schema extraction from real document scans.

Given a batch of real-world document images (receipts, invoices, forms),
``SchemaExtractor`` calls a vision-capable LLM (GPT-4o or Claude claude-sonnet-4-6) to:

1. Identify present fields (merchant name, date, line items, totals, …)
2. Infer data types and value distributions per field
3. Return a :class:`~document_simulator.synthesis.field_schema.DocumentSchema` that
   the synthetic generator can consume to produce realistic fake values.

The LLM integration is **lazy-init** and **optional**: this module imports cleanly
with no API key configured; the extractor raises :class:`SchemaExtractionError`
only when ``extract()`` is called without credentials.

Supported backends
------------------
- ``"openai"``  — OpenAI GPT-4o via ``openai`` package
- ``"anthropic"`` — Claude claude-sonnet-4-6 via ``anthropic`` package
- ``"mock"``    — Deterministic stub for testing (no network calls)
"""

from __future__ import annotations

import base64
import json
import re
from io import BytesIO
from pathlib import Path
from typing import Any

from loguru import logger
from PIL import Image
from pydantic import BaseModel

from document_simulator.synthesis.field_schema import (
    DocumentSchema,
    FieldDataType,
    FieldSchema,
)

# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class SchemaExtractionError(Exception):
    """Raised when schema extraction fails (no API key, network error, etc.)."""


class SchemaParseError(SchemaExtractionError):
    """Raised when the LLM response cannot be parsed into a DocumentSchema."""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are a document analysis expert. Given one or more document images, extract a
structured schema describing the fields present in the document.

Respond ONLY with a single JSON object — no markdown, no prose — with this exact shape:

{
  "document_type": "<receipt|invoice|form|other>",
  "language": "<ISO 639-1 code, e.g. en|fr|ja>",
  "currency": "<ISO 4217 code or symbol, e.g. USD|EUR|CAD|¥>",
  "confidence": <0.0–1.0>,
  "fields": [
    {
      "field_name": "<snake_case machine name>",
      "display_label": "<label as it appears in the document>",
      "data_type": "<text|name|date|amount|phone|email|address|number|percentage|currency_code|language_code|line_items|boolean|unknown>",
      "required": <true|false>,
      "example_values": ["<up to 5 raw string examples>"],
      "value_pattern": "<optional regex or format hint, or null>",
      "faker_provider": "<Faker provider name or custom key such as price_medium|date_numeric|address_single_line>",
      "notes": "<optional free-form notes about units, language, format>"
    }
  ]
}

Rules:
- Use snake_case for field_name.
- For monetary amounts use faker_provider = "price_medium" unless the amounts are typically large (>10000) → use "price_large".
- For dates use faker_provider = "date_numeric" or "date_written".
- For person names use faker_provider = "name".
- For addresses use faker_provider = "address_single_line".
- For phone numbers use faker_provider = "phone_number".
- For email use faker_provider = "email".
- For free text use faker_provider = "sentence".
- For numeric IDs use faker_provider = "numerify:########".
- Do NOT include structural template text (headers, column titles) as fields.
- line_items fields should represent one row; set required=false and notes="repeating".
"""


def _image_to_base64(image: Image.Image, max_short_side: int = 768) -> str:
    """Resize *image* so its shorter side ≤ *max_short_side*, then base64-encode as JPEG."""
    w, h = image.size
    short = min(w, h)
    if short > max_short_side:
        scale = max_short_side / short
        image = image.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    buf = BytesIO()
    image.convert("RGB").save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def _extract_json_block(text: str) -> str:
    """Strip markdown fences and return the first {...} JSON block found."""
    # Remove ```json ... ``` fences
    text = re.sub(r"```(?:json)?", "", text).strip()
    text = text.strip("`").strip()
    # Find first { ... } block
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise SchemaParseError(f"No JSON object found in LLM response: {text[:200]!r}")
    return text[start : end + 1]


def _parse_llm_response(raw: str, model_id: str, source_count: int) -> DocumentSchema:
    """Parse the raw LLM JSON string into a :class:`DocumentSchema`."""
    try:
        json_str = _extract_json_block(raw)
        data: dict[str, Any] = json.loads(json_str)
    except (json.JSONDecodeError, SchemaParseError) as exc:
        raise SchemaParseError(f"Failed to parse LLM JSON: {exc}") from exc

    fields = []
    for raw_field in data.get("fields", []):
        try:
            dt_str = raw_field.get("data_type", "unknown")
            try:
                data_type = FieldDataType(dt_str)
            except ValueError:
                data_type = FieldDataType.UNKNOWN
            fields.append(
                FieldSchema(
                    field_name=raw_field.get("field_name", "field"),
                    display_label=raw_field.get("display_label", ""),
                    data_type=data_type,
                    required=raw_field.get("required", True),
                    example_values=raw_field.get("example_values", []),
                    value_pattern=raw_field.get("value_pattern"),
                    faker_provider=raw_field.get("faker_provider", "word"),
                    notes=raw_field.get("notes", ""),
                )
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Skipping malformed field entry: {exc}")

    return DocumentSchema(
        document_type=data.get("document_type", "receipt"),
        language=data.get("language", "en"),
        currency=data.get("currency", "USD"),
        confidence=float(data.get("confidence", 0.5)),
        fields=fields,
        source_count=source_count,
        raw_llm_output=raw,
        extractor_model=model_id,
    )


# ---------------------------------------------------------------------------
# Backend implementations
# ---------------------------------------------------------------------------


def _call_openai(images_b64: list[str], model: str, api_key: str) -> str:
    """Call OpenAI vision API and return the raw text response."""
    try:
        import openai  # type: ignore[import-untyped]
    except ImportError as exc:
        raise SchemaExtractionError(
            "openai package not installed. Run: uv add openai"
        ) from exc

    client = openai.OpenAI(api_key=api_key)
    content: list[dict[str, Any]] = [{"type": "text", "text": _SYSTEM_PROMPT}]
    for b64 in images_b64:
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "low"},
            }
        )
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": content}],
        max_tokens=2048,
    )
    return response.choices[0].message.content or ""


def _call_anthropic(images_b64: list[str], model: str, api_key: str) -> str:
    """Call Anthropic Claude vision API and return the raw text response."""
    try:
        import anthropic as ant  # type: ignore[import-untyped]
    except ImportError as exc:
        raise SchemaExtractionError(
            "anthropic package not installed. Run: uv add anthropic"
        ) from exc

    client = ant.Anthropic(api_key=api_key)
    content: list[dict[str, Any]] = []
    for b64 in images_b64:
        content.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": b64,
                },
            }
        )
    content.append({"type": "text", "text": _SYSTEM_PROMPT})

    response = client.messages.create(
        model=model,
        max_tokens=2048,
        messages=[{"role": "user", "content": content}],
    )
    return response.content[0].text  # type: ignore[index,union-attr]


def _call_mock(images_b64: list[str], model: str, api_key: str) -> str:  # noqa: ARG001
    """Deterministic mock backend — no network calls."""
    return json.dumps(
        {
            "document_type": "receipt",
            "language": "en",
            "currency": "USD",
            "confidence": 0.92,
            "fields": [
                {
                    "field_name": "merchant_name",
                    "display_label": "Merchant",
                    "data_type": "name",
                    "required": True,
                    "example_values": ["Coffee House", "Air Canada"],
                    "value_pattern": None,
                    "faker_provider": "company",
                    "notes": "",
                },
                {
                    "field_name": "transaction_date",
                    "display_label": "Date",
                    "data_type": "date",
                    "required": True,
                    "example_values": ["2024-03-15", "15/03/2024"],
                    "value_pattern": r"\d{4}-\d{2}-\d{2}",
                    "faker_provider": "date_numeric",
                    "notes": "",
                },
                {
                    "field_name": "total_amount",
                    "display_label": "Total",
                    "data_type": "amount",
                    "required": True,
                    "example_values": ["$12.50", "$8.75"],
                    "value_pattern": r"\$\d+\.\d{2}",
                    "faker_provider": "price_medium",
                    "notes": "",
                },
                {
                    "field_name": "tax_amount",
                    "display_label": "Tax",
                    "data_type": "amount",
                    "required": False,
                    "example_values": ["$1.63", "$1.14"],
                    "value_pattern": None,
                    "faker_provider": "price_short",
                    "notes": "HST/GST",
                },
            ],
        }
    )


_BACKENDS: dict[str, Any] = {
    "openai": _call_openai,
    "anthropic": _call_anthropic,
    "mock": _call_mock,
}

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


class SchemaExtractorConfig(BaseModel):
    """Configuration for :class:`SchemaExtractor`.

    Attributes:
        backend:   LLM provider. One of ``"openai"``, ``"anthropic"``, ``"mock"``.
        model:     Model ID.  Defaults to the recommended model per backend.
        api_key:   API key.  If ``None``, the extractor reads from the
                   standard env var (``OPENAI_API_KEY`` / ``ANTHROPIC_API_KEY``).
        max_images: Maximum number of images sent in a single LLM call.
        max_short_side: Resize images so their shorter side ≤ this value (pixels).
    """

    backend: str = "openai"
    model: str = ""
    api_key: str | None = None
    max_images: int = 5
    max_short_side: int = 768

    def effective_model(self) -> str:
        if self.model:
            return self.model
        defaults = {
            "openai": "gpt-4o",
            "anthropic": "claude-sonnet-4-6",
            "mock": "mock-v1",
        }
        return defaults.get(self.backend, "gpt-4o")

    def effective_api_key(self) -> str | None:
        if self.api_key:
            return self.api_key
        import os

        if self.backend == "openai":
            return os.environ.get("OPENAI_API_KEY")
        if self.backend == "anthropic":
            return os.environ.get("ANTHROPIC_API_KEY")
        return None  # mock backend needs no key


# ---------------------------------------------------------------------------
# Public class
# ---------------------------------------------------------------------------


class SchemaExtractor:
    """Extract a :class:`DocumentSchema` from one or more document image scans.

    The extractor is lazy-init: instantiating it does **not** require an API
    key. The key is resolved (from ``config.api_key`` or the appropriate
    environment variable) only when :meth:`extract` is called.

    Usage::

        extractor = SchemaExtractor()               # defaults to openai/gpt-4o
        schema = extractor.extract(["receipt1.jpg", "receipt2.jpg"])

        # Anthropic backend
        extractor = SchemaExtractor(
            SchemaExtractorConfig(backend="anthropic")
        )

        # Mock backend (no API key needed)
        extractor = SchemaExtractor(SchemaExtractorConfig(backend="mock"))
        schema = extractor.extract([pil_image])

    Args:
        config: Optional :class:`SchemaExtractorConfig`. Uses defaults when
                ``None``.
    """

    def __init__(self, config: SchemaExtractorConfig | None = None) -> None:
        self._config = config or SchemaExtractorConfig()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract(
        self,
        images: list[str | Path | Image.Image],
        *,
        document_type_hint: str | None = None,
    ) -> DocumentSchema:
        """Analyse *images* and return a :class:`DocumentSchema`.

        Args:
            images: One or more document images.  Accepts file paths (str /
                    :class:`pathlib.Path`) or PIL ``Image`` objects.
            document_type_hint: Optional hint passed to the LLM (e.g.
                ``"receipt"``).  When provided it is appended to the system
                prompt.

        Returns:
            A :class:`DocumentSchema` populated by the LLM.

        Raises:
            SchemaExtractionError: If no API key is configured (for non-mock
                backends), or if the LLM call fails.
            SchemaParseError: If the LLM response cannot be parsed.
        """
        cfg = self._config
        backend_fn = _BACKENDS.get(cfg.backend)
        if backend_fn is None:
            raise SchemaExtractionError(
                f"Unknown backend {cfg.backend!r}. Choose from: {list(_BACKENDS)}"
            )

        if cfg.backend != "mock":
            api_key = cfg.effective_api_key()
            if not api_key:
                raise SchemaExtractionError(
                    f"No API key for backend {cfg.backend!r}. "
                    f"Set OPENAI_API_KEY / ANTHROPIC_API_KEY or pass config.api_key."
                )
        else:
            api_key = ""

        pil_images = self._load_images(images)
        sample = pil_images[: cfg.max_images]
        images_b64 = [_image_to_base64(img, cfg.max_short_side) for img in sample]

        model = cfg.effective_model()
        logger.info(
            f"SchemaExtractor: calling {cfg.backend}/{model} with {len(sample)} image(s)"
        )

        try:
            raw = backend_fn(images_b64, model, api_key)
        except SchemaExtractionError:
            raise
        except Exception as exc:
            raise SchemaExtractionError(f"LLM call failed: {exc}") from exc

        schema = _parse_llm_response(raw, model_id=model, source_count=len(pil_images))
        if document_type_hint and not schema.document_type:
            schema = schema.model_copy(update={"document_type": document_type_hint})

        logger.info(
            f"SchemaExtractor: extracted {len(schema.fields)} fields "
            f"(confidence={schema.confidence:.2f}, lang={schema.language})"
        )
        return schema

    def extract_batch(
        self,
        image_batches: list[list[str | Path | Image.Image]],
        *,
        document_type_hint: str | None = None,
    ) -> list[DocumentSchema]:
        """Run :meth:`extract` on multiple batches and return one schema per batch.

        Useful when the input contains multiple document *types* that need
        separate schemas.
        """
        return [
            self.extract(batch, document_type_hint=document_type_hint)
            for batch in image_batches
        ]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _load_images(images: list[str | Path | Image.Image]) -> list[Image.Image]:
        """Load and validate images from mixed path/PIL input."""
        loaded: list[Image.Image] = []
        for item in images:
            if isinstance(item, Image.Image):
                loaded.append(item)
            else:
                path = Path(item)
                if not path.exists():
                    raise SchemaExtractionError(f"Image path does not exist: {path}")
                loaded.append(Image.open(path).convert("RGB"))
        if not loaded:
            raise SchemaExtractionError("No images provided.")
        return loaded
