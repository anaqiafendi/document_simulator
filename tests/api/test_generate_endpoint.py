import time
import zipfile
import io


def _wait_for_job(client, job_id, timeout=30):
    """Poll until job is done or failed."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = client.get(f"/api/jobs/{job_id}")
        data = r.json()
        if data["status"] in ("done", "failed"):
            return data
        time.sleep(0.2)
    raise TimeoutError(f"Job {job_id} did not complete in {timeout}s")


def test_post_generate_returns_202(client, minimal_synthesis_config):
    r = client.post("/api/generate", json={"synthesis_config": minimal_synthesis_config, "n": 2})
    assert r.status_code == 202


def test_post_generate_returns_job_id(client, minimal_synthesis_config):
    r = client.post("/api/generate", json={"synthesis_config": minimal_synthesis_config, "n": 2})
    assert "job_id" in r.json()


def test_get_job_status_returns_200(client, minimal_synthesis_config):
    job_id = client.post("/api/generate", json={"synthesis_config": minimal_synthesis_config, "n": 1}).json()["job_id"]
    r = client.get(f"/api/jobs/{job_id}")
    assert r.status_code == 200


def test_get_job_unknown_id_returns_404(client):
    r = client.get("/api/jobs/nonexistent-job-id")
    assert r.status_code == 404


def test_get_job_download_returns_zip(client, minimal_synthesis_config):
    job_id = client.post("/api/generate", json={"synthesis_config": minimal_synthesis_config, "n": 2}).json()["job_id"]
    _wait_for_job(client, job_id)
    r = client.get(f"/api/jobs/{job_id}/download")
    assert r.status_code == 200
    assert "zip" in r.headers["content-type"]


def test_generate_zip_contains_n_pdf_files(client, minimal_synthesis_config):
    n = 3
    job_id = client.post("/api/generate", json={"synthesis_config": minimal_synthesis_config, "n": n}).json()["job_id"]
    _wait_for_job(client, job_id)
    r = client.get(f"/api/jobs/{job_id}/download")
    zf = zipfile.ZipFile(io.BytesIO(r.content))
    pdf_files = [f for f in zf.namelist() if f.endswith(".pdf")]
    assert len(pdf_files) == n


def test_generate_zip_contains_n_json_files(client, minimal_synthesis_config):
    n = 3
    job_id = client.post("/api/generate", json={"synthesis_config": minimal_synthesis_config, "n": n}).json()["job_id"]
    _wait_for_job(client, job_id)
    r = client.get(f"/api/jobs/{job_id}/download")
    zf = zipfile.ZipFile(io.BytesIO(r.content))
    json_files = [f for f in zf.namelist() if f.endswith(".json")]
    assert len(json_files) == n


def test_generate_zip_json_is_valid_ground_truth(client, minimal_synthesis_config):
    from document_simulator.data.ground_truth import GroundTruth
    job_id = client.post("/api/generate", json={"synthesis_config": minimal_synthesis_config, "n": 1}).json()["job_id"]
    _wait_for_job(client, job_id)
    r = client.get(f"/api/jobs/{job_id}/download")
    zf = zipfile.ZipFile(io.BytesIO(r.content))
    json_files = [f for f in zf.namelist() if f.endswith(".json")]
    for jf in json_files:
        raw = zf.read(jf).decode()
        GroundTruth.model_validate_json(raw)  # must not raise
