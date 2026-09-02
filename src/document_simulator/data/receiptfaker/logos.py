"""Download the logo assets referenced by scraped templates.

Templates reference their logo either as a remote Firebase Storage URL or as an
inline ``data:image/...;base64,`` URI. Both are materialised to disk here and
deduplicated by content hash, since the same brand logo is reused across many
templates.

Usage::

    python -m document_simulator.data.receiptfaker.logos --data data/receiptfaker
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import binascii
import hashlib
import json
import re
from pathlib import Path
from typing import Any, NamedTuple

import httpx
from loguru import logger

from document_simulator.config import DEFAULT_LOGO_CACHE
from document_simulator.data.receiptfaker.scrape import USER_AGENT

_DATA_URI_RE = re.compile(r"^data:(?P<mime>image/[\w.+-]+);base64,(?P<payload>.+)$", re.DOTALL)

_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/svg+xml": ".svg",
}

# Magic-number sniffing, used when the server sends no usable content type.
_MAGIC: list[tuple[bytes, str]] = [
    (b"\xff\xd8\xff", ".jpg"),
    (b"\x89PNG\r\n\x1a\n", ".png"),
    (b"GIF8", ".gif"),
    (b"RIFF", ".webp"),
    (b"<svg", ".svg"),
    (b"<?xml", ".svg"),
]


class LogoRef(NamedTuple):
    """One template's reference to a logo asset."""

    slug: str
    section_index: int
    source: str


def collect_logo_refs(data_dir: Path) -> list[LogoRef]:
    """Every logo reference across the scraped catalogue, in slug order."""
    refs: list[LogoRef] = []
    for path in sorted((data_dir / "templates").glob("*.json")):
        payload: dict[str, Any] = json.loads(path.read_text())
        slug = payload.get("slug", path.stem)
        for index, section in enumerate(payload.get("sections") or []):
            source = (section or {}).get("logo") or ""
            if source:
                refs.append(LogoRef(slug=slug, section_index=index, source=source))
    return refs


def _extension_for(content: bytes, mime: str | None) -> str:
    """Best-effort file extension from the declared mime type, else magic bytes."""
    if mime:
        normalised = mime.split(";")[0].strip().lower()
        if normalised in _EXTENSIONS:
            return _EXTENSIONS[normalised]
    for prefix, extension in _MAGIC:
        if content.startswith(prefix):
            return extension
    return ".bin"


def decode_data_uri(source: str) -> tuple[bytes, str] | None:
    """Decode an inline ``data:image/...;base64,`` URI to bytes and extension."""
    match = _DATA_URI_RE.match(source)
    if not match:
        return None
    try:
        content = base64.b64decode(match.group("payload"), validate=False)
    except (binascii.Error, ValueError):
        return None
    if not content:
        return None
    return content, _extension_for(content, match.group("mime"))


async def _fetch_remote(
    client: httpx.AsyncClient, url: str, semaphore: asyncio.Semaphore, retries: int = 3
) -> tuple[bytes, str] | None:
    """Download a remote logo, retrying on transient failures."""
    async with semaphore:
        for attempt in range(1, retries + 1):
            try:
                response = await client.get(url)
                response.raise_for_status()
                content = response.content
                if not content:
                    return None
                return content, _extension_for(content, response.headers.get("content-type"))
            except httpx.HTTPError as exc:
                if attempt == retries:
                    logger.error(f"Failed logo {url[:80]}: {exc}")
                    return None
                await asyncio.sleep(2.0 * attempt)
        return None


async def download_logos(
    data_dir: Path,
    concurrency: int = 6,
    delay: float = 0.1,
    logos_dir: Path | None = None,
) -> dict[str, Any]:
    """Materialise every referenced logo into ``data_dir/logos``.

    Assets are stored as ``<sha256[:16]><ext>`` so identical images shared across
    templates are written once. Returns the manifest that maps templates to files.
    """
    # Default outside the repo: worktrees are disposable and these are not in
    # git, so writing under the checkout means re-downloading on every branch.
    logos_dir = logos_dir or DEFAULT_LOGO_CACHE
    logos_dir.mkdir(parents=True, exist_ok=True)

    refs = collect_logo_refs(data_dir)
    unique_sources = list(dict.fromkeys(ref.source for ref in refs))
    logger.info(f"{len(refs)} logo references, {len(unique_sources)} distinct sources")

    resolved: dict[str, str | None] = {}
    semaphore = asyncio.Semaphore(concurrency)

    def store(content: bytes, extension: str) -> str:
        digest = hashlib.sha256(content).hexdigest()[:16]
        filename = f"{digest}{extension}"
        target = logos_dir / filename
        if not target.exists():
            target.write_bytes(content)
        return filename

    inline_sources = [s for s in unique_sources if s.startswith("data:")]
    remote_sources = [s for s in unique_sources if not s.startswith("data:")]

    for source in inline_sources:
        decoded = decode_data_uri(source)
        resolved[source] = store(*decoded) if decoded else None

    headers = {"User-Agent": USER_AGENT}
    async with httpx.AsyncClient(
        headers=headers, timeout=90.0, follow_redirects=True
    ) as client:

        async def worker(source: str) -> None:
            fetched = await _fetch_remote(client, source, semaphore)
            resolved[source] = store(*fetched) if fetched else None
            await asyncio.sleep(delay)

        await asyncio.gather(*(worker(source) for source in remote_sources))

    failures = sorted(source for source, name in resolved.items() if name is None)
    manifest: dict[str, Any] = {
        "reference_count": len(refs),
        "distinct_sources": len(unique_sources),
        "distinct_files": len({name for name in resolved.values() if name}),
        "failed_sources": failures,
        "templates": {},
    }
    for ref in refs:
        filename = resolved.get(ref.source)
        if filename:
            manifest["templates"].setdefault(ref.slug, []).append(
                {"section_index": ref.section_index, "file": filename}
            )

    manifest_path = data_dir / "logos_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    logger.info(
        f"Stored {manifest['distinct_files']} distinct logo files "
        f"({len(failures)} failed) -> {logos_dir}"
    )
    return manifest


def main() -> None:
    """CLI entry point for logo acquisition."""
    parser = argparse.ArgumentParser(description="Download ReceiptFaker logo assets")
    parser.add_argument("--data", type=Path, default=Path("data/receiptfaker"))
    parser.add_argument("--concurrency", type=int, default=6)
    parser.add_argument("--delay", type=float, default=0.1)
    parser.add_argument(
        "--logos-dir",
        type=Path,
        default=None,
        help=f"Where to store images. Defaults to the shared cache: {DEFAULT_LOGO_CACHE}",
    )
    args = parser.parse_args()

    asyncio.run(download_logos(args.data, args.concurrency, args.delay, args.logos_dir))


if __name__ == "__main__":
    main()
