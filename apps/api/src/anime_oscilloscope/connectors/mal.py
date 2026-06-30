import asyncio
from collections.abc import Mapping
from datetime import UTC, date, datetime
from typing import Any

import httpx2 as httpx

from anime_oscilloscope.connectors.base import (
    ConnectorCapability,
    ConnectorCapabilityError,
    ConnectorError,
    ConnectorResponseError,
    SourceConnector,
)
from anime_oscilloscope.domain import (
    AirStatus,
    MediaType,
    NormalizedAnime,
    NormalizedEpisode,
    RatingObservation,
    SourceCode,
    SubjectPage,
)

MAL_API_BASE_URL = "https://api.myanimelist.net/v2"
MAL_FIELDS = ",".join(
    (
        "id",
        "title",
        "main_picture",
        "alternative_titles",
        "start_date",
        "end_date",
        "synopsis",
        "mean",
        "rank",
        "num_scoring_users",
        "nsfw",
        "media_type",
        "status",
        "genres",
        "num_episodes",
        "start_season",
        "studios",
    )
)
_SEASONS = {1: "winter", 4: "spring", 7: "summer", 10: "fall"}


def _parse_partial_date(value: Any) -> date | None:
    if not isinstance(value, str) or not value.strip():
        return None
    parts = value.strip().split("-")
    try:
        year = int(parts[0])
        month = int(parts[1]) if len(parts) >= 2 else 1
        day = int(parts[2]) if len(parts) >= 3 else 1
        return date(year, month, day)
    except (ValueError, IndexError):
        return None


def normalize_mal_media_type(value: Any) -> MediaType:
    normalized = str(value or "").strip().casefold()
    return {
        "tv": MediaType.TV,
        "ona": MediaType.WEB,
        "movie": MediaType.MOVIE,
        "ova": MediaType.OVA,
        "special": MediaType.SPECIAL,
    }.get(normalized, MediaType.OTHER)


def _normalize_status(value: Any) -> AirStatus:
    normalized = str(value or "").strip().casefold()
    return {
        "not_yet_aired": AirStatus.UPCOMING,
        "currently_airing": AirStatus.AIRING,
        "finished_airing": AirStatus.FINISHED,
    }.get(normalized, AirStatus.UNKNOWN)


def _aliases(payload: Mapping[str, Any]) -> list[str]:
    alternative = payload.get("alternative_titles")
    if not isinstance(alternative, Mapping):
        return []
    values: list[str] = []
    synonyms = alternative.get("synonyms")
    if isinstance(synonyms, list):
        values.extend(str(value).strip() for value in synonyms if str(value).strip())
    for key in ("en", "ja"):
        value = alternative.get(key)
        if isinstance(value, str) and value.strip():
            values.append(value.strip())
    title = str(payload.get("title") or "").strip()
    return list(dict.fromkeys(value for value in values if value != title))


def _normalize_rating(payload: Mapping[str, Any]) -> RatingObservation | None:
    mean = payload.get("mean")
    count = payload.get("num_scoring_users")
    if not isinstance(mean, (int, float)) or not isinstance(count, int) or count < 0:
        return None
    rank = payload.get("rank")
    return RatingObservation(
        source=SourceCode.MAL,
        score=float(mean),
        rating_count=count,
        source_rank=rank if isinstance(rank, int) and rank > 0 else None,
        sampled_at=datetime.now(UTC),
    )


def normalize_mal_anime(payload: Mapping[str, Any]) -> NormalizedAnime:
    anime_id = payload.get("id")
    title = payload.get("title")
    if not isinstance(anime_id, int) or not isinstance(title, str) or not title.strip():
        raise ConnectorResponseError("MAL anime requires an integer id and non-empty title")
    picture = payload.get("main_picture")
    image_url = None
    if isinstance(picture, Mapping):
        image_url = picture.get("large") or picture.get("medium")
        if not isinstance(image_url, str):
            image_url = None
    raw_genres = payload.get("genres")
    genres: list[str] = []
    if isinstance(raw_genres, list):
        genres = [
            str(item["name"]).strip()
            for item in raw_genres
            if isinstance(item, Mapping) and isinstance(item.get("name"), str)
        ]
    aliases = _aliases(payload)
    episode_count = payload.get("num_episodes")
    return NormalizedAnime(
        source=SourceCode.MAL,
        external_id=str(anime_id),
        canonical_name=title.strip(),
        name_cn=None,
        aliases=aliases,
        summary=str(payload.get("synopsis") or "").strip() or None,
        image_url=image_url,
        air_date=_parse_partial_date(payload.get("start_date")),
        end_date=_parse_partial_date(payload.get("end_date")),
        episode_count=episode_count if isinstance(episode_count, int) else None,
        status=_normalize_status(payload.get("status")),
        media_type=normalize_mal_media_type(payload.get("media_type")),
        regions=set(),
        is_nsfw=str(payload.get("nsfw") or "white").casefold() in {"gray", "black"},
        tags=genres,
        rating=_normalize_rating(payload),
        source_url=f"https://myanimelist.net/anime/{anime_id}",
        raw_platform=str(payload.get("media_type") or "").strip() or None,
    )


def season_from_bounds(start_date: date, end_date: date) -> tuple[int, str]:
    if start_date.day != 1 or start_date.month not in _SEASONS:
        raise ValueError("MAL discovery requires an exact calendar quarter")
    expected_end = (
        date(start_date.year + 1, 1, 1)
        if start_date.month == 10
        else date(start_date.year, start_date.month + 3, 1)
    )
    if end_date != expected_end:
        raise ValueError("MAL discovery requires an exact calendar quarter")
    return start_date.year, _SEASONS[start_date.month]


class MALConnector(SourceConnector):
    source = SourceCode.MAL
    capabilities = frozenset(
        {
            ConnectorCapability.DISCOVERY,
            ConnectorCapability.SEARCH,
            ConnectorCapability.SUBJECT,
            ConnectorCapability.RATINGS,
        }
    )

    def __init__(
        self,
        *,
        client_id: str,
        base_url: str = MAL_API_BASE_URL,
        timeout_seconds: float = 15.0,
        max_attempts: int = 3,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        if not client_id.strip():
            raise ValueError("MAL client ID is required")
        self.base_url = base_url.rstrip("/")
        self.max_attempts = max(1, max_attempts)
        self._client = httpx.AsyncClient(
            headers={"Accept": "application/json", "X-MAL-CLIENT-ID": client_id.strip()},
            timeout=timeout_seconds,
            transport=transport,
        )

    async def __aenter__(self) -> "MALConnector":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _request_json(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                response = await self._client.get(f"{self.base_url}{path}", params=params)
                if response.status_code == 429 or response.status_code >= 500:
                    raise ConnectorError(
                        f"MAL temporary response {response.status_code} for {path}"
                    )
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict):
                    raise ConnectorResponseError(f"MAL returned a non-object for {path}")
                return payload
            except (httpx.HTTPError, ConnectorError, ValueError) as exc:
                last_error = exc
                if attempt < self.max_attempts:
                    await asyncio.sleep(0.25 * (2 ** (attempt - 1)))
        raise ConnectorError(f"MAL request failed for {path}") from last_error

    @staticmethod
    def _normalize_list(payload: Mapping[str, Any]) -> list[NormalizedAnime]:
        data = payload.get("data")
        if not isinstance(data, list):
            raise ConnectorResponseError("MAL list response is missing data[]")
        items: list[NormalizedAnime] = []
        for item in data:
            if not isinstance(item, Mapping):
                continue
            node = item.get("node")
            if isinstance(node, Mapping):
                items.append(normalize_mal_anime(node))
        return items

    async def discover(
        self,
        *,
        start_date: date,
        end_date: date,
        limit: int = 50,
        offset: int = 0,
    ) -> SubjectPage:
        if not 1 <= limit <= 500:
            raise ValueError("limit must be between 1 and 500")
        if offset < 0:
            raise ValueError("offset must be non-negative")
        year, season = season_from_bounds(start_date, end_date)
        payload = await self._request_json(
            f"/anime/season/{year}/{season}",
            params={
                "sort": "anime_score",
                "limit": limit,
                "offset": offset,
                "fields": MAL_FIELDS,
                "nsfw": "false",
            },
        )
        items = self._normalize_list(payload)
        paging = payload.get("paging")
        has_next = isinstance(paging, Mapping) and bool(paging.get("next"))
        return SubjectPage(
            total=None,
            limit=limit,
            offset=offset,
            has_next=has_next,
            items=items,
        )

    async def search(self, query: str, *, limit: int = 10) -> list[NormalizedAnime]:
        normalized_query = query.strip()
        if not normalized_query:
            return []
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        payload = await self._request_json(
            "/anime",
            params={"q": normalized_query, "limit": limit, "offset": 0, "fields": MAL_FIELDS},
        )
        return self._normalize_list(payload)

    async def fetch_subject(self, external_id: str) -> NormalizedAnime:
        payload = await self._request_json(
            f"/anime/{int(external_id)}",
            params={"fields": MAL_FIELDS},
        )
        return normalize_mal_anime(payload)

    async def fetch_episodes(self, external_id: str) -> list[NormalizedEpisode]:
        raise ConnectorCapabilityError(
            f"MAL does not expose episode timeline data for anime {external_id}"
        )
