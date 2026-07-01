import argparse
import asyncio
import json
import sys
from datetime import UTC, datetime

from anime_oscilloscope.config import get_settings
from anime_oscilloscope.connectors import BangumiConnector, MALConnector
from anime_oscilloscope.database import PostgresDatabase
from anime_oscilloscope.domain import SourceCode
from anime_oscilloscope.jobs.discover_bangumi import run as discover_bangumi
from anime_oscilloscope.jobs.match_mal import run as match_mal
from anime_oscilloscope.sync_store import PostgresSyncStore


def current_season() -> tuple[int, int]:
    now = datetime.now(UTC)
    return now.year, (now.month - 1) // 3 + 1


async def run(year: int, quarter: int, limit: int, offset: int) -> dict[str, object]:
    settings = get_settings()
    if settings.repository_backend != "postgres":
        raise RuntimeError("APP_REPOSITORY_BACKEND must be postgres for live synchronization")
    discovery = await discover_bangumi(year, quarter, limit, offset, write=True)
    store = PostgresSyncStore(PostgresDatabase(settings.database_url).connection)
    eligible = [
        item
        for item in discovery["items"]
        if item["eligibility"] == "eligible" and item.get("stored_id")
    ]
    episode_writes = 0
    matched = 0
    sampled = {"bangumi": 0, "mal": 0}
    errors: list[str] = []
    async with BangumiConnector(token=settings.bangumi_token) as bangumi:
        for item in eligible:
            bangumi_id = str(item["bangumi_id"])
            try:
                episodes = await bangumi.fetch_episodes(bangumi_id)
                episode_writes += store.upsert_episodes(str(item["stored_id"]), episodes)
            except Exception as error:  # noqa: BLE001 - continue the remaining catalog
                errors.append(f"episodes {bangumi_id}: {error}")
            if settings.mal_client_id:
                try:
                    await match_mal(bangumi_id, 10, write=True)
                    matched += 1
                except Exception as error:  # noqa: BLE001 - retain Bangumi progress
                    errors.append(f"mal {bangumi_id}: {error}")
        for external_id in store.list_due_mappings(
            SourceCode.BANGUMI, launch_date=settings.tracking_launch_date, now=datetime.now(UTC)
        ):
            try:
                subject = await bangumi.fetch_subject(external_id)
                sampled["bangumi"] += int(store.upsert_mapped_rating(subject))
            except Exception as error:  # noqa: BLE001 - retain other source snapshots
                errors.append(f"bangumi rating {external_id}: {error}")
    if settings.mal_client_id:
        async with MALConnector(client_id=settings.mal_client_id) as mal:
            for external_id in store.list_due_mappings(
                SourceCode.MAL,
                launch_date=settings.tracking_launch_date,
                now=datetime.now(UTC),
            ):
                try:
                    subject = await mal.fetch_subject(external_id)
                    sampled["mal"] += int(store.upsert_mapped_rating(subject))
                except Exception as error:  # noqa: BLE001 - retain other source snapshots
                    errors.append(f"mal rating {external_id}: {error}")
    return {
        "year": year,
        "quarter": quarter,
        "discovered": len(discovery["items"]),
        "catalog_written": discovery["written_count"],
        "episodes_written": episode_writes,
        "mal_matches_processed": matched,
        "ratings_sampled": sampled,
        "failed_count": len(errors) + int(discovery["failed_count"]),
        "errors": [*discovery["errors"], *errors],
    }


def main() -> None:
    default_year, default_quarter = current_season()
    parser = argparse.ArgumentParser(description="Synchronize one seasonal catalog page")
    parser.add_argument("--year", type=int, default=default_year)
    parser.add_argument("--quarter", type=int, choices=(1, 2, 3, 4), default=default_quarter)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--offset", type=int, default=0)
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        result = asyncio.run(run(args.year, args.quarter, args.limit, args.offset))
    except RuntimeError as error:
        parser.exit(2, f"Configuration error: {error}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    if result["failed_count"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
