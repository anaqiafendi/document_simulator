import base64
from PIL import Image
import io


def test_post_preview_returns_200(client, minimal_synthesis_config):
    r = client.post("/api/preview", json={"synthesis_config": minimal_synthesis_config})
    assert r.status_code == 200


def test_post_preview_returns_exactly_3_samples(client, minimal_synthesis_config):
    r = client.post("/api/preview", json={"synthesis_config": minimal_synthesis_config})
    data = r.json()
    assert len(data["samples"]) == 3


def test_post_preview_samples_are_base64_strings(client, minimal_synthesis_config):
    r = client.post("/api/preview", json={"synthesis_config": minimal_synthesis_config})
    for sample in r.json()["samples"]:
        assert isinstance(sample["image_b64"], str)
        assert len(sample["image_b64"]) > 0
        img_bytes = base64.b64decode(sample["image_b64"])
        img = Image.open(io.BytesIO(img_bytes))
        assert img.format == "PNG"


def test_post_preview_custom_seeds_are_respected(client, minimal_synthesis_config):
    seeds = [10, 20, 30]
    r = client.post("/api/preview", json={"synthesis_config": minimal_synthesis_config, "seeds": seeds})
    returned_seeds = [s["seed"] for s in r.json()["samples"]]
    assert returned_seeds == seeds


def test_post_preview_invalid_config_returns_422(client):
    r = client.post("/api/preview", json={"synthesis_config": {"bad_field": "bad_value"}})
    assert r.status_code == 422


def test_post_preview_zero_zones_returns_3_samples(client, minimal_synthesis_config):
    # Zero zones should still produce 3 blank images, not crash
    r = client.post("/api/preview", json={"synthesis_config": minimal_synthesis_config})
    assert r.status_code == 200
    assert len(r.json()["samples"]) == 3
