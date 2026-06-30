from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class SourceCode(StrEnum):
    BANGUMI = "bangumi"
    MAL = "mal"
    DOUBAN = "douban"
    FILMARKS = "filmarks"


class MediaType(StrEnum):
    TV = "tv"
    WEB = "web"
    MOVIE = "movie"
    OVA = "ova"
    SPECIAL = "special"
    OTHER = "other"


class AirStatus(StrEnum):
    UPCOMING = "upcoming"
    AIRING = "airing"
    FINISHED = "finished"
    UNKNOWN = "unknown"


class RatingObservation(BaseModel):
    source: SourceCode
    score: float = Field(ge=0, le=10)
    rating_count: int = Field(ge=0)
    source_rank: int | None = Field(default=None, gt=0)
    distribution: dict[int, int] | None = None
    sampled_at: datetime | None = None


class NormalizedAnime(BaseModel):
    source: SourceCode
    external_id: str
    canonical_name: str
    name_cn: str | None = None
    aliases: list[str] = Field(default_factory=list)
    summary: str | None = None
    image_url: str | None = None
    air_date: date | None = None
    end_date: date | None = None
    status: AirStatus = AirStatus.UNKNOWN
    media_type: MediaType = MediaType.OTHER
    regions: set[str] = Field(default_factory=set)
    is_nsfw: bool = False
    tags: list[str] = Field(default_factory=list)
    rating: RatingObservation | None = None
    source_url: str
    raw_platform: str | None = None


class NormalizedEpisode(BaseModel):
    source: SourceCode
    external_id: str
    subject_external_id: str
    episode_number: float | None = None
    episode_type: int
    title: str | None = None
    title_cn: str | None = None
    air_date: date | None = None


class SubjectPage(BaseModel):
    total: int = Field(ge=0)
    limit: int = Field(gt=0)
    offset: int = Field(ge=0)
    items: list[NormalizedAnime]
