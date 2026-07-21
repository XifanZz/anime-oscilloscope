from fastapi.testclient import TestClient

from anime_oscilloscope.main import app

client = TestClient(app)


def test_rankings_are_scored_sorted_and_explicitly_demo_data() -> None:
    response = client.get("/api/v1/rankings")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data_mode"] == "demo"
    assert payload["total"] == 4
    assert payload["items"][0]["anime"]["name_cn"] == "极光频率"
    assert payload["items"][0]["completeness"] == 100
    assert payload["items"][2]["missing_sources"] == ["mal"]


def test_ranking_filters_by_season_region_media_and_default_thresholds() -> None:
    seasonal = client.get("/api/v1/rankings?year=2026&quarter=2&region=CN&media_type=web")
    threshold = client.get("/api/v1/rankings?mode=threshold")

    assert seasonal.status_code == 200
    assert seasonal.json()["total"] == 1
    assert seasonal.json()["items"][0]["anime"]["id"] == "demo-tidal"
    assert threshold.status_code == 200
    assert [item["anime"]["id"] for item in threshold.json()["items"]] == [
        "demo-aurora",
        "demo-tidal",
    ]


def test_custom_thresholds_and_pagination_are_applied() -> None:
    response = client.get(
        "/api/v1/rankings?mode=threshold&bangumi_min=400&mal_min=6000&page=2&page_size=1"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 3
    assert payload["page"] == 2
    assert len(payload["items"]) == 1


def test_search_matches_chinese_title_aliases_and_tags() -> None:
    title = client.get("/api/v1/anime/search", params={"q": "潮汐"})
    tag = client.get("/api/v1/anime/search", params={"q": "太空"})

    assert title.status_code == 200
    assert title.json()["items"][0]["id"] == "demo-tidal"
    assert tag.json()["items"][0]["id"] == "demo-lantern"


def test_catalog_index_can_be_downloaded_without_uploading_private_titles() -> None:
    response = client.get("/api/v1/anime/index")
    limited = client.get("/api/v1/anime/index?limit=2")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data_mode"] == "demo"
    assert payload["total"] == 4
    assert {item["id"] for item in payload["items"]} == {
        "demo-aurora",
        "demo-tidal",
        "demo-lantern",
        "demo-paper-moon",
    }
    assert limited.json()["total"] == 4
    assert len(limited.json()["items"]) == 2


def test_data_quality_summarizes_demo_catalog_and_source_gaps() -> None:
    response = client.get("/api/v1/data/quality")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data_mode"] == "demo"
    assert payload["total_anime"] == 4
    assert payload["eligible_anime"] == 4
    assert payload["rankable_anime"] == 4
    assert payload["with_bangumi_rating"] == 4
    assert payload["with_mal_rating"] == 3
    assert payload["missing_mal"] == 1
    assert payload["connectors"][0]["source"] == "bangumi"
    assert payload["connectors"][0]["status"] == "fresh"


def test_mapping_candidate_queue_is_readable_and_review_writes_are_guarded() -> None:
    response = client.get("/api/v1/mappings/candidates")
    forbidden = client.post(
        "/api/v1/mappings/candidates/1001/resolve",
        json={"decision": "approved"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data_mode"] == "demo"
    assert payload["summary"]["source"] == "mal"
    assert payload["summary"]["unresolved_review_count"] == 1
    assert payload["items"][0]["source"] == "mal"
    assert payload["items"][0]["external_url"].startswith("https://myanimelist.net/anime/")
    assert forbidden.status_code == 403
    assert forbidden.json()["detail"] == "Review writes are disabled"


def test_detail_explains_source_completeness_and_returns_404() -> None:
    detail = client.get("/api/v1/anime/demo-lantern")
    missing = client.get("/api/v1/anime/unknown")

    assert detail.status_code == 200
    assert detail.json()["composite_score"] == 8.3
    assert detail.json()["missing_sources"] == ["mal"]
    assert missing.status_code == 404
