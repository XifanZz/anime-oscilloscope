from fastapi import APIRouter, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from anime_oscilloscope import __version__
from anime_oscilloscope.catalog import RankingPage, rank_catalog, search_catalog
from anime_oscilloscope.config import get_settings
from anime_oscilloscope.connectors import BangumiConnector, MALConnector
from anime_oscilloscope.demo_catalog import DEMO_CATALOG
from anime_oscilloscope.domain import MediaType, SourceCode
from anime_oscilloscope.schemas import (
    AnimeDetailResponse,
    HealthResponse,
    ScoringRule,
    SearchResponse,
    ServiceMetaResponse,
    SourceStatus,
)
from anime_oscilloscope.scoring import composite_score

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


@router.get("/rankings", response_model=RankingPage, tags=["catalog"])
def rankings(
    year: int | None = Query(default=None, ge=1900, le=2100),
    quarter: int | None = Query(default=None, ge=1, le=4),
    region: str | None = Query(default=None, min_length=2, max_length=2),
    media_type: MediaType | None = None,
    mode: str = Query(default="unrestricted", pattern="^(unrestricted|threshold)$"),
    bangumi_min: int = Query(default=1000, ge=0),
    mal_min: int = Query(default=20000, ge=0),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> RankingPage:
    return rank_catalog(
        DEMO_CATALOG,
        year=year,
        quarter=quarter,
        region=region,
        media_type=media_type,
        threshold_mode=mode == "threshold",
        thresholds={SourceCode.BANGUMI: bangumi_min, SourceCode.MAL: mal_min},
        page=page,
        page_size=page_size,
    )


@router.get("/anime/search", response_model=SearchResponse, tags=["catalog"])
def anime_search(
    q: str = Query(min_length=1, max_length=100),
    limit: int = Query(default=20, ge=1, le=50),
) -> SearchResponse:
    items = search_catalog(DEMO_CATALOG, q, limit)
    return SearchResponse(data_mode=DEMO_CATALOG.data_mode, query=q, total=len(items), items=items)


@router.get("/anime/{anime_id}", response_model=AnimeDetailResponse, tags=["catalog"])
def anime_detail(anime_id: str) -> AnimeDetailResponse:
    anime = DEMO_CATALOG.get(anime_id)
    if anime is None:
        raise HTTPException(status_code=404, detail="Anime not found")
    expected = {SourceCode.BANGUMI, SourceCode.MAL}
    present = {rating.source for rating in anime.ratings}
    return AnimeDetailResponse(
        data_mode=DEMO_CATALOG.data_mode,
        anime=anime,
        composite_score=composite_score(anime.ratings),
        completeness=round(100 * len(present & expected) / len(expected)),
        missing_sources=sorted(expected - present, key=str),
    )


app.include_router(router)
