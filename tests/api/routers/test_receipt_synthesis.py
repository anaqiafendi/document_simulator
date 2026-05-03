"""Integration tests for the /api/receipt-synthesis router (FDD #28 AC-4 .. AC-6).

Uses Starlette's TestClient via the ``client`` fixture defined in
``tests/api/conftest.py``. Each test exercises one endpoint and one assertion
focus so failures are easy to diagnose.
"""

from __future__ import annotations


def test_render_endpoint_returns_all_stages(client) -> None:
    """AC-4: POST /render with augraphy_preset returns 3 stages (content, raster, augraphy)."""
    body = {
        "template": "thermal_minimal",
        "seed": 42,
        "augraphy_preset": "light",
    }
    r = client.post("/api/receipt-synthesis/render", json=body)
    assert r.status_code == 200, f"Unexpected status {r.status_code}: {r.text}"

    payload = r.json()
    assert "image_id" in payload, "response missing image_id"
    assert (
        "final_image_b64" in payload and payload["final_image_b64"]
    ), "final_image_b64 must be a non-empty base64 string"
    assert "ground_truth" in payload, "response missing ground_truth"
    assert "pipeline_version" in payload, "response missing pipeline_version"

    stages = payload["stages"]
    assert (
        isinstance(stages, list) and len(stages) == 3
    ), f"expected 3 stages with augraphy preset, got {len(stages)}"
    stage_names = [s["stage"] for s in stages]
    assert stage_names == [
        "content",
        "raster",
        "augraphy",
    ], f"unexpected stage order: {stage_names}"

    # Content stage has no image; raster + augraphy do.
    by_name = {s["stage"]: s for s in stages}
    assert by_name["content"]["image_b64"] is None, "content stage must have null image"
    assert by_name["raster"]["image_b64"], "raster stage must include base64 image"
    assert by_name["augraphy"]["image_b64"], "augraphy stage must include base64 image"

    # elapsed_ms is recorded per stage.
    for s in stages:
        assert (
            isinstance(s["elapsed_ms"], int) and s["elapsed_ms"] >= 0
        ), f"stage {s['stage']}: invalid elapsed_ms {s['elapsed_ms']!r}"

    # Ground truth carries the schema we expect.
    gt = payload["ground_truth"]
    assert (
        "tokens" in gt and len(gt["tokens"]) >= 8
    ), f"ground_truth tokens too few: {len(gt.get('tokens', []))}"


def test_render_endpoint_no_augraphy_when_preset_null(client) -> None:
    """AC-4: when ``augraphy_preset`` is omitted, only content + raster stages run."""
    body = {"template": "thermal_minimal", "seed": 42}
    r = client.post("/api/receipt-synthesis/render", json=body)
    assert r.status_code == 200, r.text

    stages = r.json()["stages"]
    stage_names = [s["stage"] for s in stages]
    assert stage_names == [
        "content",
        "raster",
    ], f"expected just [content, raster], got {stage_names}"


def test_templates_endpoint_returns_5(client) -> None:
    """AC-5: GET /templates returns metadata for the 5 v0.2 templates."""
    r = client.get("/api/receipt-synthesis/templates")
    assert r.status_code == 200, r.text

    payload = r.json()
    assert "templates" in payload, "response missing templates"
    assert len(payload["templates"]) == 5, f"expected 5 templates, got {len(payload['templates'])}"

    ids = {t["id"] for t in payload["templates"]}
    expected = {
        "thermal_minimal",
        "restaurant_tip",
        "retail_multicol",
        "a4_invoice",
        "taxi_stub",
    }
    assert ids == expected, f"template ids mismatch: got {ids}, expected {expected}"

    # Every template entry has the spec'd fields.
    for t in payload["templates"]:
        for field in ("id", "name", "description", "sample_token_count"):
            assert field in t, f"template {t.get('id')} missing field {field!r}"
        assert isinstance(t["sample_token_count"], int) and t["sample_token_count"] > 0


def test_augraphy_presets_endpoint_returns_known_presets(client) -> None:
    """AC-6: GET /augraphy-presets returns the existing preset names."""
    r = client.get("/api/receipt-synthesis/augraphy-presets")
    assert r.status_code == 200, r.text

    presets = r.json()["presets"]
    assert isinstance(presets, list) and presets, "presets must be a non-empty list"
    assert "medium" in presets, f"medium preset missing from {presets}"
    assert "light" in presets, f"light preset missing from {presets}"
    assert "heavy" in presets, f"heavy preset missing from {presets}"


def test_render_endpoint_invalid_template_returns_400(client) -> None:
    """AC-4: an unknown template name must return a client error (4xx)."""
    body = {"template": "NOT_A_REAL_TEMPLATE", "seed": 1}
    r = client.post("/api/receipt-synthesis/render", json=body)
    assert (
        400 <= r.status_code < 500
    ), f"unknown template should return 4xx, got {r.status_code}: {r.text}"
