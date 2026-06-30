from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

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
    phase: int = 1
    sources: list[SourceStatus]
    scoring: ScoringRule
