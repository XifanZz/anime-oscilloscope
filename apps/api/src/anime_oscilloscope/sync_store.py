from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID

from psycopg.types.json import Jsonb

from anime_oscilloscope.database import ConnectionFactory
from anime_oscilloscope.domain import MatchResult, NormalizedAnime, NormalizedEpisode, SourceCode
from anime_oscilloscope.policies import EligibilityDecision, EligibilityStatus
from anime_oscilloscope.sampling import is_sample_due, is_tracking_candidate, sampling_cadence


class PostgresSyncStore:
    """Transactional, idempotent writes used only by scheduled acquisition jobs."""

    def __init__(self, connection_factory: ConnectionFactory) -> None:
        self._connection = connection_factory

    def start_run(self, source: SourceCode, job_type: str, requested_count: int = 0) -> UUID:
        with self._connection() as connection:
            row = connection.execute(
                """insert into sync_run (source, job_type, status, requested_count)
                   values (%s, %s, 'running', %s) returning id""",
                (source, job_type, requested_count),
            ).fetchone()
        if row is None:
            raise RuntimeError("sync_run insert did not return an id")
        return row["id"]

    def finish_run(
        self,
        run_id: UUID,
        *,
        succeeded: int,
        failed: int,
        errors: Sequence[str] = (),
    ) -> None:
        status = "failed" if failed and not succeeded else "partial" if failed else "succeeded"
        with self._connection() as connection:
            connection.execute(
                """update sync_run set status = %s, succeeded_count = %s,
                          failed_count = %s, error_summary = %s, finished_at = now()
                   where id = %s""",
                (status, succeeded, failed, Jsonb({"errors": list(errors)[:20]}), run_id),
            )

    def upsert_bangumi(self, anime: NormalizedAnime, decision: EligibilityDecision) -> str:
        if anime.source is not SourceCode.BANGUMI:
            raise ValueError("primary catalog records must come from Bangumi")
        excluded = decision.status is not EligibilityStatus.ELIGIBLE
        reason = decision.reason if excluded else None
        with self._connection() as connection:
            row = connection.execute(
                """insert into anime (
                     bangumi_id, canonical_name, name_cn, aliases, summary, image_url,
                     air_date, end_date, status, media_type, regions, episode_count, tags,
                     is_nsfw, is_excluded, exclusion_reason, updated_at
                   ) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                             %s, %s, %s, now())
                   on conflict (bangumi_id) do update set
                     canonical_name = excluded.canonical_name, name_cn = excluded.name_cn,
                     aliases = excluded.aliases, summary = excluded.summary,
                     image_url = excluded.image_url, air_date = excluded.air_date,
                     end_date = excluded.end_date, status = excluded.status,
                     media_type = excluded.media_type, regions = excluded.regions,
                     episode_count = excluded.episode_count, tags = excluded.tags,
                     is_nsfw = excluded.is_nsfw, is_excluded = excluded.is_excluded,
                     exclusion_reason = excluded.exclusion_reason, updated_at = now()
                   returning id""",
                (
                    int(anime.external_id), anime.canonical_name, anime.name_cn, anime.aliases,
                    anime.summary, anime.image_url, anime.air_date, anime.end_date, anime.status,
                    anime.media_type, sorted(anime.regions), anime.episode_count, anime.tags,
                    anime.is_nsfw, excluded, reason,
                ),
            ).fetchone()
            if row is None:
                raise RuntimeError("anime upsert did not return an id")
            anime_id = row["id"]
            connection.execute(
                """insert into external_mapping
                     (anime_id, source, external_id, confidence, review_status, match_evidence)
                   values (%s, 'bangumi', %s, 1, 'automatic', '{}'::jsonb)
                   on conflict (anime_id, source) do update set
                     external_id = excluded.external_id, confidence = 1,
                     review_status = 'automatic', updated_at = now()""",
                (anime_id, anime.external_id),
            )
            if anime.rating is not None:
                self._write_rating(connection, anime_id, anime.rating)
        return str(anime_id)

    def upsert_episodes(self, anime_id: str, episodes: Sequence[NormalizedEpisode]) -> int:
        written = 0
        with self._connection() as connection:
            for episode in episodes:
                if episode.source is not SourceCode.BANGUMI:
                    continue
                air_date = (
                    datetime.combine(episode.air_date, datetime.min.time(), tzinfo=UTC)
                    if episode.air_date
                    else None
                )
                connection.execute(
                    """insert into episode
                         (anime_id, bangumi_episode_id, episode_number, title, title_cn, air_date)
                       values (%s, %s, %s, %s, %s, %s)
                       on conflict (bangumi_episode_id) do update set
                         episode_number = excluded.episode_number, title = excluded.title,
                         title_cn = excluded.title_cn, air_date = excluded.air_date,
                         updated_at = now()""",
                    (
                        anime_id, int(episode.external_id), episode.episode_number,
                        episode.title, episode.title_cn, air_date,
                    ),
                )
                written += 1
        return written

    def record_match_result(self, bangumi_id: str, result: MatchResult) -> None:
        with self._connection() as connection:
            anime_row = connection.execute(
                "select id from anime where bangumi_id = %s", (int(bangumi_id),)
            ).fetchone()
            if anime_row is None:
                raise LookupError(f"Bangumi subject {bangumi_id} is not stored")
            anime_id = anime_row["id"]
            for candidate in result.candidates:
                connection.execute(
                    """insert into mapping_candidate
                         (anime_id, source, external_id, title, confidence, disposition, evidence)
                       values (%s, %s, %s, %s, %s, %s, %s)
                       on conflict (anime_id, source, external_id) do update set
                         title = excluded.title, confidence = excluded.confidence,
                         disposition = excluded.disposition, evidence = excluded.evidence,
                         generated_at = now(), resolved_at = null""",
                    (
                        anime_id, candidate.source, candidate.external_id, candidate.title,
                        candidate.confidence, candidate.disposition,
                        Jsonb(candidate.evidence.model_dump(mode="json")),
                    ),
                )
            selected = result.selected
            if selected is not None:
                connection.execute(
                    """insert into external_mapping
                         (anime_id, source, external_id, confidence, review_status, match_evidence)
                       values (%s, %s, %s, %s, 'automatic', %s)
                       on conflict (anime_id, source) do update set
                         external_id = excluded.external_id, confidence = excluded.confidence,
                         review_status = 'automatic', match_evidence = excluded.match_evidence,
                         updated_at = now()""",
                    (
                        anime_id, selected.source, selected.external_id, selected.confidence,
                        Jsonb(selected.evidence.model_dump(mode="json")),
                    ),
                )

    def upsert_mapped_rating(self, anime: NormalizedAnime) -> bool:
        if anime.rating is None:
            return False
        with self._connection() as connection:
            mapping = connection.execute(
                """select anime_id from external_mapping
                   where source = %s and external_id = %s
                   and review_status in ('automatic', 'approved')""",
                (anime.source, anime.external_id),
            ).fetchone()
            if mapping is None:
                return False
            self._write_rating(connection, mapping["anime_id"], anime.rating)
            if anime.source is SourceCode.MAL:
                connection.execute(
                    """update anime set status = %s, end_date = coalesce(%s, end_date),
                              episode_count = coalesce(%s, episode_count), updated_at = now()
                       where id = %s""",
                    (anime.status, anime.end_date, anime.episode_count, mapping["anime_id"]),
                )
        return True

    def list_due_mappings(
        self, source: SourceCode, *, launch_date: date, now: datetime
    ) -> list[str]:
        with self._connection() as connection:
            rows = connection.execute(
                """select m.external_id, a.status, a.end_date, a.air_date,
                          max(s.sampled_at) as last_sampled_at
                   from external_mapping m
                   join anime a on a.id = m.anime_id
                   left join rating_snapshot s on s.anime_id = a.id and s.source = m.source
                   where m.source = %s and m.review_status in ('automatic', 'approved')
                     and not a.is_nsfw and not a.is_excluded and a.air_date is not null
                   group by m.external_id, a.status, a.end_date, a.air_date""",
                (source,),
            ).fetchall()
        return due_external_ids(rows, launch_date=launch_date, now=now)

    def list_unmatched_bangumi_ids_for_review(
        self,
        *,
        source: SourceCode,
        limit: int,
        offset: int = 0,
    ) -> list[str]:
        if source is SourceCode.BANGUMI:
            raise ValueError("Bangumi is the primary source and cannot be matched to itself")
        with self._connection() as connection:
            rows = connection.execute(
                """select a.bangumi_id
                   from anime a
                   where a.bangumi_id is not null
                     and not a.is_nsfw and not a.is_excluded and a.air_date is not null
                     and exists (
                       select 1 from current_rating cr where cr.anime_id = a.id
                     )
                     and not exists (
                       select 1 from external_mapping m
                       where m.anime_id = a.id and m.source = %s
                         and m.review_status in ('automatic', 'approved')
                     )
                     and not exists (
                       select 1 from mapping_candidate c
                       where c.anime_id = a.id and c.source = %s
                         and c.resolved_at is null
                         and c.disposition in ('automatic', 'review')
                     )
                   order by a.air_date desc, a.updated_at desc
                   limit %s offset %s""",
                (source, source, limit, offset),
            ).fetchall()
        return [str(row["bangumi_id"]) for row in rows]

    def initialize_backfill(
        self,
        *,
        start_year: int,
        end_year: int,
        reset: bool = False,
    ) -> dict[str, Any]:
        with self._connection() as connection:
            if reset:
                connection.execute(
                    "delete from catalog_backfill_state where source = 'bangumi'"
                )
            connection.execute(
                """insert into catalog_backfill_state
                     (source, start_year, end_year, next_year, next_offset)
                   values ('bangumi', %s, %s, %s, 0)
                   on conflict (source) do update set
                     end_year = greatest(catalog_backfill_state.end_year, excluded.end_year),
                     completed = case
                       when catalog_backfill_state.next_year <= excluded.end_year then false
                       else catalog_backfill_state.completed
                     end,
                     updated_at = now()""",
                (start_year, end_year, start_year),
            )
            row = connection.execute(
                "select * from catalog_backfill_state where source = 'bangumi'"
            ).fetchone()
        if row is None:
            raise RuntimeError("catalog backfill state was not initialized")
        return dict(row)

    def advance_backfill(
        self,
        *,
        next_year: int,
        next_offset: int,
        discovered: int,
        completed: bool,
        error: str | None = None,
    ) -> None:
        with self._connection() as connection:
            connection.execute(
                """update catalog_backfill_state set
                     next_year = %s, next_offset = %s,
                     processed_pages = processed_pages + 1,
                     discovered_count = discovered_count + %s,
                     completed = %s, last_error = %s, updated_at = now()
                   where source = 'bangumi'""",
                (next_year, next_offset, discovered, completed, error),
            )

    def fail_backfill(self, error: str) -> None:
        with self._connection() as connection:
            connection.execute(
                """update catalog_backfill_state
                   set last_error = %s, updated_at = now()
                   where source = 'bangumi'""",
                (error[:2000],),
            )

    def mark_connector(self, source: SourceCode, *, error: str | None = None) -> None:
        with self._connection() as connection:
            if error:
                connection.execute(
                    """update source_connector set last_attempt_at = now(), last_error = %s,
                              updated_at = now() where code = %s""",
                    (error[:2000], source),
                )
            else:
                connection.execute(
                    """update source_connector set enabled = true, disabled_reason = null,
                              last_attempt_at = now(), last_success_at = now(), last_error = null,
                              updated_at = now() where code = %s""",
                    (source,),
                )

    @staticmethod
    def _write_rating(connection: Any, anime_id: Any, rating: Any) -> None:
        observed_at = rating.sampled_at or datetime.now(UTC)
        sampled_at = datetime.combine(observed_at.date(), datetime.min.time(), tzinfo=UTC)
        connection.execute(
            """insert into current_rating
                 (anime_id, source, score, rating_count, source_rank, sampled_at)
               values (%s, %s, %s, %s, %s, %s)
               on conflict (anime_id, source) do update set
                 score = excluded.score, rating_count = excluded.rating_count,
                 source_rank = excluded.source_rank, sampled_at = excluded.sampled_at""",
            (
                anime_id, rating.source, rating.score, rating.rating_count,
                rating.source_rank, sampled_at,
            ),
        )
        connection.execute(
            """insert into rating_snapshot
                 (anime_id, source, score, rating_count, source_rank,
                  rating_distribution, sampled_at)
               values (%s, %s, %s, %s, %s, %s, %s)
               on conflict (anime_id, source, sampled_at) do nothing""",
            (
                anime_id, rating.source, rating.score, rating.rating_count,
                rating.source_rank, Jsonb(rating.distribution) if rating.distribution else None,
                sampled_at,
            ),
        )


def due_external_ids(
    rows: Sequence[dict[str, Any]], *, launch_date: date, now: datetime
) -> list[str]:
    due = []
    for row in rows:
        if not is_tracking_candidate(row["air_date"], launch_date):
            continue
        cadence = sampling_cadence(
            status=row["status"], end_date=row.get("end_date"), today=now.date()
        )
        if is_sample_due(
            cadence=cadence, last_sampled_at=row.get("last_sampled_at"), now=now
        ):
            due.append(str(row["external_id"]))
    return due
