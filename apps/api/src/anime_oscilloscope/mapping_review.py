from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any, Literal, Protocol

from psycopg.types.json import Jsonb

from anime_oscilloscope.catalog import CatalogRepository
from anime_oscilloscope.config import Settings
from anime_oscilloscope.database import ConnectionFactory, PostgresDatabase
from anime_oscilloscope.domain import SourceCode
from anime_oscilloscope.schemas import (
    MappingAnimeSummary,
    MappingCandidateItem,
    MappingCandidatePage,
    MappingResolutionResponse,
    MappingReviewSummary,
)

Row = Mapping[str, Any]


class MappingReviewRepository(Protocol):
    @property
    def data_mode(self) -> Literal["demo", "live"]: ...

    def list_candidates(
        self,
        *,
        source: SourceCode,
        disposition: str,
        unresolved_only: bool,
        limit: int,
        offset: int,
    ) -> MappingCandidatePage: ...

    def resolve_candidate(
        self,
        candidate_id: int,
        *,
        decision: Literal["approved", "rejected"],
    ) -> MappingResolutionResponse: ...


class DemoMappingReviewRepository:
    data_mode: Literal["demo"] = "demo"

    def __init__(self, catalog_repository: CatalogRepository) -> None:
        self._catalog_repository = catalog_repository

    def list_candidates(
        self,
        *,
        source: SourceCode,
        disposition: str,
        unresolved_only: bool,
        limit: int,
        offset: int,
    ) -> MappingCandidatePage:
        catalog = self._catalog_repository.list_all()
        if not catalog:
            items: list[MappingCandidateItem] = []
        else:
            items = [
                MappingCandidateItem(
                    id=1001,
                    anime=MappingAnimeSummary(
                        id=catalog[0].id,
                        bangumi_id=12345,
                        canonical_name=catalog[0].canonical_name,
                        name_cn=catalog[0].name_cn,
                        image_url=catalog[0].image_url,
                        air_date=catalog[0].air_date,
                        media_type=catalog[0].media_type,
                        status=catalog[0].status,
                        regions=sorted(catalog[0].regions),
                        episode_count=catalog[0].episode_count,
                    ),
                    source=source,
                    external_id="60001",
                    external_url=external_url(source, "60001"),
                    title=f"{catalog[0].canonical_name} Season 1",
                    confidence=0.7421,
                    disposition="review",
                    evidence={
                        "title_similarity": 0.81,
                        "date_similarity": 0.9,
                        "media_similarity": 1,
                        "episode_similarity": 1,
                        "installment_conflict": True,
                        "reasons": ["installment_signature_conflict"],
                    },
                    generated_at=datetime(2026, 7, 21, tzinfo=UTC),
                    resolved_at=None,
                    current_review_status=None,
                )
            ]
        filtered = [
            item
            for item in items
            if item.disposition == disposition and (not unresolved_only or not item.resolved_at)
        ]
        page_items = filtered[offset : offset + limit]
        return MappingCandidatePage(
            data_mode="demo",
            total=len(filtered),
            limit=limit,
            offset=offset,
            summary=MappingReviewSummary(
                source=source,
                unresolved_review_count=len(filtered),
                automatic_count=0,
                rejected_count=0,
                approved_mapping_count=0,
                unmapped_rankable_count=max(len(catalog) - 1, 0),
            ),
            items=page_items,
        )

    def resolve_candidate(
        self,
        candidate_id: int,
        *,
        decision: Literal["approved", "rejected"],
    ) -> MappingResolutionResponse:
        return MappingResolutionResponse(
            data_mode="demo",
            candidate_id=candidate_id,
            decision=decision,
            external_mapping_id=None,
        )


class PostgresMappingReviewRepository:
    data_mode: Literal["live"] = "live"

    def __init__(self, connection_factory: ConnectionFactory) -> None:
        self._connection = connection_factory

    def list_candidates(
        self,
        *,
        source: SourceCode,
        disposition: str,
        unresolved_only: bool,
        limit: int,
        offset: int,
    ) -> MappingCandidatePage:
        unresolved_sql = "and c.resolved_at is null" if unresolved_only else ""
        params = {"source": source, "disposition": disposition, "limit": limit, "offset": offset}
        with self._connection() as connection:
            total = connection.execute(
                f"""select count(*)::int as value
                    from mapping_candidate c
                    where c.source = %(source)s and c.disposition = %(disposition)s
                    {unresolved_sql}""",
                params,
            ).fetchone()
            rows = connection.execute(
                f"""select c.id, c.source, c.external_id, c.title, c.confidence,
                           c.disposition, c.evidence, c.generated_at, c.resolved_at,
                           a.id as anime_id, a.bangumi_id, a.canonical_name, a.name_cn,
                           a.image_url, a.air_date, a.media_type, a.status, a.regions,
                           a.episode_count, m.review_status as current_review_status
                    from mapping_candidate c
                    join anime a on a.id = c.anime_id
                    left join external_mapping m
                      on m.anime_id = c.anime_id and m.source = c.source
                    where c.source = %(source)s and c.disposition = %(disposition)s
                    {unresolved_sql}
                    order by c.confidence desc, c.generated_at desc, c.id desc
                    limit %(limit)s offset %(offset)s""",
                params,
            ).fetchall()
            summary = self._summary(connection, source)
        return MappingCandidatePage(
            data_mode="live",
            total=(total or {}).get("value", 0),
            limit=limit,
            offset=offset,
            summary=summary,
            items=[candidate_from_row(row) for row in rows],
        )

    def resolve_candidate(
        self,
        candidate_id: int,
        *,
        decision: Literal["approved", "rejected"],
    ) -> MappingResolutionResponse:
        with self._connection() as connection:
            candidate = connection.execute(
                """select id, anime_id, source, external_id, confidence, evidence
                   from mapping_candidate where id = %s""",
                (candidate_id,),
            ).fetchone()
            if candidate is None:
                raise LookupError("Mapping candidate not found")
            external_mapping_id = None
            if decision == "approved":
                mapping = connection.execute(
                    """insert into external_mapping
                         (anime_id, source, external_id, confidence, review_status,
                          match_evidence, reviewed_at)
                       values (%s, %s, %s, %s, 'approved', %s, now())
                       on conflict (anime_id, source) do update set
                         external_id = excluded.external_id,
                         confidence = excluded.confidence,
                         review_status = 'approved',
                         match_evidence = excluded.match_evidence,
                         reviewed_at = now(),
                         updated_at = now()
                       returning id""",
                    (
                        candidate["anime_id"],
                        candidate["source"],
                        candidate["external_id"],
                        candidate["confidence"],
                        Jsonb(candidate["evidence"]),
                    ),
                ).fetchone()
                external_mapping_id = mapping["id"] if mapping else None
            connection.execute(
                """update mapping_candidate set disposition = %s, resolved_at = now()
                   where id = %s""",
                ("automatic" if decision == "approved" else "reject", candidate_id),
            )
        return MappingResolutionResponse(
            data_mode="live",
            candidate_id=candidate_id,
            decision=decision,
            external_mapping_id=external_mapping_id,
        )

    def _summary(self, connection: Any, source: SourceCode) -> MappingReviewSummary:
        candidate_counts = connection.execute(
            """select disposition, count(*)::int as value
               from mapping_candidate
               where source = %s and resolved_at is null
               group by disposition""",
            (source,),
        ).fetchall()
        counts = {row["disposition"]: row["value"] for row in candidate_counts}
        approved = connection.execute(
            """select count(*)::int as value from external_mapping
               where source = %s and review_status in ('automatic', 'approved')""",
            (source,),
        ).fetchone()
        unmapped = connection.execute(
            """select count(*)::int as value
               from anime a
               where not a.is_nsfw and not a.is_excluded and a.air_date is not null
                 and exists (select 1 from current_rating cr where cr.anime_id = a.id)
                 and not exists (
                   select 1 from external_mapping m
                   where m.anime_id = a.id and m.source = %s
                     and m.review_status in ('automatic', 'approved')
                 )""",
            (source,),
        ).fetchone()
        return MappingReviewSummary(
            source=source,
            unresolved_review_count=counts.get("review", 0),
            automatic_count=counts.get("automatic", 0),
            rejected_count=counts.get("reject", 0),
            approved_mapping_count=(approved or {}).get("value", 0),
            unmapped_rankable_count=(unmapped or {}).get("value", 0),
        )


def candidate_from_row(row: Row) -> MappingCandidateItem:
    source = SourceCode(row["source"])
    return MappingCandidateItem(
        id=row["id"],
        anime=MappingAnimeSummary(
            id=str(row["anime_id"]),
            bangumi_id=row.get("bangumi_id"),
            canonical_name=row["canonical_name"],
            name_cn=row.get("name_cn"),
            image_url=row.get("image_url"),
            air_date=row.get("air_date"),
            media_type=row["media_type"],
            status=row["status"],
            regions=list(row.get("regions") or []),
            episode_count=row.get("episode_count"),
        ),
        source=source,
        external_id=row["external_id"],
        external_url=external_url(source, row["external_id"]),
        title=row["title"],
        confidence=float(row["confidence"]),
        disposition=row["disposition"],
        evidence=dict(row["evidence"] or {}),
        generated_at=row["generated_at"],
        resolved_at=row.get("resolved_at"),
        current_review_status=row.get("current_review_status"),
    )


def external_url(source: SourceCode, external_id: str) -> str:
    if source is SourceCode.MAL:
        return f"https://myanimelist.net/anime/{external_id}"
    if source is SourceCode.DOUBAN:
        return f"https://movie.douban.com/subject/{external_id}/"
    if source is SourceCode.FILMARKS:
        return f"https://filmarks.com/animes/{external_id}"
    return ""


def create_mapping_review_repository(
    settings: Settings,
    catalog_repository: CatalogRepository,
) -> MappingReviewRepository:
    if settings.repository_backend == "demo":
        return DemoMappingReviewRepository(catalog_repository)
    database = PostgresDatabase(settings.database_url)
    return PostgresMappingReviewRepository(database.connection)
