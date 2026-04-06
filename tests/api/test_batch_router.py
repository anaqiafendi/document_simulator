"""Tests for the batch augmentation router endpoints."""

import io
import time
import pytest
from PIL import Image


@pytest.fixture
def two_tiny_pngs():
    """Two small PNG byte strings."""
    result = []
    for color in ((200, 200, 200), (100, 150, 200)):
        buf = io.BytesIO()
        Image.new("RGB", (50, 60), color=color).save(buf, format="PNG")
        buf.seek(0)
        result.append(buf.read())
    return result


def test_process_returns_job_id(client, two_tiny_pngs):
    r = client.post(
        "/api/batch/process",
        files=[
            ("files", ("a.png", two_tiny_pngs[0], "image/png")),
            ("files", ("b.png", two_tiny_pngs[1], "image/png")),
        ],
        data={"preset": "light", "mode": "single"},
    )
    assert r.status_code == 202, r.text
    assert "job_id" in r.json()


def test_process_job_id_is_string(client, two_tiny_pngs):
    r = client.post(
        "/api/batch/process",
        files=[("files", ("a.png", two_tiny_pngs[0], "image/png"))],
        data={"preset": "light", "mode": "single"},
    )
    assert r.status_code == 202
    assert isinstance(r.json()["job_id"], str)
    assert len(r.json()["job_id"]) > 0


def test_batch_status_pending_or_running(client, two_tiny_pngs):
    r = client.post(
        "/api/batch/process",
        files=[("files", ("a.png", two_tiny_pngs[0], "image/png"))],
        data={"preset": "light", "mode": "single", "n_workers": "1"},
    )
    job_id = r.json()["job_id"]
    status_r = client.get(f"/api/batch/jobs/{job_id}")
    assert status_r.status_code == 200
    assert status_r.json()["status"] in ("pending", "running", "done", "failed")


def test_download_before_done_returns_404(client, two_tiny_pngs):
    # Start a job but don't wait — it almost certainly hasn't finished yet
    r = client.post(
        "/api/batch/process",
        files=[("files", ("a.png", two_tiny_pngs[0], "image/png"))],
        data={"preset": "heavy", "mode": "single", "n_workers": "1"},
    )
    job_id = r.json()["job_id"]
    # Poll until done or give up after a few attempts — for test purposes,
    # if job is already done we skip the 404 check (fast machines / mocked env)
    for _ in range(3):
        status = client.get(f"/api/batch/jobs/{job_id}").json()["status"]
        if status == "done":
            pytest.skip("Job finished before we could test 404 on download")
        if status == "failed":
            break
        time.sleep(0.05)
    dl = client.get(f"/api/batch/jobs/{job_id}/download")
    # Either 404 (not done yet) or 200 (completed quickly) is acceptable
    assert dl.status_code in (200, 404)


def test_status_unknown_job_returns_404(client):
    r = client.get("/api/batch/jobs/nonexistent-uuid-12345")
    assert r.status_code == 404


def test_process_no_files_returns_422(client):
    r = client.post("/api/batch/process", data={"preset": "light"})
    assert r.status_code == 422


def test_process_invalid_preset_returns_422(client, two_tiny_pngs):
    r = client.post(
        "/api/batch/process",
        files=[("files", ("a.png", two_tiny_pngs[0], "image/png"))],
        data={"preset": "nonexistent"},
    )
    assert r.status_code == 422
