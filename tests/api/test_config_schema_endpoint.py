def test_get_config_schema_returns_200(client):
    r = client.get("/api/config/schema")
    assert r.status_code == 200


def test_get_config_schema_is_valid_json_schema(client):
    data = client.get("/api/config/schema").json()
    # Pydantic v2 JSON schema has either "properties" or "$defs"
    assert "properties" in data or "$defs" in data


def test_get_config_schema_contains_title(client):
    data = client.get("/api/config/schema").json()
    assert "title" in data
