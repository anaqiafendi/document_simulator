"""LLM-backed schema extractor for document images.

Supported backends (in recommended order):

- ``mock``       — deterministic fake response, no API key needed (great for tests)
- ``gemini``     — Google Gemini via google-genai SDK (free tier)
- ``groq``       — Groq API with LLaMA vision (free tier)
- ``openai``     — OpenAI GPT-4o vision API
- ``anthropic``  — Anthropic Claude vision API
- ``vertex_ai``  — Google Vertex AI (Gemini on GCP, service-account auth)

All provider packages are optional and lazy-imported. A missing package raises a
:class:`SchemaExtractionError` with the install command instead of a cryptic
ImportError at startup.

The extractor asks the LLM to emit (for every field):

- ``field_name`` / ``display_label`` / ``data_type`` / ``example_values``
- A **bounding box** (normalised to [0, 1]) identifying where the value sits on
  the page — used by the UI to overlay green rectangles on the scan preview
- ``language`` (BCP-47) and ``currency`` (ISO 4217) per field for multi-lingual
  / multi-currency documents
- Structured ``line_items`` for invoices and receipts (each with its own
  currency + language)

Public surface:

- :class:`SchemaExtractor` — configure a backend, then call :meth:`extract`
  (consolidated schema) or :meth:`extract_per_image` (one schema per image).
- :class:`SchemaExtractorConfig` — Pydantic config (backend, api_key, model, …).
- :class:`SchemaExtractionError` / :class:`SchemaParseError` — typed failures.
"""

from __future__ import annotations

import base64
import io
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Literal, Union

from loguru import logger
from PIL import Image
from pydantic import BaseModel

from document_simulator.synthesis.field_schema import (
    BoundingBox,
    DocumentSchema,
    FieldDataType,
    FieldSchema,
    LineItem,
)

Backend = Literal["mock", "gemini", "groq", "openai", "anthropic", "vertex_ai"]

ImageInput = Union[Image.Image, str, Path]


# ── Exceptions ───────────────────────────────────────────────────────────────


class SchemaExtractionError(RuntimeError):
    """Raised when the extractor cannot produce a schema (API / IO / auth)."""


class SchemaParseError(SchemaExtractionError):
    """Raised when the LLM response cannot be parsed into a DocumentSchema."""


# ── Default model IDs per backend ────────────────────────────────────────────


_DEFAULT_MODELS: dict[str, str] = {
    "mock": "mock-v1",
    "openai": "gpt-4o",
    "anthropic": "claude-opus-4-5",
    "gemini": "gemini-2.0-flash-001",
    "groq": "meta-llama/llama-4-scout-17b-16e-instruct",
    "vertex_ai": "gemini-2.0-flash",
}

# Candidate Gemini models tried in order if the configured one is unavailable.
_GEMINI_FALLBACKS: list[str] = [
    "gemini-2.5-flash-preview-04-17",
    "gemini-2.0-flash-001",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
]

_BACKEND_API_KEY_ENV: dict[str, list[str]] = {
    "openai": ["OPENAI_API_KEY"],
    "anthropic": ["ANTHROPIC_API_KEY"],
    "gemini": ["GOOGLE_API_KEY", "GEMINI_API_KEY"],
    "groq": ["GROQ_API_KEY"],
    "vertex_ai": [],
}


# ── Prompts ───────────────────────────────────────────────────────────────────


_SYSTEM_PROMPT = """\
You are a document-analysis assistant. Given ONE document image, identify every
distinct fillable / data field present and return a JSON object describing the
schema.

For every field, emit:
- field_name (snake_case machine-readable label, e.g. "merchant_name")
- display_label (label as it appears on the document, e.g. "Merchant")
- data_type — one of: text, name, date, time, datetime, number, amount,
  currency, percentage, currency_code, language_code, phone, email, address,
  company, id, checkbox, signature, boolean, other, unknown
- description — one short sentence explaining the field
- example_values — up to 5 raw strings copied from the image
- faker_provider — suggested Faker method (name, date, email, company, phone,
  address, pricetag, …) or null
- required — true / false
- language — BCP-47 / ISO 639-1 code of the field's value (e.g. "en", "fr",
  "ja"), or null if the field has no text
- currency — ISO 4217 code if the field holds a monetary amount (e.g. "USD",
  "CAD", "EUR"), or null otherwise
- bbox — {"x1":…, "y1":…, "x2":…, "y2":…} normalised to [0, 1] with the
  TOP-LEFT of the image at (0, 0) and BOTTOM-RIGHT at (1, 1).

If the document is an invoice / receipt, ALSO emit a "line_items" array:
[
  {
    "description": "…",
    "quantity": <number|null>,
    "unit_price": "<formatted string>",
    "total": "<formatted string>",
    "currency": "USD",
    "language": "en",
    "bbox": {"x1":…,"y1":…,"x2":…,"y2":…}
  }
]

Return ONLY a valid JSON object with this structure — no prose:
{
  "document_type": "<string>",
  "language": "<BCP-47 code, primary language>",
  "currency": "<ISO 4217, primary currency>",
  "confidence": <float 0..1>,
  "fields": [ ... ],
  "line_items": [ ... ],
  "notes": "<string>"
}
"""


_USER_PROMPT = (
    "Analyse the attached document image and return the schema JSON as instructed."
)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _image_to_base64(
    source: ImageInput,
    max_short_side: int = 1024,
) -> str:
    """Return a PNG base64 string for *source*.

    Accepts a PIL image or a filesystem path. Large images are downscaled so
    the shorter side is ``max_short_side``px, keeping LLM payloads sane.
    """
    if isinstance(source, (str, Path)):
        path = Path(source)
        if not path.exists():
            raise SchemaExtractionError(f"Image path does not exist: {path}")
        img = Image.open(path).convert("RGB")
    elif isinstance(source, Image.Image):
        img = source.convert("RGB")
    else:
        raise SchemaExtractionError(f"Unsupported image input: {type(source).__name__}")

    w, h = img.size
    short = min(w, h)
    if short > max_short_side:
        scale = max_short_side / short
        img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def _extract_json_block(raw: str) -> str:
    """Extract a JSON object substring from a raw LLM response.

    Handles:
    - Plain JSON
    - ```json …``` or ```…``` fenced code blocks
    - JSON embedded in prose (greedy first ``{…}`` match)

    Raises :class:`SchemaParseError` if no JSON object can be found.
    """
    text = raw.strip()

    # Strip markdown fences first
    fence = re.match(r"^```(?:json|JSON)?\s*\n(.*?)\n?```\s*$", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()

    # Greedy: first { to last } — handles prose before/after
    first = text.find("{")
    last = text.rfind("}")
    if first == -1 or last == -1 or last <= first:
        raise SchemaParseError(f"No JSON object found in LLM response. Raw: {raw[:200]}")
    return text[first : last + 1]


def _parse_bbox(raw: Any) -> BoundingBox | None:
    """Best-effort parse of a bbox dict from an LLM response."""
    if not isinstance(raw, dict):
        return None
    try:
        return BoundingBox(
            x1=float(raw.get("x1", raw.get("x", 0.0))),
            y1=float(raw.get("y1", raw.get("y", 0.0))),
            x2=float(raw.get("x2", float(raw.get("x", 0.0)) + float(raw.get("w", 0.0)))),
            y2=float(raw.get("y2", float(raw.get("y", 0.0)) + float(raw.get("h", 0.0)))),
        )
    except Exception as exc:
        logger.debug(f"Skipping malformed bbox {raw!r}: {exc}")
        return None


def _parse_line_item(raw: Any) -> LineItem | None:
    if not isinstance(raw, dict):
        return None
    try:
        return LineItem(
            description=str(raw.get("description", "")),
            quantity=raw.get("quantity"),
            unit_price=raw.get("unit_price"),
            total=raw.get("total"),
            currency=raw.get("currency"),
            language=raw.get("language"),
            bbox=_parse_bbox(raw.get("bbox")),
        )
    except Exception as exc:
        logger.debug(f"Skipping malformed line_item {raw!r}: {exc}")
        return None


def _parse_llm_response(
    raw: str,
    model_id: str = "",
    source_count: int = 1,
    backend: str = "",
    source_image_index: int = 0,
    source_image_size: tuple[int, int] | None = None,
) -> DocumentSchema:
    """Parse a raw LLM JSON response into a :class:`DocumentSchema`.

    Raises :class:`SchemaParseError` if the response is not valid JSON.
    """
    block = _extract_json_block(raw)
    try:
        data = json.loads(block)
    except json.JSONDecodeError as exc:
        raise SchemaParseError(f"LLM returned invalid JSON: {exc}. Raw: {block[:200]}") from exc
    if not isinstance(data, dict):
        raise SchemaParseError("LLM JSON root must be an object.")

    # Fields
    fields: list[FieldSchema] = []
    for f in data.get("fields", []):
        if not isinstance(f, dict):
            logger.warning(f"Skipping malformed field {f!r}")
            continue
        try:
            fields.append(
                FieldSchema(
                    field_name=str(f.get("field_name", "field")),
                    display_label=str(f.get("display_label", "") or ""),
                    data_type=f.get("data_type", FieldDataType.UNKNOWN),
                    required=bool(f.get("required", True)),
                    example_values=[str(v) for v in (f.get("example_values") or [])],
                    value_pattern=f.get("value_pattern"),
                    faker_provider=str(f.get("faker_provider") or "word"),
                    description=str(f.get("description", "") or ""),
                    notes=str(f.get("notes", "") or ""),
                    language=f.get("language"),
                    currency=f.get("currency"),
                    bbox=_parse_bbox(f.get("bbox")),
                )
            )
        except Exception as exc:
            logger.warning(f"Skipping malformed field {f!r}: {exc}")

    # Line items
    line_items: list[LineItem] = []
    for li in data.get("line_items", []) or []:
        parsed = _parse_line_item(li)
        if parsed is not None:
            line_items.append(parsed)

    width = height = None
    if source_image_size is not None:
        width, height = source_image_size

    return DocumentSchema(
        document_type=str(data.get("document_type", "document") or "document"),
        language=str(data.get("language", "en") or "en"),
        currency=str(data.get("currency", "USD") or "USD"),
        fields=fields,
        line_items=line_items,
        confidence=float(data.get("confidence", 0.0) or 0.0),
        source_count=source_count,
        source_image_index=source_image_index,
        source_image_width=width,
        source_image_height=height,
        raw_llm_output=block,
        extractor_model=model_id,
        backend_used=backend or model_id,
        notes=str(data.get("notes", "") or ""),
    )


# ── Mock backend ──────────────────────────────────────────────────────────────


def _call_mock(images_b64: list[str], model_id: str, document_type_hint: str) -> str:
    """Deterministic mock response — returns plausible receipt JSON."""
    doc_type = document_type_hint or "receipt"
    payload = {
        "document_type": doc_type,
        "language": "en",
        "currency": "USD",
        "confidence": 0.82,
        "fields": [
            {
                "field_name": "merchant_name",
                "display_label": "Merchant",
                "data_type": "company",
                "description": "Name of the merchant or issuing organisation",
                "example_values": ["Quick Mart", "Acme Corp"],
                "faker_provider": "company",
                "required": True,
                "language": "en",
                "currency": None,
                "bbox": {"x1": 0.08, "y1": 0.05, "x2": 0.62, "y2": 0.11},
            },
            {
                "field_name": "transaction_date",
                "display_label": "Date",
                "data_type": "date",
                "description": "Date the transaction was issued",
                "example_values": ["2024-03-15", "15/03/2024"],
                "faker_provider": "date",
                "required": True,
                "language": "en",
                "currency": None,
                "bbox": {"x1": 0.62, "y1": 0.05, "x2": 0.94, "y2": 0.10},
            },
            {
                "field_name": "total_amount",
                "display_label": "Total",
                "data_type": "currency",
                "description": "Total amount paid",
                "example_values": ["$42.50", "$18.99"],
                "faker_provider": "pricetag",
                "required": True,
                "language": "en",
                "currency": "USD",
                "bbox": {"x1": 0.55, "y1": 0.82, "x2": 0.94, "y2": 0.90},
            },
            {
                "field_name": "tax_amount",
                "display_label": "Tax",
                "data_type": "currency",
                "description": "Sales / VAT tax on the transaction",
                "example_values": ["$3.40"],
                "faker_provider": "pricetag",
                "required": False,
                "language": "en",
                "currency": "USD",
                "bbox": {"x1": 0.55, "y1": 0.74, "x2": 0.94, "y2": 0.80},
            },
        ],
        "line_items": [
            {
                "description": "Coffee — medium",
                "quantity": 1,
                "unit_price": "$4.50",
                "total": "$4.50",
                "currency": "USD",
                "language": "en",
                "bbox": {"x1": 0.08, "y1": 0.40, "x2": 0.94, "y2": 0.46},
            },
            {
                "description": "Blueberry muffin",
                "quantity": 2,
                "unit_price": "$3.25",
                "total": "$6.50",
                "currency": "USD",
                "language": "en",
                "bbox": {"x1": 0.08, "y1": 0.46, "x2": 0.94, "y2": 0.52},
            },
        ],
        "notes": (
            f"Mock schema ({model_id}) — no LLM called. "
            "Upload real images with Gemini / Groq / GPT-4o to extract from a real scan."
        ),
    }
    return json.dumps(payload)


# ── Real backends ────────────────────────────────────────────────────────────


def _call_gemini(images_b64: list[str], model_id: str, api_key: str) -> str:
    try:
        from google import genai  # type: ignore[import-untyped]
        from google.genai import types as genai_types  # type: ignore[import-untyped]
    except ImportError as exc:
        raise SchemaExtractionError(
            "google-genai package not installed. Run: uv add google-genai"
        ) from exc

    client = genai.Client(api_key=api_key)
    contents = [
        genai_types.Content(
            role="user",
            parts=[
                genai_types.Part(text=f"{_SYSTEM_PROMPT}\n\n{_USER_PROMPT}"),
                *[
                    genai_types.Part(
                        inline_data=genai_types.Blob(
                            mime_type="image/png",
                            data=base64.b64decode(b64),
                        )
                    )
                    for b64 in images_b64
                ],
            ],
        )
    ]

    candidates = [model_id] if model_id and model_id != _DEFAULT_MODELS["gemini"] else _GEMINI_FALLBACKS
    last_exc: Exception | None = None
    for mid in candidates:
        try:
            response = client.models.generate_content(
                model=mid,
                contents=contents,
                config=genai_types.GenerateContentConfig(temperature=0, max_output_tokens=4096),
            )
            logger.info(f"Gemini: used model {mid!r}")
            return response.text or "{}"
        except Exception as api_exc:
            err = repr(api_exc)
            if "404" in err or "NOT_FOUND" in err or "no longer available" in err:
                logger.warning(f"Gemini model {mid!r} unavailable, trying next: {api_exc}")
                last_exc = api_exc
                continue
            raise SchemaExtractionError(
                f"Gemini API error ({type(api_exc).__name__}): {api_exc!r}"
            ) from api_exc
    raise SchemaExtractionError(
        f"No available Gemini model found. Tried: {candidates}. Last error: {last_exc!r}"
    )


def _call_groq(images_b64: list[str], model_id: str, api_key: str) -> str:
    try:
        from groq import Groq  # type: ignore[import-untyped]
    except ImportError as exc:
        raise SchemaExtractionError("groq package not installed. Run: uv add groq") from exc

    client = Groq(api_key=api_key)
    content: list[dict] = [{"type": "text", "text": _USER_PROMPT}]
    for b64 in images_b64:
        content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}})

    try:
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": content},
            ],
            max_tokens=4096,
            temperature=0,
        )
    except Exception as api_exc:
        raise SchemaExtractionError(
            f"Groq API error ({type(api_exc).__name__}): {api_exc!r}"
        ) from api_exc
    return response.choices[0].message.content or "{}"


def _call_openai(images_b64: list[str], model_id: str, api_key: str) -> str:
    try:
        from openai import OpenAI  # type: ignore[import-untyped]
    except ImportError as exc:
        raise SchemaExtractionError("openai package not installed. Run: uv add openai") from exc

    client = OpenAI(api_key=api_key)
    content: list[dict] = [{"type": "text", "text": _USER_PROMPT}]
    for b64 in images_b64:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{b64}", "detail": "high"},
        })
    try:
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": content},
            ],
            max_tokens=4096,
            temperature=0,
        )
    except Exception as api_exc:
        raise SchemaExtractionError(
            f"OpenAI API error ({type(api_exc).__name__}): {api_exc!r}"
        ) from api_exc
    return response.choices[0].message.content or "{}"


def _call_anthropic(images_b64: list[str], model_id: str, api_key: str) -> str:
    try:
        import anthropic as anthropic_sdk  # type: ignore[import-untyped]
    except ImportError as exc:
        raise SchemaExtractionError("anthropic package not installed. Run: uv add anthropic") from exc

    client = anthropic_sdk.Anthropic(api_key=api_key)
    content: list[dict] = []
    for b64 in images_b64:
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": "image/png", "data": b64},
        })
    content.append({"type": "text", "text": _USER_PROMPT})
    try:
        response = client.messages.create(
            model=model_id,
            max_tokens=4096,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": content}],
        )
    except Exception as api_exc:
        raise SchemaExtractionError(
            f"Anthropic API error ({type(api_exc).__name__}): {api_exc!r}"
        ) from api_exc
    return response.content[0].text if response.content else "{}"


def _call_vertex(
    images_b64: list[str],
    model_id: str,
    service_account_json: str | None,
) -> str:
    try:
        import vertexai  # type: ignore[import-untyped]
        from vertexai.generative_models import GenerativeModel  # type: ignore[import-untyped]
    except ImportError as exc:
        raise SchemaExtractionError(
            "Vertex AI package not installed. Run: uv add google-cloud-aiplatform"
        ) from exc

    if service_account_json:
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        tmp.write(service_account_json)
        tmp.flush()
        tmp.close()
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = tmp.name

    project = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCLOUD_PROJECT")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

    try:
        vertexai.init(project=project, location=location)
        model = GenerativeModel(model_name=model_id, system_instruction=_SYSTEM_PROMPT)
        parts: list = [_USER_PROMPT]
        for b64 in images_b64:
            parts.append({"mime_type": "image/png", "data": b64})
        response = model.generate_content(parts)
        return response.text or "{}"
    except Exception as api_exc:
        raise SchemaExtractionError(
            f"Vertex AI error ({type(api_exc).__name__}): {api_exc!r}"
        ) from api_exc


# ── Config + Extractor ────────────────────────────────────────────────────────


class SchemaExtractorConfig(BaseModel):
    """Configuration for :class:`SchemaExtractor`."""

    backend: str = "mock"
    api_key: str | None = None
    service_account_json: str | None = None
    model: str | None = None
    max_images: int = 10
    max_short_side: int = 1024
    request_timeout_s: float = 60.0

    def effective_model(self) -> str:
        """Return ``self.model`` or the backend's default."""
        if self.model:
            return self.model
        return _DEFAULT_MODELS.get(self.backend, self.backend)

    def effective_api_key(self) -> str | None:
        """Return the API key (explicit or from env); ``None`` if missing."""
        if self.api_key:
            return self.api_key
        for var in _BACKEND_API_KEY_ENV.get(self.backend, []):
            val = os.environ.get(var)
            if val:
                return val
        return None


class SchemaExtractor:
    """Extract :class:`DocumentSchema` objects from document scan images.

    Args:
        config: :class:`SchemaExtractorConfig` with backend + credentials.
            If omitted, defaults to mock (no API key required).

    Typical usage::

        extractor = SchemaExtractor(SchemaExtractorConfig(backend="gemini", api_key="…"))
        schemas = extractor.extract_per_image([scan1, scan2])  # list[DocumentSchema]

    For backward compatibility, :meth:`extract` still returns a single
    :class:`DocumentSchema` (consolidated across all inputs).
    """

    def __init__(self, config: SchemaExtractorConfig | None = None) -> None:
        self.config = config or SchemaExtractorConfig()

    # ------------------------------------------------------------------ public

    def extract(
        self,
        images: list[ImageInput],
        document_type_hint: str = "",
    ) -> DocumentSchema:
        """Extract a single consolidated schema from 1–``max_images`` scans."""
        imgs = self._prepare_images(images)
        total = len(images)
        sample = imgs[: self.config.max_images]

        b64 = [_image_to_base64(img, self.config.max_short_side) for img in sample]
        raw = self._call_backend(b64, document_type_hint)
        first_size = sample[0].size if isinstance(sample[0], Image.Image) else None
        schema = _parse_llm_response(
            raw,
            model_id=self.config.effective_model(),
            source_count=total,
            backend=self.config.backend,
            source_image_index=0,
            source_image_size=first_size,
        )

        if document_type_hint and not schema.document_type:
            schema = schema.model_copy(update={"document_type": document_type_hint})
        return schema

    def extract_per_image(
        self,
        images: list[ImageInput],
        document_type_hint: str = "",
    ) -> list[DocumentSchema]:
        """Extract ONE schema per uploaded image (up to ``max_images``).

        This is what the UI uses so every thumbnail gets its own schema tab —
        no more forced consolidation.
        """
        imgs = self._prepare_images(images)
        total = len(images)
        sample = imgs[: self.config.max_images]

        schemas: list[DocumentSchema] = []
        for idx, img in enumerate(sample):
            b64 = _image_to_base64(img, self.config.max_short_side)
            raw = self._call_backend([b64], document_type_hint)
            size = img.size if isinstance(img, Image.Image) else None
            schema = _parse_llm_response(
                raw,
                model_id=self.config.effective_model(),
                source_count=total,
                backend=self.config.backend,
                source_image_index=idx,
                source_image_size=size,
            )
            if document_type_hint and not schema.document_type:
                schema = schema.model_copy(update={"document_type": document_type_hint})
            schemas.append(schema)
        return schemas

    def extract_batch(
        self,
        image_groups: list[list[ImageInput]],
        document_type_hint: str = "",
    ) -> list[DocumentSchema]:
        """Run :meth:`extract` on each list in ``image_groups``."""
        return [self.extract(g, document_type_hint) for g in image_groups]

    # ----------------------------------------------------------------- helpers

    def _prepare_images(self, images: list[ImageInput]) -> list[Image.Image]:
        if not images:
            raise SchemaExtractionError("At least one image is required.")
        out: list[Image.Image] = []
        for item in images:
            if isinstance(item, (str, Path)):
                path = Path(item)
                if not path.exists():
                    raise SchemaExtractionError(f"Image path does not exist: {path}")
                out.append(Image.open(path).convert("RGB"))
            elif isinstance(item, Image.Image):
                out.append(item.convert("RGB"))
            else:
                raise SchemaExtractionError(
                    f"Unsupported image input type: {type(item).__name__}"
                )
        return out

    _API_KEY_BACKENDS = {"gemini", "groq", "openai", "anthropic"}

    def _call_backend(self, images_b64: list[str], document_type_hint: str) -> str:
        backend = self.config.backend
        model_id = self.config.effective_model()

        if backend == "mock":
            return _call_mock(images_b64, model_id, document_type_hint)
        if backend == "vertex_ai":
            return _call_vertex(images_b64, model_id, self.config.service_account_json)
        if backend not in self._API_KEY_BACKENDS:
            raise SchemaExtractionError(f"Unknown backend: {backend!r}")

        api_key = self.config.effective_api_key()
        if not api_key:
            env_var = _BACKEND_API_KEY_ENV.get(backend, ["<env>"])[0]
            raise SchemaExtractionError(
                f"No API key configured for backend {backend!r}. "
                f"Provide one via SchemaExtractorConfig(api_key=…) or the {env_var} env var."
            )

        if backend == "gemini":
            return _call_gemini(images_b64, model_id, api_key)
        if backend == "groq":
            return _call_groq(images_b64, model_id, api_key)
        if backend == "openai":
            return _call_openai(images_b64, model_id, api_key)
        if backend == "anthropic":
            return _call_anthropic(images_b64, model_id, api_key)

        raise SchemaExtractionError(f"Unknown backend: {backend!r}")


__all__ = [
    "Backend",
    "SchemaExtractor",
    "SchemaExtractorConfig",
    "SchemaExtractionError",
    "SchemaParseError",
    "_call_mock",
    "_extract_json_block",
    "_image_to_base64",
    "_parse_llm_response",
]
