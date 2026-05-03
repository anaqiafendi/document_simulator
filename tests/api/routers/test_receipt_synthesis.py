"""Integration tests for the /api/receipt-synthesis router (FDD #28 AC-4 .. AC-6
plus FDD #29 v0.3d AC-render-3d / AC-5d).

Uses Starlette's TestClient via the ``client`` fixture defined in
``tests/api/conftest.py``. Each test exercises one endpoint and one assertion
focus so failures are easy to diagnose.

Tests that hit the bpy sidecar (``test_render_endpoint_with_render_3d_*``) are
marked ``slow`` because the cold-start sidecar spawn is 30–60s and a tiny 3D
render still takes a few seconds inside the worker. Run with
``pytest -m "not slow"`` to skip; run the full suite to exercise them.
"""

from __future__ import annotations

import pytest


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


# ---------------------------------------------------------------------------
# FDD #29 v0.3d — 3D render path + HDRI thumbnails endpoint
# ---------------------------------------------------------------------------


def test_render_endpoint_render_3d_false_unchanged_behavior(client) -> None:
    """AC-render-3d: when ``render_3d`` is omitted (or False) the v0.2 stage
    list is preserved verbatim — no ``3d_render`` stage appended, no behavior
    change for existing callers.
    """
    body = {"template": "thermal_minimal", "seed": 42, "augraphy_preset": "light"}
    r = client.post("/api/receipt-synthesis/render", json=body)
    assert r.status_code == 200, r.text

    payload = r.json()
    stage_names = [s["stage"] for s in payload["stages"]]
    assert (
        "3d_render" not in stage_names
    ), f"render_3d omitted should not produce a 3d_render stage; got {stage_names}"
    assert stage_names == [
        "content",
        "raster",
        "augraphy",
    ], f"v0.2 stage order must be unchanged; got {stage_names}"

    # Explicit render_3d=False must behave identically.
    body_explicit = {**body, "render_3d": False}
    r2 = client.post("/api/receipt-synthesis/render", json=body_explicit)
    assert r2.status_code == 200, r2.text
    stage_names_2 = [s["stage"] for s in r2.json()["stages"]]
    assert (
        stage_names_2 == stage_names
    ), f"render_3d=False should match omitted: got {stage_names_2} vs {stage_names}"


def test_hdri_thumbnails_endpoint_returns_three(client) -> None:
    """AC-5d (backend): GET /hdri-thumbnails returns the 3 bundled HDRIs with
    base64-encoded thumbnail PNGs. Each entry has id + name + thumbnail_b64.
    """
    r = client.get("/api/receipt-synthesis/hdri-thumbnails")
    assert r.status_code == 200, r.text

    payload = r.json()
    assert "hdris" in payload, f"response missing 'hdris': {payload}"
    hdris = payload["hdris"]
    assert (
        isinstance(hdris, list) and len(hdris) == 3
    ), f"expected 3 HDRIs (kitchen_bright/office_warm/outdoor_overcast), got {len(hdris)}"

    ids = {h["id"] for h in hdris}
    expected_ids = {"kitchen_bright", "office_warm", "outdoor_overcast"}
    assert ids == expected_ids, f"hdri ids mismatch: got {ids}, expected {expected_ids}"

    for h in hdris:
        for field in ("id", "name", "thumbnail_b64"):
            assert field in h, f"hdri {h.get('id')} missing field {field!r}"
        assert (
            isinstance(h["thumbnail_b64"], str) and h["thumbnail_b64"]
        ), f"hdri {h['id']} thumbnail_b64 must be a non-empty base64 string"
        # Cheap sanity check that it's actually base64-decodable PNG bytes.
        import base64

        raw = base64.b64decode(h["thumbnail_b64"])
        assert (
            raw[:8] == b"\x89PNG\r\n\x1a\n"
        ), f"hdri {h['id']} thumbnail_b64 does not decode to a PNG"


def test_render_endpoint_invalid_hdri_id_returns_400_when_3d_true(client) -> None:
    """AC-render-3d: when ``render_3d=True`` and ``hdri_id`` is unknown, the
    endpoint must reject with a 4xx before spawning the bpy sidecar (cheap
    validation up front).
    """
    body = {
        "template": "thermal_minimal",
        "seed": 1,
        "render_3d": True,
        "hdri_id": "NOT_A_REAL_HDRI",
    }
    r = client.post("/api/receipt-synthesis/render", json=body)
    assert (
        400 <= r.status_code < 500
    ), f"unknown hdri_id with render_3d=True should return 4xx, got {r.status_code}: {r.text}"


@pytest.mark.slow
def test_render_endpoint_with_render_3d_true_returns_3d_stage(client) -> None:
    """AC-render-3d (slow): POST with ``render_3d=True`` runs the full
    content -> raster -> augraphy -> 3d_render chain and returns a stage with
    ``stage="3d_render"``.

    Skipped unless bpy is installed in the test interpreter (Python 3.11). The
    ``slow`` marker keeps this out of the default fast-test pass — bpy
    sidecar cold start is 30–60s and the render itself adds a few seconds.
    """
    pytest.importorskip("bpy")

    body = {
        "template": "thermal_minimal",
        "seed": 42,
        "render_3d": True,
        "hdri_id": "office_warm",
        "curl_strength": 0.05,
    }
    r = client.post("/api/receipt-synthesis/render", json=body)
    assert r.status_code == 200, f"3D render returned {r.status_code}: {r.text}"

    payload = r.json()
    stage_names = [s["stage"] for s in payload["stages"]]
    assert (
        "3d_render" in stage_names
    ), f"render_3d=True must produce a 3d_render stage; got {stage_names}"
    # The 3d_render stage must come AFTER raster (and after augraphy when
    # an augraphy_preset isn't supplied, augraphy is skipped — that's fine).
    assert stage_names.index("3d_render") > stage_names.index("raster")

    by_name = {s["stage"]: s for s in payload["stages"]}
    three_d = by_name["3d_render"]
    assert three_d["image_b64"], "3d_render stage must include base64 image"
    params = three_d["parameters"]
    assert (
        params.get("hdri_id") == "office_warm"
    ), f"3d_render parameters must echo back hdri_id; got {params}"
    assert (
        params.get("curl_strength") == 0.05
    ), f"3d_render parameters must echo back curl_strength; got {params}"

    # final_image_b64 must be the 3D render (not the raster).
    assert (
        payload["final_image_b64"] == three_d["image_b64"]
    ), "final_image_b64 should be the 3D render output when render_3d=True"

    # GT tokens should now carry the full coord trail through to final_crop.
    gt = payload["ground_truth"]
    assert gt["tokens"], "ground truth must have tokens"
    # At least one token should have a final_crop snapshot (some may be
    # off-frame and end at camera_2d — that's allowed by v0.3c design).
    visible_with_crop = [
        t for t in gt["tokens"] if any(c["stage"] == "final_crop" for c in t["coords"])
    ]
    assert (
        visible_with_crop
    ), "no tokens carry a final_crop coord snapshot — projector chain didn't run"
