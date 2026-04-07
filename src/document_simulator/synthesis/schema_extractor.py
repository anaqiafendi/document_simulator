"""LLM-backed schema extractor for document images.

Supported backends (in recommended order):
- ``mock``       — deterministic fake response, no API key needed (great for testing)
- ``gemini``     — Google Gemini via google-genai SDK (free tier at aistudio.google.com)
- ``groq``       — Groq API with LLaMA vision (free tier at console.groq.com)
- ``openai``     — OpenAI GPT-4o vision API
- ``anthropic``  — Anthropic Claude vision API
- ``vertex_ai``  — Google Vertex AI (Gemini on GCP, service-account auth)

All provider packages are optional and lazy-imported — a missing package produces a
clear error message with the install command rather than a cryptic import failure.
"""

from __future__ import annotations

import base64
import io
import json
import os
import tempfile
from typing import Literal

from loguru import logger
from PIL import Image

from document_simulator.synthesis.field_schema import (
    DocumentSchema,
    FieldDataType,
    FieldSchema,
)

Backend = Literal["mock", "gemini", "groq", "openai", "anthropic", "vertex_ai"]

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
        notes=(
            f"Mock schema generated from {n_images} sample image(s). "
            "Use Gemini (free) or Groq (free) for real extraction."
        ),
        backend_used="mock",
    )


# ── Gemini backend ────────────────────────────────────────────────────────────


def _gemini_schema(images_b64: list[str], api_key: str | None) -> DocumentSchema:
    """Extract schema via Google Gemini (free tier via Google AI Studio).

    Uses the new ``google-genai`` SDK (v1.x), which replaced ``google-generativeai``.
    """
    try:
        from google import genai  # type: ignore[import-untyped]
        from google.genai import types as genai_types  # type: ignore[import-untyped]
    except ImportError as exc:
        raise RuntimeError(
            "google-genai package not installed. Run: uv add google-genai"
        ) from exc

    key = api_key or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError(
            "No Gemini API key found. Provide one in the UI or set GOOGLE_API_KEY env var. "
            "Get a free key at https://aistudio.google.com/app/apikey"
        )

    client = genai.Client(api_key=key)

    # Build content parts: system instruction + user prompt + images
    contents: list = [
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

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=contents,
        config=genai_types.GenerateContentConfig(
            temperature=0,
            max_output_tokens=2048,
        ),
    )

    raw = response.text if response.text else "{}"
    return _parse_llm_response(raw, backend="gemini")


# ── Groq backend ──────────────────────────────────────────────────────────────


def _groq_schema(images_b64: list[str], api_key: str | None) -> DocumentSchema:
    """Extract schema via Groq API (free tier, LLaMA vision)."""
    try:
        from groq import Groq  # type: ignore[import-untyped]
    except ImportError as exc:
        raise RuntimeError(
            "groq package not installed. Run: uv add groq"
        ) from exc

    key = api_key or os.environ.get("GROQ_API_KEY")
    if not key:
        raise RuntimeError(
            "No Groq API key found. Provide one in the UI or set GROQ_API_KEY env var. "
            "Get a free key at https://console.groq.com"
        )

    client = Groq(api_key=key)

    content: list[dict] = [{"type": "text", "text": _USER_PROMPT}]
    for b64 in images_b64:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{b64}"},
        })

    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ],
        max_tokens=2048,
        temperature=0,
    )

    raw = response.choices[0].message.content or "{}"
    return _parse_llm_response(raw, backend="groq")


# ── OpenAI backend ────────────────────────────────────────────────────────────


def _openai_schema(images_b64: list[str], api_key: str | None) -> DocumentSchema:
    try:
        from openai import OpenAI  # type: ignore[import-untyped]
    except ImportError as exc:
        raise RuntimeError("openai package not installed. Run: uv add openai") from exc

    key = api_key or os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError(
            "No OpenAI API key found. Provide one in the UI or set OPENAI_API_KEY env var."
        )

    client = OpenAI(api_key=key)

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


def _anthropic_schema(images_b64: list[str], api_key: str | None) -> DocumentSchema:
    try:
        import anthropic as anthropic_sdk  # type: ignore[import-untyped]
    except ImportError as exc:
        raise RuntimeError(
            "anthropic package not installed. Run: uv add anthropic"
        ) from exc

    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError(
            "No Anthropic API key found. Provide one in the UI or set ANTHROPIC_API_KEY env var."
        )

    client = anthropic_sdk.Anthropic(api_key=key)

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


# ── Vertex AI backend ─────────────────────────────────────────────────────────


def _vertex_schema(
    images_b64: list[str],
    api_key: str | None,
    service_account_json: str | None,
) -> DocumentSchema:
    """Extract schema via Vertex AI (Gemini on GCP)."""
    try:
        import vertexai  # type: ignore[import-untyped]
        from vertexai.generative_models import GenerativeModel, Image as VImage  # type: ignore[import-untyped]
    except ImportError:
        try:
            import google.cloud.aiplatform as aiplatform  # type: ignore[import-untyped]
            from google.cloud.aiplatform import GenerativeModel  # type: ignore[import-untyped]
        except ImportError as exc:
            raise RuntimeError(
                "Vertex AI package not installed. Run: uv add google-cloud-aiplatform"
            ) from exc

    sa_json = service_account_json or os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if sa_json:
        # Write to a temp file and set credentials env var
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        tmp.write(sa_json)
        tmp.flush()
        tmp.close()
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = tmp.name
        logger.debug("Vertex AI: using service account credentials from provided JSON")
    else:
        logger.debug("Vertex AI: using application default credentials")

    project = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCLOUD_PROJECT")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

    try:
        vertexai.init(project=project, location=location)  # type: ignore[name-defined]
        model = GenerativeModel(  # type: ignore[name-defined]
            model_name="gemini-2.0-flash",
            system_instruction=_SYSTEM_PROMPT,
        )
        parts: list = [_USER_PROMPT]
        for b64 in images_b64:
            parts.append({"mime_type": "image/png", "data": b64})
        response = model.generate_content(parts)
        raw = response.text if response.text else "{}"
    except NameError:
        # vertexai not available, fall back to google.cloud.aiplatform path
        raise RuntimeError(
            "Could not initialise Vertex AI. Ensure google-cloud-aiplatform is installed: "
            "uv add google-cloud-aiplatform"
        )

    return _parse_llm_response(raw, backend="vertex_ai")


# ── Response parser ───────────────────────────────────────────────────────────


def _parse_llm_response(raw: str, backend: str) -> DocumentSchema:
    """Parse a raw LLM JSON response into a DocumentSchema."""
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        logger.warning(f"LLM returned invalid JSON: {exc}. Raw: {text[:200]}")
        data = {}

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
    """Extract a DocumentSchema from one or more document scan images.

    Args:
        backend: LLM provider to use. Default is ``"mock"`` (no API key needed).
            Free options with an API key: ``"gemini"`` and ``"groq"``.
        api_key: Optional API key for the chosen provider. Falls back to the
            corresponding environment variable if not supplied.
        service_account_json: Raw JSON string of a GCP service account key,
            used only by the ``vertex_ai`` backend. Falls back to
            ``GOOGLE_APPLICATION_CREDENTIALS`` / ``GOOGLE_SERVICE_ACCOUNT_JSON``
            env vars if not supplied.
    """

    def __init__(
        self,
        backend: Backend = "mock",
        api_key: str | None = None,
        service_account_json: str | None = None,
    ) -> None:
        self.backend: Backend = backend
        self.api_key = api_key or None  # normalise empty string → None
        self.service_account_json = service_account_json or None

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

        if self.backend == "gemini":
            return _gemini_schema(images_b64, self.api_key)
        if self.backend == "groq":
            return _groq_schema(images_b64, self.api_key)
        if self.backend == "openai":
            return _openai_schema(images_b64, self.api_key)
        if self.backend == "anthropic":
            return _anthropic_schema(images_b64, self.api_key)
        if self.backend == "vertex_ai":
            return _vertex_schema(images_b64, self.api_key, self.service_account_json)

        raise ValueError(f"Unknown backend: {self.backend!r}")
