from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

from anime_oscilloscope.catalog import CatalogAnime
from anime_oscilloscope.domain import SourceCode


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: str = "anime-oscilloscope-api"
    version: str
    environment: str
    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SourceStatus(BaseModel):
    code: SourceCode
    label: str
    enabled: bool
    reason: str | None = None
    capabilities: list[str] = Field(default_factory=list)


class ScoringRule(BaseModel):
    formula: str
    platform_coefficients: dict[SourceCode, float]
    default_vote_thresholds: dict[SourceCode, int]


class ServiceMetaResponse(BaseModel):
    product_name: str = "番剧示波器"
    product_name_en: str = "Anime Oscilloscope"
    subtitle: str = "多源动画评分采样与分析平台"
    phase: int = 7
    sources: list[SourceStatus]
    scoring: ScoringRule


class SearchResponse(BaseModel):
    data_mode: Literal["demo", "live"]
    query: str
    total: int
    items: list[CatalogAnime]


class CatalogIndexResponse(BaseModel):
    data_mode: Literal["demo", "live"]
    total: int
    items: list[CatalogAnime]


class AnimeDetailResponse(BaseModel):
    data_mode: Literal["demo", "live"]
    anime: CatalogAnime
    composite_score: float | None
    completeness: int = Field(ge=0, le=100)
    missing_sources: list[SourceCode]
