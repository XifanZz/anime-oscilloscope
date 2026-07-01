from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from contextlib import AbstractContextManager
from datetime import UTC, datetime
from typing import Any

from psycopg import Connection, connect
from psycopg.rows import dict_row

from anime_oscilloscope.catalog import CatalogAnime, CatalogRepository
from anime_oscilloscope.config import Settings
from anime_oscilloscope.demo_catalog import DEMO_CATALOG
from anime_oscilloscope.demo_history import DEMO_HISTORY
from anime_oscilloscope.domain import RatingObservation, SourceCode
from anime_oscilloscope.history import (
    EpisodeMarker,
    HistoryRepository,
    RatingHistory,
    RatingPoint,
    RatingSeries,
    SourceFreshness,
    build_composite_series,
)

Row = Mapping[str, Any]
ConnectionFactory = Callable[[], AbstractContextManager[Connection[dict[str, Any]]]]


def normalize_dsn(value: str) -> str:
    return value.replace("postgresql+psycopg://", "postgresql://", 1)


def external_url(source: SourceCode, external_id: str) -> str:
    if source is SourceCode.BANGUMI:
        return f"https://bgm.tv/subject/{external_id}"
    if source is SourceCode.MAL:
        return f"https://myanimelist.net/anime/{external_id}"
    return ""


def catalog_anime_from_rows(
    row: Row,
    rating_rows: Sequence[Row],
    mapping_rows: Sequence[Row],
) -> CatalogAnime:
    ratings = [
        RatingObservation(
            source=item["source"],
            score=float(item["score"]),
            rating_count=item["rating_count"],
            source_rank=item.get("source_rank"),
            sampled_at=item["sampled_at"],
        )
        for item in rating_rows
    ]
    links = {
        SourceCode(item["source"]): external_url(SourceCode(item["source"]), item["external_id"])
        for item in mapping_rows
        if external_url(SourceCode(item["source"]), item["external_id"])
    }
    return CatalogAnime(
        id=str(row["id"]),
        canonical_name=row["canonical_name"],
        name_cn=row.get("name_cn"),
        aliases=list(row.get("aliases") or []),
        summary=row.get("summary") or "",
        image_url=row.get("image_url"),
        air_date=row["air_date"],
        end_date=row.get("end_date"),
        media_type=row["media_type"],
        status=row["status"],
        regions=set(row.get("regions") or []),
        episode_count=row.get("episode_count"),
        tags=list(row.get("tags") or []),
        ratings=ratings,
        external_links=links,
        updated_at=row["updated_at"],
    )


class PostgresDatabase:
    def __init__(self, dsn: str) -> None:
        self.dsn = normalize_dsn(dsn)

    def connection(self) -> AbstractContextManager[Connection[dict[str, Any]]]:
        return connect(self.dsn, row_factory=dict_row, connect_timeout=10)


class PostgresCatalogRepository(CatalogRepository):
    data_mode = "live"

    def __init__(self, connection_factory: ConnectionFactory) -> None:
        self._connection = connection_factory

    def list_all(self) -> list[CatalogAnime]:
        with self._connection() as connection:
            anime_rows = connection.execute(
                """select id, canonical_name, name_cn, aliases, summary, image_url,
                          air_date, end_date, media_type, status, regions, episode_count,
                          tags, updated_at
                   from anime
                   where not is_nsfw and not is_excluded and air_date is not null
                   order by air_date desc, id"""
            ).fetchall()
            if not anime_rows:
                return []
            ids = [row["id"] for row in anime_rows]
            ratings = connection.execute(
                """select anime_id, source, score, rating_count, source_rank, sampled_at
                   from current_rating where anime_id = any(%s)""",
                (ids,),
            ).fetchall()
            mappings = connection.execute(
                """select anime_id, source, external_id from external_mapping
                   where anime_id = any(%s) and review_status in ('automatic', 'approved')""",
                (ids,),
            ).fetchall()
        ratings_by_id: dict[Any, list[Row]] = defaultdict(list)
        mappings_by_id: dict[Any, list[Row]] = defaultdict(list)
        for item in ratings:
            ratings_by_id[item["anime_id"]].append(item)
        for item in mappings:
            mappings_by_id[item["anime_id"]].append(item)
        return [
            catalog_anime_from_rows(row, ratings_by_id[row["id"]], mappings_by_id[row["id"]])
            for row in anime_rows
        ]

    def get(self, anime_id: str) -> CatalogAnime | None:
        return next((item for item in self.list_all() if item.id == anime_id), None)


class PostgresHistoryRepository(HistoryRepository):
    data_mode = "live"

    def __init__(self, connection_factory: ConnectionFactory) -> None:
        self._connection = connection_factory

    def get(self, anime_id: str) -> RatingHistory | None:
        with self._connection() as connection:
            snapshots = connection.execute(
                """select source, score, rating_count, sampled_at from rating_snapshot
                   where anime_id = %s order by sampled_at, source""",
                (anime_id,),
            ).fetchall()
            if not snapshots:
                return None
            episodes = connection.execute(
                """select episode_number, air_date, coalesce(title_cn, title) as title
                   from episode where anime_id = %s and episode_number is not null
                   and air_date is not null order by episode_number""",
                (anime_id,),
            ).fetchall()
            freshness = connection.execute(
                """select code as source, last_success_at, last_attempt_at, last_error
                   from source_connector where code in ('bangumi', 'mal') order by code"""
            ).fetchall()
        by_source: dict[SourceCode, list[RatingPoint]] = defaultdict(list)
        for item in snapshots:
            by_source[SourceCode(item["source"])].append(
                RatingPoint(
                    sampled_at=item["sampled_at"],
                    score=float(item["score"]),
                    rating_count=item["rating_count"],
                )
            )
        series = [
            RatingSeries(source=source, points=points) for source, points in by_source.items()
        ]
        return RatingHistory(
            anime_id=anime_id,
            series=series,
            composite=build_composite_series(series),
            episodes=[EpisodeMarker(**item) for item in episodes],
            freshness=[source_freshness_from_row(item) for item in freshness],
        )


def source_freshness_from_row(row: Row) -> SourceFreshness:
    attempted = row.get("last_attempt_at")
    succeeded = row.get("last_success_at")
    error = row.get("last_error")
    if succeeded is None:
        status = "unavailable"
    elif error and attempted and attempted >= succeeded:
        status = "stale"
    else:
        status = "fresh"
    return SourceFreshness(
        source=row["source"],
        status=status,
        last_success_at=succeeded,
        last_attempt_at=attempted,
        message=error,
    )


def create_repositories(settings: Settings) -> tuple[CatalogRepository, HistoryRepository]:
    if settings.repository_backend == "demo":
        return DEMO_CATALOG, DEMO_HISTORY
    database = PostgresDatabase(settings.database_url)
    return (
        PostgresCatalogRepository(database.connection),
        PostgresHistoryRepository(database.connection),
    )


def utcnow() -> datetime:
    return datetime.now(UTC)
