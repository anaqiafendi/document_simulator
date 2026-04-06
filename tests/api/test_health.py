def test_health_returns_200(client):
    r = client.get("/health")
    assert r.status_code == 200

def test_health_body_has_status_ok(client):
    r = client.get("/health")
    assert r.json()["status"] == "ok"
