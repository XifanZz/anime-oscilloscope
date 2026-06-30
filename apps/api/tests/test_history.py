from datetime import UTC, datetime

from fastapi.testclient import TestClient

from anime_oscilloscope.domain import SourceCode
from anime_oscilloscope.history import RatingPoint, RatingSeries, build_composite_series
from anime_oscilloscope.main import app

client = TestClient(app)


def test_composite_history_uses_available_sources_per_timestamp() -> None:
    first = datetime(2026, 4, 1, tzinfo=UTC)
    second = datetime(2026, 4, 2, tzinfo=UTC)
    series = [
        RatingSeries(
            source=SourceCode.BANGUMI,
            points=[
                RatingPoint(sampled_at=first, score=8.0, rating_count=1000),
                RatingPoint(sampled_at=second, score=8.4, rating_count=1500),
            ],
        ),
        RatingSeries(
            source=SourceCode.MAL,
            points=[RatingPoint(sampled_at=first, score=8.2, rating_count=20000)],
        ),
    ]

    result = build_composite_series(series)

    assert result[0].source_count == 2
    assert result[1].score == 8.4
    assert result[1].source_count == 1


def test_history_endpoint_returns_series_episodes_policy_and_stale_source() -> None:
    response = client.get("/api/v1/anime/demo-aurora/ratings/history")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data_mode"] == "demo"
    assert len(payload["history"]["series"]) == 2
    assert len(payload["history"]["composite"]) == 87
    assert len(payload["history"]["episodes"]) == 12
    assert payload["sampling_policy"]["airing"] == "daily"
    freshness = {item["source"]: item for item in payload["history"]["freshness"]}
    assert freshness["mal"]["status"] == "stale"
    assert "上次成功快照" in freshness["mal"]["message"]


def test_history_endpoint_distinguishes_unknown_title_from_untracked_title() -> None:
    untracked = client.get("/api/v1/anime/demo-tidal/ratings/history")
    unknown = client.get("/api/v1/anime/unknown/ratings/history")

    assert untracked.status_code == 404
    assert untracked.json()["detail"] == "Rating history is not available"
    assert unknown.status_code == 404
    assert unknown.json()["detail"] == "Anime not found"
