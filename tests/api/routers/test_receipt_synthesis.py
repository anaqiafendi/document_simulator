"""Integration tests for the /api/receipt-synthesis router.

Covers FDD #28 AC-4 .. AC-6, FDD #29 v0.3d AC-render-3d / AC-5d, and the v0.4
layout/batch endpoints.

Uses Starlette's TestClient via the ``client`` fixture defined in
``tests/api/conftest.py``. Each test exercises one endpoint and one assertion
focus so failures are easy to diagnose.

Tests that hit the bpy sidecar (``test_render_endpoint_with_render_3d_*``) are
marked ``slow`` because the cold-start sidecar spawn is 30–60s and a tiny 3D
render still takes a few seconds inside the worker. Run with
``pytest -m "not slow"`` to skip; run the full suite to exercise them.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from document_simulator.api.routers import receipt_synthesis as router_module
from document_simulator.synthesis.receipts.batch import (
    TEMPLATE_IDS,
    BatchResult,
    SampleFailure,
    SampleSuccess,
)

#: The v0.4 pipeline in full. ``layout`` leads: spec sampling became a real
#: stage when the renderer stopped being driven by the template id alone, and
#: it is what the ``content`` and ``raster`` stages are parameterised by.
FULL_STAGES = ["layout", "content", "raster", "augraphy"]

#: Stages that carry no image — they run before anything is rasterised.
IMAGELESS_STAGES = {"layout", "content"}


def test_render_endpoint_returns_all_stages(client) -> None:
    """AC-4: POST /render with augraphy_preset runs the whole pipeline, in order."""
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
    stage_names = [s["stage"] for s in stages]
    assert stage_names == FULL_STAGES, f"unexpected stage order: {stage_names}"

    by_name = {s["stage"]: s for s in stages}
    for name in FULL_STAGES:
        has_image = bool(by_name[name]["image_b64"])
        should_have = name not in IMAGELESS_STAGES
        assert (
            has_image is should_have
        ), f"stage {name}: image_b64 presence {has_image} but expected {should_have}"

    # The layout stage reports the spec that drove the render, so a sample can
    # be traced back to a layout without re-sampling.
    layout_params = by_name["layout"]["parameters"]
    assert (
        isinstance(layout_params.get("spec_id"), str) and len(layout_params["spec_id"]) == 12
    ), f"layout stage must report a 12-char spec_id, got {layout_params.get('spec_id')!r}"
    assert layout_params.get("blocks"), "layout stage must report the spec's blocks"

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
    assert gt["image_id"] == payload["image_id"], "GT image_id must match the response image_id"


def test_render_endpoint_no_augraphy_when_preset_null(client) -> None:
    """AC-4: when ``augraphy_preset`` is omitted, the augraphy stage is skipped."""
    body = {"template": "thermal_minimal", "seed": 42}
    r = client.post("/api/receipt-synthesis/render", json=body)
    assert r.status_code == 200, r.text

    stage_names = [s["stage"] for s in r.json()["stages"]]
    assert stage_names == [
        s for s in FULL_STAGES if s != "augraphy"
    ], f"expected the pipeline minus augraphy, got {stage_names}"


def test_render_is_deterministic_for_same_seed(client) -> None:
    """Same template + seed must select the same layout spec on every call."""
    body = {"template": "thermal_minimal", "seed": 7}
    first = client.post("/api/receipt-synthesis/render", json=body).json()
    second = client.post("/api/receipt-synthesis/render", json=body).json()

    def _spec_id(payload: dict) -> str:
        return next(s for s in payload["stages"] if s["stage"] == "layout")["parameters"]["spec_id"]

    assert _spec_id(first) == _spec_id(second), "layout sampling is not seed-deterministic"
    assert first["final_image_b64"] == second["final_image_b64"], "render is not deterministic"


def test_templates_endpoint_matches_the_content_registry(client) -> None:
    """AC-5: /templates lists exactly the registry's ids, with dropdown metadata.

    Asserted against the imported registry rather than a hardcoded id set: the
    router no longer keeps its own copy of the template list, and the point of
    that change is that these two can no longer disagree. A literal list here
    would just reintroduce the drift in the test suite.
    """
    r = client.get("/api/receipt-synthesis/templates")
    assert r.status_code == 200, r.text

    payload = r.json()
    assert "templates" in payload, "response missing templates"
    assert payload["templates"], "template list must not be empty"

    ids = [t["id"] for t in payload["templates"]]
    assert ids == list(
        TEMPLATE_IDS
    ), f"endpoint ids {ids} do not match the content registry {list(TEMPLATE_IDS)}"
    assert len(set(ids)) == len(ids), f"duplicate template ids: {ids}"

    for t in payload["templates"]:
        for field in ("id", "name", "description", "sample_token_count"):
            assert field in t, f"template {t.get('id')} missing field {field!r}"
        assert t["name"] and t["description"], f"template {t['id']} has empty display metadata"
        assert isinstance(t["sample_token_count"], int) and t["sample_token_count"] > 0


def test_augraphy_presets_endpoint_returns_known_presets(client) -> None:
    """AC-6: GET /augraphy-presets returns the existing preset names."""
    r = client.get("/api/receipt-synthesis/augraphy-presets")
    assert r.status_code == 200, r.text

    presets = r.json()["presets"]
    assert isinstance(presets, list) and presets, "presets must be a non-empty list"
    for expected in ("light", "medium", "heavy"):
        assert expected in presets, f"{expected} preset missing from {presets}"


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
    """AC-render-3d: omitting ``render_3d`` (or passing False) appends no
    ``3d_render`` stage, and explicit False matches omitted exactly.

    The expected list gained ``layout`` in v0.4, when spec sampling became a
    first-class stage. That is a deliberate widening, not the regression this
    test guards: the guarantee is that the *3D* path stays off.
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
        "layout",
        "content",
        "raster",
        "augraphy",
    ], f"non-3D stage order must be unchanged; got {stage_names}"

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

def test_render_endpoint_invalid_preset_returns_400(client) -> None:
    """An unknown Augraphy preset is rejected up front, not mid-pipeline."""
    body = {"template": "thermal_minimal", "seed": 1, "augraphy_preset": "nope"}
    r = client.post("/api/receipt-synthesis/render", json=body)
    assert r.status_code == 400, f"expected 400, got {r.status_code}: {r.text}"


# ---------------------------------------------------------------------------
# Batch endpoints (v0.4)
#
# ``run_batch`` is stubbed: these tests are about the HTTP contract (job
# lifecycle, dataset sandboxing, failure reporting), and a real batch would add
# a second of WeasyPrint per sample without testing anything new.
# ---------------------------------------------------------------------------


@pytest.fixture
def batch_sandbox(tmp_path, monkeypatch):
    """Point batch output at ``tmp_path`` and stub the runner.

    Yields the recorded ``run_batch`` kwargs so tests can assert the request was
    translated faithfully, and a mutable ``result`` the stub returns.
    """
    monkeypatch.setattr(router_module, "BATCH_ROOT", tmp_path)
    monkeypatch.setattr(router_module, "_BATCH_META", {})
    monkeypatch.setattr(router_module, "_BATCH_RESULTS", {})

    recorded: dict = {}

    def _fake_run_batch(n, seed, out_dir, **kwargs):
        recorded.update({"n": n, "seed": seed, "out_dir": Path(out_dir), **kwargs})
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        result = recorded.get("result")
        if result is None:
            result = BatchResult(
                n_requested=n,
                n_written=n,
                n_skipped=0,
                n_failed=0,
                out_dir=Path(out_dir),
                seed=seed,
                elapsed_s=0.1,
                written=[
                    SampleSuccess(
                        index=i, sample_id=f"s{i}", seed=seed + i, spec_id="a" * 12, elapsed_ms=1
                    )
                    for i in range(n)
                ],
            )
        return result

    monkeypatch.setattr(router_module, "run_batch", _fake_run_batch)
    return recorded


def test_start_batch_returns_202_and_runs_to_done(client, batch_sandbox) -> None:
    """POST /batch accepts the job, and the status endpoint reports the result."""
    body = {"n": 3, "seed": 5, "dataset": "unit-test", "workers": 1}
    r = client.post("/api/receipt-synthesis/batch", json=body)
    assert r.status_code == 202, f"expected 202 Accepted, got {r.status_code}: {r.text}"

    start = r.json()
    assert start["n"] == 3 and start["seed"] == 5 and start["dataset"] == "unit-test"
    assert start["out_dir"].endswith("unit-test"), f"unexpected out_dir {start['out_dir']}"

    # TestClient drains background tasks before returning, so the job is final.
    status = client.get(f"/api/receipt-synthesis/batch/{start['job_id']}")
    assert status.status_code == 200, status.text
    payload = status.json()
    assert payload["status"] == "done", f"job did not finish: {payload}"
    assert payload["progress"] == 1.0
    assert payload["n_written"] == 3, f"wrong written count: {payload}"
    assert payload["n_failed"] == 0
    assert payload["failures"] == []

    # The request was translated to the runner faithfully.
    assert batch_sandbox["n"] == 3
    assert batch_sandbox["seed"] == 5
    assert batch_sandbox["workers"] == 1
    assert batch_sandbox["resume"] is True


def test_batch_reports_per_sample_failures_without_failing_the_job(
    client, batch_sandbox, tmp_path
) -> None:
    """A run that wrote *some* samples is ``done`` — the failures ride in the body."""
    batch_sandbox["result"] = BatchResult(
        n_requested=2,
        n_written=1,
        n_skipped=0,
        n_failed=1,
        out_dir=tmp_path / "partial",
        seed=0,
        elapsed_s=0.2,
        written=[SampleSuccess(index=0, sample_id="ok", seed=0, spec_id="b" * 12, elapsed_ms=1)],
        failures=[
            SampleFailure(
                index=1, sample_id="bad", seed=1, spec_id="c" * 12, error="RuntimeError: x"
            )
        ],
    )
    start = client.post(
        "/api/receipt-synthesis/batch", json={"n": 2, "seed": 0, "dataset": "partial"}
    ).json()

    payload = client.get(f"/api/receipt-synthesis/batch/{start['job_id']}").json()
    assert payload["status"] == "done", "a partially successful batch is still a completed job"
    assert payload["n_failed"] == 1
    assert payload["error"], "a partial failure must surface an error summary"
    assert payload["failures"][0]["sample_id"] == "bad"
    assert "RuntimeError" in payload["failures"][0]["error"]


def test_batch_samples_endpoint_pages_the_manifest(client, batch_sandbox, tmp_path) -> None:
    """GET /batch/{id}/samples reads the on-disk manifest, and honours limit/offset."""
    start = client.post(
        "/api/receipt-synthesis/batch", json={"n": 1, "seed": 0, "dataset": "listing"}
    ).json()

    manifest = tmp_path / "listing" / "manifest.jsonl"
    manifest.write_text(
        "".join(
            f'{{"image_id": "id{i}", "image_path": "images/id{i}.png", '
            f'"gt_path": "ground_truth/id{i}.gt.json", "n_tokens": {i + 1}}}\n'
            for i in range(3)
        ),
        encoding="utf-8",
    )

    listing = client.get(f"/api/receipt-synthesis/batch/{start['job_id']}/samples").json()
    assert listing["total"] == 3, f"expected 3 manifest entries, got {listing['total']}"
    assert [s["image_id"] for s in listing["samples"]] == ["id0", "id1", "id2"]

    paged = client.get(
        f"/api/receipt-synthesis/batch/{start['job_id']}/samples",
        params={"limit": 1, "offset": 1},
    ).json()
    assert [s["image_id"] for s in paged["samples"]] == ["id1"], f"paging wrong: {paged}"
    assert paged["total"] == 3, "total must count the whole manifest, not the page"


def test_batch_download_returns_zip_of_the_dataset(client, batch_sandbox, tmp_path) -> None:
    """GET /batch/{id}/download streams the dataset directory as a ZIP."""
    import io
    import zipfile

    start = client.post(
        "/api/receipt-synthesis/batch", json={"n": 1, "seed": 0, "dataset": "zipme"}
    ).json()
    (tmp_path / "zipme" / "images").mkdir(parents=True, exist_ok=True)
    (tmp_path / "zipme" / "images" / "a.png").write_bytes(b"not-really-a-png")
    (tmp_path / "zipme" / "manifest.jsonl").write_text('{"image_id": "a"}\n', encoding="utf-8")

    r = client.get(f"/api/receipt-synthesis/batch/{start['job_id']}/download")
    assert r.status_code == 200, r.text
    assert r.headers["content-type"] == "application/zip"

    names = set(zipfile.ZipFile(io.BytesIO(r.content)).namelist())
    assert {"images/a.png", "manifest.jsonl"} <= names, f"zip missing dataset files: {names}"


def test_batch_status_unknown_job_returns_404(client, batch_sandbox) -> None:
    """An unknown job id is a 404, not a 500 from a missing dict key."""
    r = client.get("/api/receipt-synthesis/batch/not-a-job")
    assert r.status_code == 404, f"expected 404, got {r.status_code}: {r.text}"


@pytest.mark.parametrize("dataset", ["../escape", "/etc", "a/b", ""])
def test_batch_rejects_dataset_names_that_leave_the_output_root(
    client, batch_sandbox, dataset
) -> None:
    """The caller names a directory, never a path — the server picks where to write."""
    r = client.post("/api/receipt-synthesis/batch", json={"n": 1, "seed": 0, "dataset": dataset})
    assert (
        400 <= r.status_code < 500
    ), f"dataset {dataset!r} should be rejected, got {r.status_code}: {r.text}"


def test_batch_rejects_unknown_template_before_queueing(client, batch_sandbox) -> None:
    """A bad template id fails the request, rather than N samples later."""
    r = client.post(
        "/api/receipt-synthesis/batch",
        json={"n": 1, "seed": 0, "dataset": "bad-template", "template": "NOPE"},
    )
    assert r.status_code == 400, f"expected 400, got {r.status_code}: {r.text}"
    assert "n" not in batch_sandbox, "run_batch was called despite an invalid template"
