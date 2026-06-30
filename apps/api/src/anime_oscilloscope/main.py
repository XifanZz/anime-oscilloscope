from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from anime_oscilloscope import __version__
from anime_oscilloscope.config import get_settings
from anime_oscilloscope.connectors import BangumiConnector, MALConnector
from anime_oscilloscope.schemas import (
    HealthResponse,
    ScoringRule,
    ServiceMetaResponse,
    SourceStatus,
)

settings = get_settings()

app = FastAPI(
    title="Anime Oscilloscope API",
    summary="多源动画评分采样与分析平台 API",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
)

router = APIRouter(prefix="/api/v1")


@router.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    return HealthResponse(version=__version__, environment=settings.env)


@router.get("/meta", response_model=ServiceMetaResponse, tags=["system"])
def service_meta() -> ServiceMetaResponse:
    return ServiceMetaResponse(
        sources=[
            SourceStatus(
                code="bangumi",
                label="Bangumi",
                enabled=True,
                capabilities=sorted(BangumiConnector.capabilities),
            ),
            SourceStatus(
                code="mal",
                label="MyAnimeList",
                enabled=bool(settings.mal_client_id),
                reason=None if settings.mal_client_id else "Configure APP_MAL_CLIENT_ID",
                capabilities=sorted(MALConnector.capabilities),
            ),
            SourceStatus(
                code="douban",
                label="豆瓣",
                enabled=False,
                reason="Requires written authorization",
                capabilities=[],
            ),
            SourceStatus(
                code="filmarks",
                label="Filmarks",
                enabled=False,
                reason="Requires written authorization",
                capabilities=[],
            ),
        ],
        scoring=ScoringRule(
            formula="sum(score * alpha * log1p(votes)) / sum(alpha * log1p(votes))",
            platform_coefficients={
                "bangumi": 1.5,
                "mal": 1.0,
                "douban": 1.0,
                "filmarks": 1.0,
            },
            default_vote_thresholds={
                "bangumi": 1000,
                "mal": 20000,
                "douban": 5000,
                "filmarks": 1000,
            },
        ),
    )


app.include_router(router)
