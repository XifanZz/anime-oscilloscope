from fastapi.testclient import TestClient

from anime_oscilloscope.main import app, semantic_limiter
from anime_oscilloscope.rate_limit import FixedWindowRateLimiter

client = TestClient(app)


def test_fixed_window_limiter_resets_after_window() -> None:
    now = [100.0]
    limiter = FixedWindowRateLimiter(limit=2, window_seconds=10, clock=lambda: now[0])

    assert limiter.check("client").remaining == 1
    assert limiter.check("client").remaining == 0
    denied = limiter.check("client")
    assert not denied.allowed
    assert denied.retry_after == 10

    now[0] = 110.0
    assert limiter.check("client").allowed


def test_semantic_endpoint_is_rate_limited_and_exposes_headers() -> None:
    semantic_limiter.reset()
    try:
        responses = [
            client.post("/api/v1/anime/semantic-search", json={"query": "科幻动画"})
            for _ in range(31)
        ]
        assert responses[0].headers["X-RateLimit-Limit"] == "30"
        assert responses[29].headers["X-RateLimit-Remaining"] == "0"
        assert responses[30].status_code == 429
        assert int(responses[30].headers["Retry-After"]) >= 1
    finally:
        semantic_limiter.reset()


def test_api_responses_include_security_headers() -> None:
    response = client.get("/api/v1/health")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Permissions-Policy"] == "camera=(), microphone=(), geolocation=()"
