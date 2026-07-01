import asyncio
from collections.abc import Mapping
from datetime import UTC, date, datetime
from typing import Any

import httpx2 as httpx

from anime_oscilloscope.connectors.base import (
    ConnectorCapability,
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

BANGUMI_API_BASE_URL = "https://api.bgm.tv"
BANGUMI_USER_AGENT = (
    "XifanZz/anime-oscilloscope/0.1.0 "
    "(https://github.com/XifanZz/anime-oscilloscope)"
)

_REGION_PATTERNS: dict[str, tuple[str, ...]] = {
    "CN": ("中国", "中國", "china", "chinese", "中国大陆", "中国香港", "中国台湾"),
    "JP": ("日本", "japan", "japanese", "日本国"),
    "KR": ("韩国", "韓國", "south korea", "korea", "한국", "대한민국"),
}
_REGION_INFOBOX_KEYS = {
    "国家",
    "地区",
    "国家/地区",
    "製作国家",
    "制作国家",
    "制片国家/地区",
    "放送地区",
}
_REGION_TAG_PATTERNS: dict[str, tuple[str, ...]] = {
    "CN": ("中国", "中國", "中国大陆", "国产", "国产动画", "国创", "china"),
    "JP": ("日本", "日本动画", "japan"),
    "KR": ("韩国", "韓國", "韩国动画", "south korea", "korea", "한국"),
}


def _parse_date(value: Any) -> date | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return None


def _flatten_infobox_value(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if not isinstance(value, list):
        return []
    flattened: list[str] = []
    for item in value:
        if isinstance(item, Mapping):
            candidate = item.get("v")
            if isinstance(candidate, str) and candidate.strip():
                flattened.append(candidate.strip())
    return flattened


def _infobox_entries(payload: Mapping[str, Any]) -> list[tuple[str, list[str]]]:
    result: list[tuple[str, list[str]]] = []
    raw_infobox = payload.get("infobox")
    if not isinstance(raw_infobox, list):
        return result
    for item in raw_infobox:
        if not isinstance(item, Mapping):
            continue
        key = item.get("key")
        if isinstance(key, str):
            result.append((key.strip(), _flatten_infobox_value(item.get("value"))))
    return result


def extract_aliases(payload: Mapping[str, Any]) -> list[str]:
    aliases: list[str] = []
    names = {str(payload.get("name", "")).strip(), str(payload.get("name_cn", "")).strip()}
    for key, values in _infobox_entries(payload):
        if "别名" in key or "別名" in key or key in {"英文名", "日文名", "中文名"}:
            aliases.extend(values)
    return list(dict.fromkeys(alias for alias in aliases if alias and alias not in names))


def infer_regions(payload: Mapping[str, Any]) -> set[str]:
    regions: set[str] = set()
    for key, values in _infobox_entries(payload):
        if key not in _REGION_INFOBOX_KEYS:
            continue
        joined = " ".join(values).casefold()
        for region, patterns in _REGION_PATTERNS.items():
            if any(pattern.casefold() in joined for pattern in patterns):
                regions.add(region)
    tag_values: list[str] = []
    meta_tags = payload.get("meta_tags")
    if isinstance(meta_tags, list):
        tag_values.extend(str(tag).strip().casefold() for tag in meta_tags if str(tag).strip())
    raw_tags = payload.get("tags")
    if isinstance(raw_tags, list):
        tag_values.extend(
            str(item["name"]).strip().casefold()
            for item in raw_tags
            if isinstance(item, Mapping) and isinstance(item.get("name"), str)
        )
    for region, patterns in _REGION_TAG_PATTERNS.items():
        normalized_patterns = {pattern.casefold() for pattern in patterns}
        if any(tag in normalized_patterns for tag in tag_values):
            regions.add(region)
    return regions


def normalize_media_type(platform: Any) -> MediaType:
    value = str(platform or "").strip().casefold()
    if value == "tv" or "tv" in value:
        return MediaType.TV
    if value == "web" or "web" in value:
        return MediaType.WEB
    if any(token in value for token in ("剧场", "劇場", "movie", "映画")):
        return MediaType.MOVIE
    if any(token in value for token in ("ova", "oad")):
        return MediaType.OVA
    if any(token in value for token in ("special", "特别", "特別", "sp")):
        return MediaType.SPECIAL
    return MediaType.OTHER


def _normalize_rating(payload: Mapping[str, Any]) -> RatingObservation | None:
    rating = payload.get("rating")
    if not isinstance(rating, Mapping):
        return None
    score = rating.get("score")
    total = rating.get("total")
    if not isinstance(score, (int, float)) or not isinstance(total, int) or total < 0:
        return None
    rank = rating.get("rank")
    source_rank = rank if isinstance(rank, int) and rank > 0 else None
    raw_distribution = rating.get("count")
    distribution: dict[int, int] | None = None
    if isinstance(raw_distribution, Mapping):
        distribution = {
            int(key): value
            for key, value in raw_distribution.items()
            if str(key).isdigit() and isinstance(value, int) and value >= 0
        }
    return RatingObservation(
        source=SourceCode.BANGUMI,
        score=float(score),
        rating_count=total,
        source_rank=source_rank,
        distribution=distribution,
        sampled_at=datetime.now(UTC),
    )


def normalize_subject(payload: Mapping[str, Any], *, as_of: date | None = None) -> NormalizedAnime:
    subject_id = payload.get("id")
    name = payload.get("name")
    if not isinstance(subject_id, int) or not isinstance(name, str) or not name.strip():
        raise ConnectorResponseError("Bangumi subject requires an integer id and non-empty name")

    name_cn = payload.get("name_cn")
    normalized_name_cn = name_cn.strip() if isinstance(name_cn, str) and name_cn.strip() else None
    air_date = _parse_date(payload.get("date"))
    today = as_of or date.today()
    status = (
        AirStatus.UPCOMING
        if air_date and air_date > today
        else AirStatus.AIRING
        if air_date
        else AirStatus.UNKNOWN
    )
    images = payload.get("images")
    image_url = None
    if isinstance(images, Mapping):
        for size in ("large", "common", "medium", "small", "grid"):
            candidate = images.get(size)
            if isinstance(candidate, str) and candidate:
                image_url = candidate
                break
    raw_tags = payload.get("tags")
    tags = []
    if isinstance(raw_tags, list):
        tags = [
            str(item["name"]).strip()
            for item in raw_tags
            if isinstance(item, Mapping) and isinstance(item.get("name"), str)
        ]

    return NormalizedAnime(
        source=SourceCode.BANGUMI,
        external_id=str(subject_id),
        canonical_name=name.strip(),
        name_cn=normalized_name_cn,
        aliases=extract_aliases(payload),
        summary=str(payload.get("summary") or "").strip() or None,
        image_url=image_url,
        air_date=air_date,
        episode_count=(
            int(payload["total_episodes"])
            if isinstance(payload.get("total_episodes"), int)
            else None
        ),
        status=status,
        media_type=normalize_media_type(payload.get("platform")),
        regions=infer_regions(payload),
        is_nsfw=bool(payload.get("nsfw", False)),
        tags=tags,
        rating=_normalize_rating(payload),
        source_url=f"https://bgm.tv/subject/{subject_id}",
        raw_platform=str(payload.get("platform") or "").strip() or None,
    )


def normalize_episode(payload: Mapping[str, Any], subject_external_id: str) -> NormalizedEpisode:
    episode_id = payload.get("id")
    episode_type = payload.get("type")
    if not isinstance(episode_id, int) or not isinstance(episode_type, int):
        raise ConnectorResponseError("Bangumi episode requires integer id and type")
    episode_number = payload.get("ep")
    if not isinstance(episode_number, (int, float)):
        sort_number = payload.get("sort")
        episode_number = float(sort_number) if isinstance(sort_number, (int, float)) else None
    return NormalizedEpisode(
        source=SourceCode.BANGUMI,
        external_id=str(episode_id),
        subject_external_id=subject_external_id,
        episode_number=float(episode_number) if episode_number is not None else None,
        episode_type=episode_type,
        title=str(payload.get("name") or "").strip() or None,
        title_cn=str(payload.get("name_cn") or "").strip() or None,
        air_date=_parse_date(payload.get("airdate")),
    )


def build_discovery_body(start_date: date, end_date: date) -> dict[str, Any]:
    if end_date <= start_date:
        raise ValueError("end_date must be after start_date")
    return {
        "keyword": "",
        "sort": "rank",
        "filter": {
            "type": [2],
            "air_date": [f">={start_date.isoformat()}", f"<{end_date.isoformat()}"],
            "nsfw": False,
        },
    }


class BangumiConnector(SourceConnector):
    source = SourceCode.BANGUMI
    capabilities = frozenset(
        {
            ConnectorCapability.DISCOVERY,
            ConnectorCapability.SEARCH,
            ConnectorCapability.SUBJECT,
            ConnectorCapability.EPISODES,
            ConnectorCapability.RATINGS,
        }
    )

    def __init__(
        self,
        *,
        token: str | None = None,
        base_url: str = BANGUMI_API_BASE_URL,
        user_agent: str = BANGUMI_USER_AGENT,
        timeout_seconds: float = 15.0,
        max_attempts: int = 3,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.max_attempts = max(1, max_attempts)
        headers = {
            "Accept": "application/json",
            "User-Agent": user_agent,
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self._client = httpx.AsyncClient(
            headers=headers,
            timeout=timeout_seconds,
            transport=transport,
        )

    async def __aenter__(self) -> "BangumiConnector":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _request_json(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                response = await self._client.request(
                    method,
                    f"{self.base_url}{path}",
                    params=params,
                    json=json,
                )
                if response.status_code == 429 or response.status_code >= 500:
                    raise ConnectorError(
                        f"Bangumi temporary response {response.status_code} for {path}"
                    )
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict):
                    raise ConnectorResponseError(f"Bangumi returned a non-object for {path}")
                return payload
            except (httpx.HTTPError, ConnectorError, ValueError) as exc:
                last_error = exc
                if attempt < self.max_attempts:
                    await asyncio.sleep(0.25 * (2 ** (attempt - 1)))
        raise ConnectorError(f"Bangumi request failed for {path}") from last_error

    async def discover(
        self,
        *,
        start_date: date,
        end_date: date,
        limit: int = 50,
        offset: int = 0,
    ) -> SubjectPage:
        if not 1 <= limit <= 200:
            raise ValueError("limit must be between 1 and 200")
        if offset < 0:
            raise ValueError("offset must be non-negative")
        payload = await self._request_json(
            "POST",
            "/v0/search/subjects",
            params={"limit": limit, "offset": offset},
            json=build_discovery_body(start_date, end_date),
        )
        data = payload.get("data")
        if not isinstance(data, list):
            raise ConnectorResponseError("Bangumi search response is missing data[]")
        items = [normalize_subject(item) for item in data if isinstance(item, Mapping)]
        return SubjectPage(
            total=int(payload.get("total", len(items))),
            limit=int(payload.get("limit", limit)) or limit,
            offset=int(payload.get("offset", offset)),
            has_next=int(payload.get("offset", offset)) + len(items)
            < int(payload.get("total", len(items))),
            items=items,
        )

    async def fetch_subject(self, external_id: str) -> NormalizedAnime:
        payload = await self._request_json("GET", f"/v0/subjects/{int(external_id)}")
        return normalize_subject(payload)

    async def search(self, query: str, *, limit: int = 10) -> list[NormalizedAnime]:
        normalized_query = query.strip()
        if not normalized_query:
            return []
        if not 1 <= limit <= 50:
            raise ValueError("limit must be between 1 and 50")
        payload = await self._request_json(
            "POST",
            "/v0/search/subjects",
            params={"limit": limit, "offset": 0},
            json={
                "keyword": normalized_query,
                "sort": "match",
                "filter": {"type": [2], "nsfw": False},
            },
        )
        data = payload.get("data")
        if not isinstance(data, list):
            raise ConnectorResponseError("Bangumi search response is missing data[]")
        return [normalize_subject(item) for item in data if isinstance(item, Mapping)]

    async def fetch_episodes(self, external_id: str) -> list[NormalizedEpisode]:
        subject_id = str(int(external_id))
        episodes: list[NormalizedEpisode] = []
        offset = 0
        limit = 200
        while True:
            payload = await self._request_json(
                "GET",
                "/v0/episodes",
                params={"subject_id": subject_id, "limit": limit, "offset": offset},
            )
            data = payload.get("data")
            if not isinstance(data, list):
                raise ConnectorResponseError("Bangumi episode response is missing data[]")
            episodes.extend(
                normalize_episode(item, subject_id) for item in data if isinstance(item, Mapping)
            )
            total = int(payload.get("total", len(episodes)))
            offset += len(data)
            if not data or offset >= total:
                break
        return episodes
