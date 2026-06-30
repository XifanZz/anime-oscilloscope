from datetime import datetime
from typing import Literal, Protocol

from pydantic import BaseModel, Field

from anime_oscilloscope.domain import RatingObservation, SourceCode
from anime_oscilloscope.scoring import composite_score


class RatingPoint(BaseModel):
    sampled_at: datetime
    score: float = Field(ge=0, le=10)
    rating_count: int = Field(ge=0)


class RatingSeries(BaseModel):
    source: SourceCode
    points: list[RatingPoint]


class CompositePoint(BaseModel):
    sampled_at: datetime
    score: float = Field(ge=0, le=10)
    source_count: int = Field(ge=1)


class EpisodeMarker(BaseModel):
    episode_number: float = Field(gt=0)
    air_date: datetime
    title: str | None = None


class SourceFreshness(BaseModel):
    source: SourceCode
    status: Literal["fresh", "stale", "unavailable"]
    last_success_at: datetime | None = None
    last_attempt_at: datetime | None = None
    message: str | None = None


class RatingHistory(BaseModel):
    anime_id: str
    series: list[RatingSeries]
    composite: list[CompositePoint]
    episodes: list[EpisodeMarker]
    freshness: list[SourceFreshness]


class RatingHistoryResponse(BaseModel):
    data_mode: Literal["demo", "live"]
    history: RatingHistory
    sampling_policy: dict[str, str]


class HistoryRepository(Protocol):
    @property
    def data_mode(self) -> Literal["demo", "live"]: ...

    def get(self, anime_id: str) -> RatingHistory | None: ...


class InMemoryHistoryRepository:
    data_mode: Literal["demo"] = "demo"

    def __init__(self, histories: list[RatingHistory]) -> None:
        self._histories = {history.anime_id: history for history in histories}

    def get(self, anime_id: str) -> RatingHistory | None:
        return self._histories.get(anime_id)


def build_composite_series(series: list[RatingSeries]) -> list[CompositePoint]:
    by_time: dict[datetime, list[RatingObservation]] = {}
    for source_series in series:
        for point in source_series.points:
            by_time.setdefault(point.sampled_at, []).append(
                RatingObservation(
                    source=source_series.source,
                    score=point.score,
                    rating_count=point.rating_count,
                    sampled_at=point.sampled_at,
                )
            )

    result = []
    for sampled_at, observations in sorted(by_time.items()):
        score = composite_score(observations)
        if score is not None:
            result.append(
                CompositePoint(
                    sampled_at=sampled_at,
                    score=score,
                    source_count=len(observations),
                )
            )
    return result
