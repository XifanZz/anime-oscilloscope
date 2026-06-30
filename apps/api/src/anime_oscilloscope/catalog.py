from datetime import UTC, date, datetime
from typing import Literal, Protocol

from pydantic import BaseModel, Field

from anime_oscilloscope.domain import AirStatus, MediaType, RatingObservation, SourceCode
from anime_oscilloscope.scoring import DEFAULT_VOTE_THRESHOLDS, composite_score, meets_thresholds


class CatalogAnime(BaseModel):
    id: str
    canonical_name: str
    name_cn: str | None = None
    aliases: list[str] = Field(default_factory=list)
    summary: str
    image_url: str | None = None
    air_date: date
    end_date: date | None = None
    media_type: MediaType
    status: AirStatus
    regions: set[str]
    episode_count: int | None = None
    tags: list[str] = Field(default_factory=list)
    ratings: list[RatingObservation]
    external_links: dict[SourceCode, str] = Field(default_factory=dict)
    updated_at: datetime


class RankedAnime(BaseModel):
    rank: int = 0
    anime: CatalogAnime
    composite_score: float
    completeness: int = Field(ge=0, le=100)
    missing_sources: list[SourceCode]


class RankingPage(BaseModel):
    data_mode: Literal["demo", "live"]
    generated_at: datetime
    total: int
    page: int
    page_size: int
    items: list[RankedAnime]


class CatalogRepository(Protocol):
    @property
    def data_mode(self) -> Literal["demo", "live"]: ...

    def list_all(self) -> list[CatalogAnime]: ...

    def get(self, anime_id: str) -> CatalogAnime | None: ...


class InMemoryCatalogRepository:
    data_mode: Literal["demo"] = "demo"

    def __init__(self, items: list[CatalogAnime]) -> None:
        self._items = items

    def list_all(self) -> list[CatalogAnime]:
        return list(self._items)

    def get(self, anime_id: str) -> CatalogAnime | None:
        return next((item for item in self._items if item.id == anime_id), None)


def rank_catalog(
    repository: CatalogRepository,
    *,
    year: int | None = None,
    quarter: int | None = None,
    region: str | None = None,
    media_type: MediaType | None = None,
    threshold_mode: bool = False,
    thresholds: dict[SourceCode, int] | None = None,
    page: int = 1,
    page_size: int = 20,
) -> RankingPage:
    active_thresholds = thresholds or {
        SourceCode.BANGUMI: DEFAULT_VOTE_THRESHOLDS[SourceCode.BANGUMI],
        SourceCode.MAL: DEFAULT_VOTE_THRESHOLDS[SourceCode.MAL],
    }
    candidates: list[RankedAnime] = []

    for anime in repository.list_all():
        anime_quarter = (anime.air_date.month - 1) // 3 + 1
        if year is not None and anime.air_date.year != year:
            continue
        if quarter is not None and anime_quarter != quarter:
            continue
        if region is not None and region.upper() not in anime.regions:
            continue
        if media_type is not None and anime.media_type != media_type:
            continue
        if threshold_mode and not meets_thresholds(anime.ratings, active_thresholds):
            continue

        score = composite_score(anime.ratings)
        if score is None:
            continue
        present = {rating.source for rating in anime.ratings}
        expected = {SourceCode.BANGUMI, SourceCode.MAL}
        candidates.append(
            RankedAnime(
                anime=anime,
                composite_score=score,
                completeness=round(100 * len(present & expected) / len(expected)),
                missing_sources=sorted(expected - present, key=str),
            )
        )

    candidates.sort(key=lambda item: item.composite_score, reverse=True)
    for index, item in enumerate(candidates, start=1):
        item.rank = index
    start = (page - 1) * page_size
    return RankingPage(
        data_mode=repository.data_mode,
        generated_at=datetime.now(UTC),
        total=len(candidates),
        page=page,
        page_size=page_size,
        items=candidates[start : start + page_size],
    )


def search_catalog(
    repository: CatalogRepository, query: str, limit: int = 20
) -> list[CatalogAnime]:
    needle = query.casefold().strip()
    if not needle:
        return []
    matches = []
    for anime in repository.list_all():
        haystack = [anime.canonical_name, anime.name_cn or "", *anime.aliases, *anime.tags]
        if any(needle in value.casefold() for value in haystack):
            matches.append(anime)
    return matches[:limit]
