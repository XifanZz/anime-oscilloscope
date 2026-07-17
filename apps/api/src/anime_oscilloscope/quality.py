from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any, Literal, Protocol

from anime_oscilloscope.catalog import CatalogAnime, CatalogRepository
from anime_oscilloscope.config import Settings
from anime_oscilloscope.database import ConnectionFactory, PostgresDatabase
from anime_oscilloscope.domain import SourceCode
from anime_oscilloscope.schemas import (
    BackfillQuality,
    ConnectorQuality,
    DataQualityResponse,
    SyncRunSummary,
)

Row = Mapping[str, Any]


class DataQualityRepository(Protocol):
    @property
    def data_mode(self) -> Literal["demo", "live"]: ...

    def get(self) -> DataQualityResponse: ...


class DemoDataQualityRepository:
    data_mode: Literal["demo"] = "demo"

    def __init__(self, catalog_repository: CatalogRepository) -> None:
        self._catalog_repository = catalog_repository

    def get(self) -> DataQualityResponse:
        items = self._catalog_repository.list_all()
        return quality_from_catalog(
            items,
            data_mode="demo",
            notes=[
                "当前为演示数据模式；公开页面会在 API 不可用时回退到静态样例。",
                "真实数据模式下会显示 Supabase 中的采集、匹配和回填状态。",
            ],
        )


class PostgresDataQualityRepository:
    data_mode: Literal["live"] = "live"

    def __init__(self, connection_factory: ConnectionFactory) -> None:
        self._connection = connection_factory

    def get(self) -> DataQualityResponse:
        with self._connection() as connection:
            totals = connection.execute(
                """select
                     count(*)::int as total_anime,
                     count(*) filter (
                       where not is_nsfw and not is_excluded and air_date is not null
                     )::int as eligible_anime,
                     count(*) filter (where is_excluded)::int as excluded_anime,
                     count(*) filter (where is_nsfw)::int as nsfw_anime,
                     max(updated_at) as latest_catalog_updated_at
                   from anime"""
            ).fetchone() or {}
            rating_rows = connection.execute(
                """select cr.source, count(distinct cr.anime_id)::int as rated_count,
                          max(cr.sampled_at) as latest_sampled_at
                   from current_rating cr
                   join anime a on a.id = cr.anime_id
                   where not a.is_nsfw and not a.is_excluded and a.air_date is not null
                   group by cr.source"""
            ).fetchall()
            mapping_rows = connection.execute(
                """select m.source, count(distinct m.anime_id)::int as mapped_count
                   from external_mapping m
                   join anime a on a.id = m.anime_id
                   where m.review_status in ('automatic', 'approved')
                     and not a.is_nsfw and not a.is_excluded and a.air_date is not null
                   group by m.source"""
            ).fetchall()
            rankable = connection.execute(
                """select count(*)::int as value
                   from anime a
                   where not a.is_nsfw and not a.is_excluded and a.air_date is not null
                     and exists (
                       select 1 from current_rating cr where cr.anime_id = a.id
                     )"""
            ).fetchone()
            both_core = connection.execute(
                """select count(*)::int as value
                   from anime a
                   where not a.is_nsfw and not a.is_excluded and a.air_date is not null
                     and exists (
                       select 1 from current_rating cr
                       where cr.anime_id = a.id and cr.source = 'bangumi'
                     )
                     and exists (
                       select 1 from current_rating cr
                       where cr.anime_id = a.id and cr.source = 'mal'
                     )"""
            ).fetchone()
            missing_mal = connection.execute(
                """select count(*)::int as value
                   from anime a
                   where not a.is_nsfw and not a.is_excluded and a.air_date is not null
                     and not exists (
                       select 1 from current_rating cr
                       where cr.anime_id = a.id and cr.source = 'mal'
                     )"""
            ).fetchone()
            connectors = self._read_connectors(connection, rating_rows, mapping_rows)
            backfill = self._read_backfill(connection)
            recent_runs = self._read_recent_runs(connection)

        rated_counts = {SourceCode(row["source"]): row["rated_count"] for row in rating_rows}
        latest_rating_sampled_at = max(
            (row["latest_sampled_at"] for row in rating_rows if row["latest_sampled_at"]),
            default=None,
        )
        notes = [
            "MAL 缺失表示该条目尚未完成高置信度自动匹配或人工复核，不会被当作 0 分。",
            "历史回填采用断点续跑；榜单数量会随 GitHub Actions 定时任务继续增加。",
        ]
        if backfill and not backfill.completed:
            notes.append(f"Bangumi 历史目录正在回填，下一批将从 {backfill.next_year} 年继续。")

        return DataQualityResponse(
            data_mode="live",
            total_anime=totals.get("total_anime", 0),
            eligible_anime=totals.get("eligible_anime", 0),
            rankable_anime=(rankable or {}).get("value", 0),
            excluded_anime=totals.get("excluded_anime", 0),
            nsfw_anime=totals.get("nsfw_anime", 0),
            with_bangumi_rating=rated_counts.get(SourceCode.BANGUMI, 0),
            with_mal_rating=rated_counts.get(SourceCode.MAL, 0),
            with_both_core_sources=(both_core or {}).get("value", 0),
            missing_mal=(missing_mal or {}).get("value", 0),
            latest_rating_sampled_at=latest_rating_sampled_at,
            latest_catalog_updated_at=totals.get("latest_catalog_updated_at"),
            connectors=connectors,
            backfill=backfill,
            recent_runs=recent_runs,
            notes=notes,
        )

    def _read_connectors(
        self,
        connection: Any,
        rating_rows: Sequence[Row],
        mapping_rows: Sequence[Row],
    ) -> list[ConnectorQuality]:
        rated = {SourceCode(row["source"]): row for row in rating_rows}
        mapped = {SourceCode(row["source"]): row["mapped_count"] for row in mapping_rows}
        rows = connection.execute(
            """select code, label, enabled, disabled_reason,
                      last_success_at, last_attempt_at, last_error
               from source_connector order by code"""
        ).fetchall()
        return [
            connector_quality_from_row(
                row,
                rated_count=(rated.get(SourceCode(row["code"])) or {}).get("rated_count", 0),
                mapped_count=mapped.get(SourceCode(row["code"]), 0),
                latest_sampled_at=(rated.get(SourceCode(row["code"])) or {}).get(
                    "latest_sampled_at"
                ),
            )
            for row in rows
        ]

    def _read_backfill(self, connection: Any) -> BackfillQuality | None:
        exists = connection.execute(
            "select to_regclass('public.catalog_backfill_state') as table_name"
        ).fetchone()
        if not exists or exists["table_name"] is None:
            return None
        row = connection.execute(
            "select * from catalog_backfill_state where source = 'bangumi'"
        ).fetchone()
        if row is None:
            return None
        return backfill_quality_from_row(row)

    def _read_recent_runs(self, connection: Any) -> list[SyncRunSummary]:
        return [
            SyncRunSummary(**row)
            for row in connection.execute(
                """select source, job_type, status, succeeded_count, failed_count,
                          started_at, finished_at
                   from sync_run order by started_at desc limit 5"""
            ).fetchall()
        ]


def quality_from_catalog(
    items: Sequence[CatalogAnime],
    *,
    data_mode: Literal["demo", "live"],
    notes: list[str] | None = None,
) -> DataQualityResponse:
    total = len(items)
    rankable = sum(1 for item in items if item.ratings)
    with_bangumi = sum(1 for item in items if has_rating(item, SourceCode.BANGUMI))
    with_mal = sum(1 for item in items if has_rating(item, SourceCode.MAL))
    both = sum(
        1
        for item in items
        if has_rating(item, SourceCode.BANGUMI) and has_rating(item, SourceCode.MAL)
    )
    latest_rating = max(
        (rating.sampled_at for item in items for rating in item.ratings if rating.sampled_at),
        default=None,
    )
    latest_catalog = max((item.updated_at for item in items), default=None)
    return DataQualityResponse(
        data_mode=data_mode,
        total_anime=total,
        eligible_anime=total,
        rankable_anime=rankable,
        excluded_anime=0,
        nsfw_anime=0,
        with_bangumi_rating=with_bangumi,
        with_mal_rating=with_mal,
        with_both_core_sources=both,
        missing_mal=max(total - with_mal, 0),
        latest_rating_sampled_at=latest_rating,
        latest_catalog_updated_at=latest_catalog,
        connectors=[
            demo_connector_quality(SourceCode.BANGUMI, "Bangumi", with_bangumi, latest_rating),
            demo_connector_quality(SourceCode.MAL, "MyAnimeList", with_mal, latest_rating),
            demo_connector_quality(SourceCode.DOUBAN, "豆瓣", 0, None, enabled=False),
            demo_connector_quality(SourceCode.FILMARKS, "Filmarks", 0, None, enabled=False),
        ],
        notes=notes or [],
    )


def has_rating(item: CatalogAnime, source: SourceCode) -> bool:
    return any(rating.source == source for rating in item.ratings)


def demo_connector_quality(
    source: SourceCode,
    label: str,
    rated_count: int,
    latest_sampled_at: datetime | None,
    *,
    enabled: bool = True,
) -> ConnectorQuality:
    return ConnectorQuality(
        source=source,
        label=label,
        enabled=enabled,
        status="fresh" if enabled and rated_count else "unavailable",
        mapped_count=rated_count,
        rated_count=rated_count,
        latest_sampled_at=latest_sampled_at,
        last_success_at=latest_sampled_at,
        last_attempt_at=latest_sampled_at,
        message=None if enabled else "Requires written authorization",
    )


def connector_quality_from_row(
    row: Row,
    *,
    rated_count: int,
    mapped_count: int,
    latest_sampled_at: datetime | None,
) -> ConnectorQuality:
    last_success_at = row.get("last_success_at")
    last_attempt_at = row.get("last_attempt_at")
    last_error = row.get("last_error") or row.get("disabled_reason")
    if not row.get("enabled"):
        status: Literal["fresh", "stale", "unavailable"] = "unavailable"
    elif (
        last_error
        and last_attempt_at
        and (last_success_at is None or last_attempt_at >= last_success_at)
    ):
        status = "stale"
    elif last_success_at or latest_sampled_at:
        status = "fresh"
    else:
        status = "unavailable"
    return ConnectorQuality(
        source=SourceCode(row["code"]),
        label=row["label"],
        enabled=bool(row["enabled"]),
        status=status,
        mapped_count=mapped_count,
        rated_count=rated_count,
        latest_sampled_at=latest_sampled_at,
        last_success_at=last_success_at,
        last_attempt_at=last_attempt_at,
        message=last_error,
    )


def backfill_quality_from_row(row: Row) -> BackfillQuality:
    total_years = max(row["end_year"] - row["start_year"] + 1, 1)
    completed_years = row["end_year"] - row["start_year"] + 1
    if not row["completed"]:
        completed_years = max(row["next_year"] - row["start_year"], 0)
    progress = 100 if row["completed"] else min(99, round(100 * completed_years / total_years))
    return BackfillQuality(
        source=SourceCode(row["source"]),
        start_year=row["start_year"],
        end_year=row["end_year"],
        next_year=row["next_year"],
        next_offset=row["next_offset"],
        processed_pages=row["processed_pages"],
        discovered_count=row["discovered_count"],
        completed=row["completed"],
        progress_percent=progress,
        last_error=row.get("last_error"),
        updated_at=row["updated_at"],
    )


def create_quality_repository(
    settings: Settings,
    catalog_repository: CatalogRepository,
) -> DataQualityRepository:
    if settings.repository_backend == "demo":
        return DemoDataQualityRepository(catalog_repository)
    database = PostgresDatabase(settings.database_url)
    return PostgresDataQualityRepository(database.connection)


def utcnow() -> datetime:
    return datetime.now(UTC)
