"""API tests for the schema-extraction endpoints added in PR #27 follow-up."""

from __future__ import annotations


class TestExtractSchemaEndpoint:
    def test_mock_backend_per_image(self, client, tiny_png_bytes):
        r = client.post(
            "/api/synthesis/extract-schema",
            files=[
                ("files", ("a.png", tiny_png_bytes, "image/png")),
                ("files", ("b.png", tiny_png_bytes, "image/png")),
            ],
            data={"backend": "mock"},
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert "schemas" in body and "source_images" in body
        assert len(body["schemas"]) == 2
        assert len(body["source_images"]) == 2
        # Each schema has its own source_image_index
        assert {s["source_image_index"] for s in body["schemas"]} == {0, 1}

    def test_schemas_include_line_items_and_bboxes(self, client, tiny_png_bytes):
        r = client.post(
            "/api/synthesis/extract-schema",
            files=[("files", ("rcp.png", tiny_png_bytes, "image/png"))],
            data={"backend": "mock"},
        )
        assert r.status_code == 200
        body = r.json()
        schema = body["schemas"][0]
        assert len(schema["line_items"]) > 0
        assert any(f.get("bbox") for f in schema["fields"])
        assert schema["language"] == "en"
        assert schema["currency"] == "USD"

    def test_no_files_returns_422(self, client):
        r = client.post("/api/synthesis/extract-schema", data={"backend": "mock"})
        assert r.status_code == 422

    def test_document_type_hint_applied(self, client, tiny_png_bytes):
        r = client.post(
            "/api/synthesis/extract-schema",
            files=[("files", ("a.png", tiny_png_bytes, "image/png"))],
            data={"backend": "mock", "document_type_hint": "invoice"},
        )
        assert r.status_code == 200
        assert r.json()["schemas"][0]["document_type"] == "invoice"


class TestFakerProvidersEndpoint:
    def test_returns_categorised_providers(self, client):
        r = client.get("/api/synthesis/faker-providers")
        assert r.status_code == 200
        body = r.json()
        assert "categories" in body and "currencies" in body
        for required in ["identity", "custom", "person", "finance"]:
            assert required in body["categories"]

    def test_custom_category_contains_pricetag(self, client):
        r = client.get("/api/synthesis/faker-providers")
        names = [p["name"] for p in r.json()["categories"]["custom"]]
        assert "pricetag" in names
        assert "price_short" in names

    def test_currencies_include_major_codes(self, client):
        r = client.get("/api/synthesis/faker-providers")
        codes = {c["code"] for c in r.json()["currencies"]}
        for required in ["USD", "EUR", "GBP", "JPY", "CAD"]:
            assert required in codes
