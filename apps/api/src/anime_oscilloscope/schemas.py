from datetime import UTC, date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from anime_oscilloscope.catalog import CatalogAnime
from anime_oscilloscope.domain import SourceCode


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: str = "anime-oscilloscope-api"
    version: str
    environment: str
    data_mode: Literal["demo", "live"]
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
    phase: int = 8
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


class ConnectorQuality(BaseModel):
    source: SourceCode
    label: str
    enabled: bool
    status: Literal["fresh", "stale", "unavailable"]
    mapped_count: int = Field(ge=0)
    rated_count: int = Field(ge=0)
    latest_sampled_at: datetime | None = None
    last_success_at: datetime | None = None
    last_attempt_at: datetime | None = None
    message: str | None = None


class BackfillQuality(BaseModel):
    source: SourceCode
    start_year: int
    end_year: int
    next_year: int
    next_offset: int
    processed_pages: int = Field(ge=0)
    discovered_count: int = Field(ge=0)
    completed: bool
    progress_percent: int = Field(ge=0, le=100)
    last_error: str | None = None
    updated_at: datetime


class SyncRunSummary(BaseModel):
    source: SourceCode
    job_type: str
    status: str
    succeeded_count: int = Field(ge=0)
    failed_count: int = Field(ge=0)
    started_at: datetime
    finished_at: datetime | None = None


class DataQualityResponse(BaseModel):
    data_mode: Literal["demo", "live"]
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    total_anime: int = Field(ge=0)
    eligible_anime: int = Field(ge=0)
    rankable_anime: int = Field(ge=0)
    excluded_anime: int = Field(ge=0)
    nsfw_anime: int = Field(ge=0)
    with_bangumi_rating: int = Field(ge=0)
    with_mal_rating: int = Field(ge=0)
    with_both_core_sources: int = Field(ge=0)
    missing_mal: int = Field(ge=0)
    latest_rating_sampled_at: datetime | None = None
    latest_catalog_updated_at: datetime | None = None
    connectors: list[ConnectorQuality] = Field(default_factory=list)
    backfill: BackfillQuality | None = None
    recent_runs: list[SyncRunSummary] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class MappingAnimeSummary(BaseModel):
    id: str
    bangumi_id: int | None = None
    canonical_name: str
    name_cn: str | None = None
    image_url: str | None = None
    air_date: date | None = None
    media_type: str
    status: str
    regions: list[str] = Field(default_factory=list)
    episode_count: int | None = None


class MappingCandidateItem(BaseModel):
    id: int
    anime: MappingAnimeSummary
    source: SourceCode
    external_id: str
    external_url: str
    title: str
    confidence: float = Field(ge=0, le=1)
    disposition: str
    evidence: dict
    generated_at: datetime
    resolved_at: datetime | None = None
    current_review_status: str | None = None


class MappingReviewSummary(BaseModel):
    source: SourceCode
    unresolved_review_count: int = Field(ge=0)
    automatic_count: int = Field(ge=0)
    rejected_count: int = Field(ge=0)
    approved_mapping_count: int = Field(ge=0)
    unmapped_rankable_count: int = Field(ge=0)


class MappingCandidatePage(BaseModel):
    data_mode: Literal["demo", "live"]
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    total: int = Field(ge=0)
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)
    summary: MappingReviewSummary
    items: list[MappingCandidateItem]


class MappingResolutionRequest(BaseModel):
    decision: Literal["approved", "rejected"]


class MappingResolutionResponse(BaseModel):
    data_mode: Literal["demo", "live"]
    candidate_id: int
    decision: Literal["approved", "rejected"]
    external_mapping_id: int | None = None
    resolved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AnimeDetailResponse(BaseModel):
    data_mode: Literal["demo", "live"]
    anime: CatalogAnime
    composite_score: float | None
    completeness: int = Field(ge=0, le=100)
    missing_sources: list[SourceCode]
