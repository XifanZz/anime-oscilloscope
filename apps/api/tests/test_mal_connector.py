import asyncio
import json
from datetime import date
from pathlib import Path

import httpx2 as httpx
import pytest

from anime_oscilloscope.connectors.base import ConnectorCapabilityError
from anime_oscilloscope.connectors.mal import (
    MAL_FIELDS,
    MALConnector,
    normalize_mal_anime,
    normalize_mal_media_type,
    season_from_bounds,
)
from anime_oscilloscope.domain import AirStatus, MediaType

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "mal"


def fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_normalizes_mal_details_and_rating_population() -> None:
    anime = normalize_mal_anime(fixture("anime_details.json"))

    assert anime.external_id == "800001"
    assert anime.canonical_name == "Signal Anime"
    assert "Signal no Anime" in anime.aliases
    assert anime.media_type is MediaType.TV
    assert anime.status is AirStatus.AIRING
    assert anime.episode_count == 12
    assert anime.rating is not None
    assert anime.rating.score == 8.32
    assert anime.rating.rating_count == 24050
    assert anime.source_url == "https://myanimelist.net/anime/800001"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("tv", MediaType.TV),
        ("ona", MediaType.WEB),
        ("movie", MediaType.MOVIE),
        ("ova", MediaType.OVA),
        ("special", MediaType.SPECIAL),
        ("music", MediaType.OTHER),
    ],
)
def test_normalizes_mal_media_type(raw: str, expected: MediaType) -> None:
    assert normalize_mal_media_type(raw) is expected


def test_maps_exact_calendar_quarters_to_mal_seasons() -> None:
    assert season_from_bounds(date(2026, 7, 1), date(2026, 10, 1)) == (2026, "summer")
    assert season_from_bounds(date(2026, 10, 1), date(2027, 1, 1)) == (2026, "fall")


def test_rejects_non_quarter_discovery_ranges() -> None:
    with pytest.raises(ValueError, match="exact calendar quarter"):
        season_from_bounds(date(2026, 7, 2), date(2026, 10, 1))


def test_season_request_uses_client_id_fields_and_pagination() -> None:
    observed: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        observed["path"] = request.url.path
        observed["client_id"] = request.headers["x-mal-client-id"]
        observed["fields"] = request.url.params["fields"]
        return httpx.Response(200, json=fixture("season.json"))

    async def execute() -> tuple[bool, list[str]]:
        async with MALConnector(
            client_id="fixture-client-id",
            transport=httpx.MockTransport(handler),
        ) as connector:
            page = await connector.discover(
                start_date=date(2026, 7, 1),
                end_date=date(2026, 10, 1),
                limit=1,
            )
        return page.has_next, [item.external_id for item in page.items]

    has_next, ids = asyncio.run(execute())

    assert observed["path"] == "/v2/anime/season/2026/summer"
    assert observed["client_id"] == "fixture-client-id"
    assert observed["fields"] == MAL_FIELDS
    assert has_next is True
    assert ids == ["800001"]


def test_mal_explicitly_rejects_episode_timeline_reads() -> None:
    async def execute() -> None:
        async with MALConnector(
            client_id="fixture-client-id",
            transport=httpx.MockTransport(lambda _: httpx.Response(200, json={})),
        ) as connector:
            await connector.fetch_episodes("800001")

    with pytest.raises(ConnectorCapabilityError, match="does not expose episode timeline"):
        asyncio.run(execute())
