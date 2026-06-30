import asyncio
import json
from datetime import date
from pathlib import Path

import httpx2 as httpx
import pytest

from anime_oscilloscope.connectors.bangumi import (
    BANGUMI_USER_AGENT,
    BangumiConnector,
    build_discovery_body,
    infer_regions,
    normalize_episode,
    normalize_media_type,
    normalize_subject,
)
from anime_oscilloscope.domain import AirStatus, MediaType
from anime_oscilloscope.policies import EligibilityStatus, evaluate_eligibility

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "bangumi"


def fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_normalizes_bangumi_subject_without_losing_provenance() -> None:
    anime = normalize_subject(fixture("subject.json"), as_of=date(2026, 6, 30))

    assert anime.external_id == "900001"
    assert anime.name_cn == "信号动画"
    assert anime.aliases == ["Signal Anime", "信号番"]
    assert anime.regions == {"JP"}
    assert anime.media_type is MediaType.TV
    assert anime.episode_count == 12
    assert anime.status is AirStatus.UPCOMING
    assert anime.rating is not None
    assert anime.rating.score == 8.4
    assert anime.rating.rating_count == 1234
    assert anime.source_url == "https://bgm.tv/subject/900001"


@pytest.mark.parametrize(
    ("platform", "expected"),
    [
        ("TV", MediaType.TV),
        ("WEB", MediaType.WEB),
        ("剧场版", MediaType.MOVIE),
        ("OVA", MediaType.OVA),
        ("Special", MediaType.SPECIAL),
        ("广播剧", MediaType.OTHER),
    ],
)
def test_normalizes_media_types(platform: str, expected: MediaType) -> None:
    assert normalize_media_type(platform) is expected


def test_discovery_payload_excludes_nsfw_and_uses_half_open_dates() -> None:
    body = build_discovery_body(date(2026, 7, 1), date(2026, 10, 1))

    assert body["keyword"] == ""
    assert body["filter"] == {
        "type": [2],
        "air_date": [">=2026-07-01", "<2026-10-01"],
        "nsfw": False,
    }


def test_infers_region_from_explicit_public_tags_when_infobox_is_missing() -> None:
    assert infer_regions({"meta_tags": ["TV", "日本", "原创"], "tags": []}) == {"JP"}


def test_fixture_search_exercises_eligibility_decisions() -> None:
    payload = fixture("search_subjects.json")
    decisions = [
        evaluate_eligibility(normalize_subject(item, as_of=date(2026, 6, 30)))
        for item in payload["data"]
    ]

    assert [decision.status for decision in decisions] == [
        EligibilityStatus.ELIGIBLE,
        EligibilityStatus.ELIGIBLE,
        EligibilityStatus.EXCLUDED,
    ]
    assert decisions[-1].reason == "excluded_franchise"


def test_normalizes_main_and_special_episodes() -> None:
    payload = fixture("episodes.json")
    episodes = [normalize_episode(item, "900001") for item in payload["data"]]

    assert episodes[0].episode_number == 1
    assert episodes[0].air_date == date(2026, 7, 3)
    assert episodes[1].episode_type == 1
    assert episodes[1].title_cn == "校准"


def test_discover_sends_identifying_headers_and_normalizes_fixture() -> None:
    observed: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        observed["method"] = request.method
        observed["user_agent"] = request.headers["user-agent"]
        observed["body"] = json.loads(request.content)
        return httpx.Response(200, json=fixture("search_subjects.json"))

    async def execute() -> tuple[int, list[str]]:
        async with BangumiConnector(transport=httpx.MockTransport(handler)) as connector:
            page = await connector.discover(
                start_date=date(2026, 7, 1),
                end_date=date(2026, 10, 1),
                limit=20,
            )
        return page.total, [item.external_id for item in page.items]

    total, ids = asyncio.run(execute())

    assert observed["method"] == "POST"
    assert observed["user_agent"] == BANGUMI_USER_AGENT
    assert observed["body"] == build_discovery_body(date(2026, 7, 1), date(2026, 10, 1))
    assert total == 3
    assert ids == ["900001", "900002", "900003"]
