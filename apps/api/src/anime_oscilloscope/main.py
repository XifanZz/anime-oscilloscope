from fastapi import APIRouter, FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from anime_oscilloscope import __version__
from anime_oscilloscope.catalog import RankingPage, rank_catalog, search_catalog
from anime_oscilloscope.config import get_settings
from anime_oscilloscope.connectors import BangumiConnector, MALConnector
from anime_oscilloscope.database import create_repositories
from anime_oscilloscope.domain import MediaType, SourceCode
from anime_oscilloscope.history import RatingHistoryResponse
from anime_oscilloscope.mapping_review import create_mapping_review_repository
from anime_oscilloscope.quality import create_quality_repository
from anime_oscilloscope.rate_limit import FixedWindowRateLimiter
from anime_oscilloscope.schemas import (
    AnimeDetailResponse,
    CatalogIndexResponse,
    DataQualityResponse,
    HealthResponse,
    MappingCandidatePage,
    MappingResolutionRequest,
    MappingResolutionResponse,
    ScoringRule,
    SearchResponse,
    ServiceMetaResponse,
    SourceStatus,
)
from anime_oscilloscope.scoring import composite_score
from anime_oscilloscope.semantic import (
    SemanticSearchRequest,
    SemanticSearchResponse,
    SemanticSearchService,
    create_embedding_provider,
)

settings = get_settings()
catalog_repository, history_repository = create_repositories(settings)
quality_repository = create_quality_repository(settings, catalog_repository)
mapping_review_repository = create_mapping_review_repository(settings, catalog_repository)
semantic_service = SemanticSearchService(
    catalog_repository,
    create_embedding_provider(settings.semantic_backend, settings.semantic_model_name),
)
semantic_limiter = FixedWindowRateLimiter(limit=30, window_seconds=60)

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


@app.middleware("http")
async def add_api_security_headers(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/api/"):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response

router = APIRouter(prefix="/api/v1")


@router.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    return HealthResponse(
        version=__version__, environment=settings.env, data_mode=catalog_repository.data_mode
    )


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


@router.get("/data/quality", response_model=DataQualityResponse, tags=["system"])
def data_quality() -> DataQualityResponse:
    return quality_repository.get()


@router.get("/mappings/candidates", response_model=MappingCandidatePage, tags=["mapping"])
def mapping_candidates(
    source: SourceCode = SourceCode.MAL,
    disposition: str = Query(default="review", pattern="^(automatic|review|reject)$"),
    unresolved_only: bool = True,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> MappingCandidatePage:
    if source not in {SourceCode.MAL, SourceCode.DOUBAN, SourceCode.FILMARKS}:
        raise HTTPException(status_code=422, detail="Only secondary sources have candidates")
    return mapping_review_repository.list_candidates(
        source=source,
        disposition=disposition,
        unresolved_only=unresolved_only,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/mappings/candidates/{candidate_id}/resolve",
    response_model=MappingResolutionResponse,
    tags=["mapping"],
)
def resolve_mapping_candidate(
    candidate_id: int,
    payload: MappingResolutionRequest,
    x_review_token: str | None = Header(default=None),
) -> MappingResolutionResponse:
    if not settings.review_admin_token:
        raise HTTPException(status_code=403, detail="Review writes are disabled")
    if x_review_token != settings.review_admin_token:
        raise HTTPException(status_code=403, detail="Invalid review token")
    try:
        return mapping_review_repository.resolve_candidate(candidate_id, decision=payload.decision)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


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
        catalog_repository,
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
    items = search_catalog(catalog_repository, q, limit)
    return SearchResponse(
        data_mode=catalog_repository.data_mode, query=q, total=len(items), items=items
    )


@router.get("/anime/index", response_model=CatalogIndexResponse, tags=["catalog"])
def anime_catalog_index(
    limit: int = Query(default=500, ge=1, le=2000),
) -> CatalogIndexResponse:
    items = catalog_repository.list_all()
    return CatalogIndexResponse(
        data_mode=catalog_repository.data_mode,
        total=len(items),
        items=items[:limit],
    )


@router.post(
    "/anime/semantic-search",
    response_model=SemanticSearchResponse,
    tags=["ai"],
)
def anime_semantic_search(
    payload: SemanticSearchRequest,
    request: Request,
    response: Response,
) -> SemanticSearchResponse:
    client_key = request.client.host if request.client else "unknown"
    decision = semantic_limiter.check(client_key)
    headers = {
        "X-RateLimit-Limit": str(semantic_limiter.limit),
        "X-RateLimit-Remaining": str(decision.remaining),
    }
    if not decision.allowed:
        headers["Retry-After"] = str(decision.retry_after)
        raise HTTPException(status_code=429, detail="Rate limit exceeded", headers=headers)
    response.headers.update(headers)
    return semantic_service.search(payload)


@router.get("/anime/{anime_id}", response_model=AnimeDetailResponse, tags=["catalog"])
def anime_detail(anime_id: str) -> AnimeDetailResponse:
    anime = catalog_repository.get(anime_id)
    if anime is None:
        raise HTTPException(status_code=404, detail="Anime not found")
    expected = {SourceCode.BANGUMI, SourceCode.MAL}
    present = {rating.source for rating in anime.ratings}
    return AnimeDetailResponse(
        data_mode=catalog_repository.data_mode,
        anime=anime,
        composite_score=composite_score(anime.ratings),
        completeness=round(100 * len(present & expected) / len(expected)),
        missing_sources=sorted(expected - present, key=str),
    )


@router.get(
    "/anime/{anime_id}/ratings/history",
    response_model=RatingHistoryResponse,
    tags=["ratings"],
)
def anime_rating_history(anime_id: str) -> RatingHistoryResponse:
    if catalog_repository.get(anime_id) is None:
        raise HTTPException(status_code=404, detail="Anime not found")
    history = history_repository.get(anime_id)
    if history is None:
        raise HTTPException(status_code=404, detail="Rating history is not available")
    return RatingHistoryResponse(
        data_mode=history_repository.data_mode,
        history=history,
        sampling_policy={
            "airing": "daily",
            "completed_0_to_3_months": "weekly",
            "completed_3_months_to_3_years": "monthly",
            "completed_after_3_years": "yearly",
        },
    )


app.include_router(router)
