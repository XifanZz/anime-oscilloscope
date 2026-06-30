from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from anime_oscilloscope.demo_catalog import DEMO_CATALOG
from anime_oscilloscope.jobs.evaluate_semantic import evaluate
from anime_oscilloscope.main import app
from anime_oscilloscope.semantic import (
    HashEmbeddingProvider,
    SemanticSearchRequest,
    SemanticSearchService,
    parse_intent,
)

client = TestClient(app)


def test_intent_parser_extracts_structured_chinese_constraints() -> None:
    intent = parse_intent(
        "想看一部2026年中日合拍的悬疑WEB连载",
        {"悬疑", "合拍", "太空"},
    )

    assert intent.year == 2026
    assert intent.regions == ["CN", "JP"]
    assert [media.value for media in intent.media_types] == ["web"]
    assert [status.value for status in intent.statuses] == ["airing"]
    assert intent.tags == ["合拍", "悬疑"]


def test_semantic_service_returns_reasons_and_confidence() -> None:
    service = SemanticSearchService(DEMO_CATALOG, HashEmbeddingProvider())

    response = service.search(
        SemanticSearchRequest(query="中日合拍的悬疑WEB动画", limit=10)
    )

    assert response.engine == "hash-512-demo"
    assert response.results[0].anime.id == "demo-tidal"
    assert response.results[0].confidence > 0.5
    assert "制作地区匹配：CN / JP" in response.results[0].reasons
    assert "标签匹配：合拍、悬疑" in response.results[0].reasons


def test_semantic_endpoint_supports_korean_completed_space_movie_query() -> None:
    response = client.post(
        "/api/v1/anime/semantic-search",
        json={"query": "韩国完结的太空电影", "limit": 5},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data_mode"] == "demo"
    assert payload["results"][0]["anime"]["id"] == "demo-lantern"
    assert payload["elapsed_ms"] >= 0
    assert payload["model_name"] == "deterministic-character-ngram"


def test_semantic_endpoint_validates_short_queries_and_limits() -> None:
    short = client.post("/api/v1/anime/semantic-search", json={"query": "番"})
    excessive = client.post(
        "/api/v1/anime/semantic-search", json={"query": "科幻动画", "limit": 100}
    )

    assert short.status_code == 422
    assert excessive.status_code == 422


def test_semantic_service_rejects_wrong_vector_dimensions() -> None:
    class WrongDimensionProvider:
        name = "wrong"
        model_name = "wrong"

        def embed(self, texts: list[str]) -> list[list[float]]:
            return [[0.0, 1.0] for _ in texts]

    service = SemanticSearchService(DEMO_CATALOG, WrongDimensionProvider())

    with pytest.raises(RuntimeError, match="512-dimensional"):
        service.search(SemanticSearchRequest(query="科幻动画"))


def test_fifty_query_evaluation_set_meets_recall_contract() -> None:
    metrics = evaluate(Path("apps/api/tests/fixtures/semantic_queries.json"))

    assert metrics["cases"] == 50
    assert metrics["recall_at_10"] >= 0.9
