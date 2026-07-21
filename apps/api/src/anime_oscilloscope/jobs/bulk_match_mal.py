import argparse
import asyncio
import json
import sys
from typing import Any

from anime_oscilloscope.config import get_settings
from anime_oscilloscope.connectors import BangumiConnector, MALConnector
from anime_oscilloscope.database import PostgresDatabase
from anime_oscilloscope.domain import SourceCode
from anime_oscilloscope.matching import CrossSourceMatcher
from anime_oscilloscope.sync_store import PostgresSyncStore


async def run(
    *,
    limit: int,
    offset: int = 0,
    candidate_limit: int = 10,
    write: bool = False,
) -> dict[str, Any]:
    settings = get_settings()
    if not settings.mal_client_id:
        raise RuntimeError("APP_MAL_CLIENT_ID is not configured")
    if write and settings.repository_backend != "postgres":
        raise RuntimeError("Bulk MAL matching writes require APP_REPOSITORY_BACKEND=postgres")

    store = PostgresSyncStore(PostgresDatabase(settings.database_url).connection)
    bangumi_ids = store.list_unmatched_bangumi_ids_for_review(
        source=SourceCode.MAL,
        limit=limit,
        offset=offset,
    )
    run_id = None
    if write:
        run_id = store.start_run(SourceCode.MAL, "bulk_cross_source_match", len(bangumi_ids))

    succeeded = 0
    failed = 0
    rating_written = 0
    errors: list[str] = []
    details: list[dict[str, Any]] = []
    async with (
        BangumiConnector(token=settings.bangumi_token) as bangumi,
        MALConnector(client_id=settings.mal_client_id) as mal,
    ):
        matcher = CrossSourceMatcher(mal)
        for bangumi_id in bangumi_ids:
            try:
                primary = await bangumi.fetch_subject(bangumi_id)
                result = await matcher.match(primary, limit=candidate_limit)
                selected_anime = (
                    await mal.fetch_subject(result.selected.external_id)
                    if result.selected
                    else None
                )
                if write:
                    store.record_match_result(bangumi_id, result)
                    if selected_anime and store.upsert_mapped_rating(selected_anime):
                        rating_written += 1
                succeeded += 1
                details.append(
                    {
                        "bangumi_id": bangumi_id,
                        "candidate_count": len(result.candidates),
                        "selected": result.selected.external_id if result.selected else None,
                        "top_confidence": (
                            result.candidates[0].confidence if result.candidates else None
                        ),
                    }
                )
            except Exception as error:  # pragma: no cover - exercised in production jobs
                failed += 1
                errors.append(f"{bangumi_id}: {error}")
    if write and run_id is not None:
        store.finish_run(run_id, succeeded=succeeded, failed=failed, errors=errors)
        store.mark_connector(SourceCode.MAL, error="; ".join(errors) if errors else None)
    return {
        "requested_limit": limit,
        "offset": offset,
        "candidate_limit": candidate_limit,
        "selected_bangumi_ids": bangumi_ids,
        "succeeded": succeeded,
        "failed": failed,
        "rating_written": rating_written,
        "writes_performed": write,
        "errors": errors[:20],
        "details": details,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Bulk Bangumi to MAL candidate matching")
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--candidate-limit", type=int, default=10)
    parser.add_argument(
        "--write",
        action="store_true",
        help="Persist candidates into APP_DATABASE_URL",
    )
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        result = asyncio.run(
            run(
                limit=args.limit,
                offset=args.offset,
                candidate_limit=args.candidate_limit,
                write=args.write,
            )
        )
    except RuntimeError as exc:
        parser.exit(2, f"Configuration error: {exc}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
