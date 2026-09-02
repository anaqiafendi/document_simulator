"""Acquire the ReceiptFaker template catalogue.

Each ``/generate/<slug>`` page server-renders its template as JSON inside the
Next.js RSC flight stream (``self.__next_f.push([1, "<chunk>"])``). Reassembling
those chunks and brace-matching around the template object yields the exact
structured template definition -- no headless browser or OCR required.

Usage::

    python -m document_simulator.data.receiptfaker.scrape --out data/receiptfaker
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

import httpx
from loguru import logger

BASE_URL = "https://www.receiptfaker.com"
SITEMAP_URL = f"{BASE_URL}/sitemap.xml"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

_FLIGHT_RE = re.compile(r'self\.__next_f\.push\(\[1,\s*("(?:[^"\\]|\\.)*")\s*\]\)')
_ANCHOR_RE = re.compile(r'"published"\s*:\s*true')
_ROW_HEADER_RE = re.compile(r"([0-9a-f]+):")
_REF_RE = re.compile(r"^\$([0-9a-f]+)$")


# --------------------------------------------------------------------------- #
# Flight-payload extraction
# --------------------------------------------------------------------------- #
def reassemble_flight(html: str) -> str:
    """Concatenate the RSC flight chunks embedded in a Next.js page."""
    parts: list[str] = []
    for match in _FLIGHT_RE.finditer(html):
        try:
            parts.append(json.loads(match.group(1)))
        except json.JSONDecodeError:
            continue
    return "".join(parts)


def parse_flight_rows(flight: str) -> dict[str, str]:
    """Index the flight stream's numbered rows by id.

    Rows are ``<hex-id>:<payload>``. A payload starting with ``T`` is a *text*
    row of the form ``T<hex-byte-length>,<text>`` and is delimited by that
    length, not by a newline -- base64 logo data URIs are stored this way and
    would otherwise run on into the rest of the stream. Every other payload
    runs to the end of the line.
    """
    rows: dict[str, str] = {}
    position = 0
    length = len(flight)

    while position < length:
        header = _ROW_HEADER_RE.match(flight, position)
        if header is None:
            newline = flight.find("\n", position)
            if newline == -1:
                break
            position = newline + 1
            continue

        row_id = header.group(1)
        cursor = header.end()

        if flight.startswith("T", cursor):
            comma = flight.find(",", cursor)
            if comma != -1:
                try:
                    byte_length = int(flight[cursor + 1 : comma], 16)
                except ValueError:
                    byte_length = -1
                if byte_length >= 0:
                    start = comma + 1
                    # The declared length counts UTF-8 bytes, not characters.
                    text = flight[start:].encode("utf-8")[:byte_length].decode(
                        "utf-8", errors="ignore"
                    )
                    rows[row_id] = text
                    position = start + len(text)
                    if flight.startswith("\n", position):
                        position += 1
                    continue

        newline = flight.find("\n", cursor)
        if newline == -1:
            rows[row_id] = flight[cursor:]
            break
        rows[row_id] = flight[cursor:newline]
        position = newline + 1

    return rows


def resolve_refs(value: Any, rows: dict[str, str]) -> Any:
    """Replace ``"$<hex>"`` back-references with their row payload.

    Row ids are assigned per render, so this must run against the same response
    the template was extracted from -- a reference cannot be resolved later.
    """
    if isinstance(value, str):
        match = _REF_RE.match(value)
        if match and match.group(1) in rows:
            return rows[match.group(1)]
        return value
    if isinstance(value, list):
        return [resolve_refs(item, rows) for item in value]
    if isinstance(value, dict):
        return {key: resolve_refs(item, rows) for key, item in value.items()}
    return value


def _balanced_end(text: str, start: int) -> int:
    """Index just past the JSON value starting at ``start``, or -1."""
    depth = 0
    in_string = False
    index = start
    while index < len(text):
        char = text[index]
        if in_string:
            if char == "\\":
                index += 2
                continue
            if char == '"':
                in_string = False
        elif char == '"':
            in_string = True
        elif char in "{[":
            depth += 1
        elif char in "}]":
            depth -= 1
            if depth == 0:
                return index + 1
        index += 1
    return -1


def extract_template_json(html: str) -> dict[str, Any] | None:
    """Pull the template object out of a ``/generate/<slug>`` page."""
    flight = reassemble_flight(html)
    matches = list(_ANCHOR_RE.finditer(flight))
    if not matches:
        return None
    anchor = matches[-1].start()
    # Walk backwards over candidate object starts until one parses and
    # encloses the anchor -- robust against nested objects in the payload.
    for index in range(anchor, -1, -1):
        if flight[index] != "{":
            continue
        end = _balanced_end(flight, index)
        if end <= anchor:
            continue
        try:
            candidate = json.loads(flight[index:end])
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict) and "published" in candidate and "sections" in candidate:
            resolved: dict[str, Any] = resolve_refs(candidate, parse_flight_rows(flight))
            return resolved
    return None


# --------------------------------------------------------------------------- #
# Catalogue discovery + fetching
# --------------------------------------------------------------------------- #
async def discover_slugs(client: httpx.AsyncClient) -> list[str]:
    """Enumerate every template slug from the site's sitemap index."""
    slugs: set[str] = set()
    queue = [SITEMAP_URL]
    seen: set[str] = set()

    while queue:
        url = queue.pop()
        if url in seen:
            continue
        seen.add(url)
        response = await client.get(url)
        response.raise_for_status()
        root = ElementTree.fromstring(response.text)
        for loc in root.iter("{http://www.sitemaps.org/schemas/sitemap/0.9}loc"):
            href = (loc.text or "").strip()
            if href.endswith(".xml"):
                queue.append(href)
            elif href.startswith(f"{BASE_URL}/generate/"):
                # default (English) locale only -- skips /<lang>/generate/ duplicates
                slugs.add(href[len(f"{BASE_URL}/generate/") :])

    logger.info(f"Discovered {len(slugs)} template slugs")
    return sorted(slugs)


def build_filenames(slugs: list[str]) -> dict[str, str]:
    """Map each slug to a collision-free filename stem.

    Some slugs differ only by case (``Hotel-Receipt`` vs ``Hotel-receipt``).
    On case-insensitive filesystems (macOS APFS, Windows) those would silently
    overwrite one another, so every member of a colliding group gets a short
    content-free hash suffix.
    """
    groups: dict[str, list[str]] = {}
    for slug in slugs:
        groups.setdefault(slug.casefold(), []).append(slug)

    filenames: dict[str, str] = {}
    for members in groups.values():
        if len(members) == 1:
            filenames[members[0]] = members[0]
            continue
        for slug in members:
            digest = hashlib.sha1(slug.encode()).hexdigest()[:8]
            filenames[slug] = f"{slug}__{digest}"
    return filenames


async def fetch_template(
    client: httpx.AsyncClient,
    slug: str,
    semaphore: asyncio.Semaphore,
    retries: int = 3,
) -> dict[str, Any] | None:
    """Fetch and extract a single template, retrying on transient failures."""
    url = f"{BASE_URL}/generate/{slug}"
    async with semaphore:
        for attempt in range(1, retries + 1):
            try:
                response = await client.get(url)
                response.raise_for_status()
                payload = extract_template_json(response.text)
                if payload is None:
                    logger.warning(f"No template payload in {slug}")
                    return None
                payload.setdefault("slug", slug)
                return payload
            except (httpx.HTTPError, httpx.StreamError) as exc:
                if attempt == retries:
                    logger.error(f"Failed {slug} after {retries} attempts: {exc}")
                    return None
                await asyncio.sleep(2.0 * attempt)
        return None


async def scrape_catalogue(
    out_dir: Path,
    concurrency: int = 4,
    delay: float = 0.25,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Scrape every published template into ``out_dir/templates/<slug>.json``."""
    templates_dir = out_dir / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)

    headers = {"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"}
    semaphore = asyncio.Semaphore(concurrency)

    async with httpx.AsyncClient(
        headers=headers, timeout=60.0, follow_redirects=True, http2=False
    ) as client:
        slugs = await discover_slugs(client)
        if limit is not None:
            slugs = slugs[:limit]
        filenames = build_filenames(slugs)

        async def worker(slug: str) -> dict[str, Any] | None:
            target = templates_dir / f"{filenames[slug]}.json"
            if target.exists():  # resumable
                cached: dict[str, Any] = json.loads(target.read_text())
                return cached
            payload = await fetch_template(client, slug, semaphore)
            if payload is not None:
                target.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
            await asyncio.sleep(delay)  # be polite to the origin
            return payload

        results = await asyncio.gather(*(worker(slug) for slug in slugs))

    templates = [item for item in results if item is not None]
    logger.info(f"Scraped {len(templates)}/{len(slugs)} templates into {templates_dir}")
    return templates


def main() -> None:
    """CLI entry point for catalogue acquisition."""
    parser = argparse.ArgumentParser(description="Scrape the ReceiptFaker template catalogue")
    parser.add_argument("--out", type=Path, default=Path("data/receiptfaker"))
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--delay", type=float, default=0.25)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    asyncio.run(scrape_catalogue(args.out, args.concurrency, args.delay, args.limit))


if __name__ == "__main__":
    main()
