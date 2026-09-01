"""Tests for RSC row parsing, reference resolution, and logo acquisition."""

from __future__ import annotations

import base64
import json
from pathlib import Path

from document_simulator.data.receiptfaker.logos import (
    _extension_for,
    collect_logo_refs,
    decode_data_uri,
)
from document_simulator.data.receiptfaker.scrape import (
    extract_template_json,
    parse_flight_rows,
    resolve_refs,
)

PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


# --------------------------------------------------------------------------- #
# Flight row parsing
# --------------------------------------------------------------------------- #
def test_parse_flight_rows_reads_line_delimited_rows() -> None:
    rows = parse_flight_rows('1:["a"]\n2:{"b":1}\n')

    assert rows["1"] == '["a"]'
    assert rows["2"] == '{"b":1}'


def test_text_row_is_length_delimited_not_newline_delimited() -> None:
    """A T-row's declared length ends it -- trailing stream must not leak in."""
    text = "data:image/png;base64,AAAA"
    flight = f"3e:T{len(text.encode()):x},{text}3f:[\"tail\"]\n"

    rows = parse_flight_rows(flight)

    assert rows["3e"] == text
    assert rows["3f"] == '["tail"]'


def test_text_row_length_counts_utf8_bytes() -> None:
    text = "café"  # 5 UTF-8 bytes, 4 characters
    rows = parse_flight_rows(f"a:T{len(text.encode()):x},{text}\n")

    assert rows["a"] == text


# --------------------------------------------------------------------------- #
# Reference resolution
# --------------------------------------------------------------------------- #
def test_resolve_refs_substitutes_hex_references() -> None:
    rows = {"3e": "data:image/png;base64,AAAA"}
    resolved = resolve_refs({"logo": "$3e", "keep": "$undefined"}, rows)

    assert resolved["logo"] == "data:image/png;base64,AAAA"
    assert resolved["keep"] == "$undefined"  # not a hex ref, left alone


def test_resolve_refs_walks_nested_structures() -> None:
    rows = {"7": "resolved"}
    resolved = resolve_refs({"sections": [{"logo": "$7"}, {"logo": "$ff"}]}, rows)

    assert resolved["sections"][0]["logo"] == "resolved"
    assert resolved["sections"][1]["logo"] == "$ff"  # unknown row left as-is


def test_extract_resolves_inline_logo_reference() -> None:
    """End to end: a template referencing a hoisted data URI comes back inlined."""
    data_uri = "data:image/png;base64," + base64.b64encode(PNG_BYTES).decode()
    template = {
        "id": "x",
        "slug": "Demo",
        "name": "Demo",
        "published": True,
        "sections": [{"id": "s1", "type": "HEADER", "logo": "$3e"}],
    }
    flight = f"3e:T{len(data_uri.encode()):x},{data_uri}\n3f:{json.dumps(template)}\n"
    html = f"<script>self.__next_f.push([1,{json.dumps(flight)}])</script>"

    extracted = extract_template_json(html)

    assert extracted is not None
    assert extracted["sections"][0]["logo"] == data_uri


# --------------------------------------------------------------------------- #
# Logo acquisition
# --------------------------------------------------------------------------- #
def test_decode_data_uri_returns_bytes_and_extension() -> None:
    uri = "data:image/png;base64," + base64.b64encode(PNG_BYTES).decode()
    decoded = decode_data_uri(uri)

    assert decoded is not None
    content, extension = decoded
    assert content == PNG_BYTES
    assert extension == ".png"


def test_decode_data_uri_rejects_plain_urls() -> None:
    assert decode_data_uri("https://example.test/logo.png") is None


def test_extension_falls_back_to_magic_bytes() -> None:
    assert _extension_for(PNG_BYTES, None) == ".png"
    assert _extension_for(b"\xff\xd8\xff\xe0rest", "application/octet-stream") == ".jpg"
    assert _extension_for(b"not an image", None) == ".bin"


def test_collect_logo_refs_reads_every_section(tmp_path: Path) -> None:
    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / "Demo.json").write_text(
        json.dumps(
            {
                "slug": "Demo",
                "sections": [
                    {"type": "HEADER", "logo": "https://example.test/a.png"},
                    {"type": "CUSTOM"},
                    {"type": "CUSTOM", "logo": ""},
                    {"type": "HEADER", "logo": "https://example.test/b.png"},
                ],
            }
        )
    )

    refs = collect_logo_refs(tmp_path)

    assert [(r.slug, r.section_index) for r in refs] == [("Demo", 0), ("Demo", 3)]
