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
    source_status = {source["code"]: source for source in payload["sources"]}
    assert source_status["bangumi"]["enabled"] is True
    assert source_status["mal"]["enabled"] is False
    assert "episodes" in source_status["bangumi"]["capabilities"]
    assert "episodes" not in source_status["mal"]["capabilities"]
    assert {source["code"] for source in payload["sources"]} == {
        "bangumi",
        "mal",
        "douban",
        "filmarks",
    }
