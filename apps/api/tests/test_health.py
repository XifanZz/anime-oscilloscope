from fastapi.testclient import TestClient

from anime_oscilloscope.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "anime-oscilloscope-api"


def test_meta_exposes_product_contract_and_disabled_sources() -> None:
    response = client.get("/api/v1/meta")

    assert response.status_code == 200
    payload = response.json()
    assert payload["product_name"] == "番剧示波器"
    assert payload["scoring"]["platform_coefficients"]["bangumi"] == 1.5
    assert all(source["enabled"] is False for source in payload["sources"])
    assert {source["code"] for source in payload["sources"]} == {
        "bangumi",
        "mal",
        "douban",
        "filmarks",
    }
