import argparse
import asyncio
import json
import sys
from datetime import date

from anime_oscilloscope.config import get_settings
from anime_oscilloscope.connectors import BangumiConnector
from anime_oscilloscope.database import PostgresDatabase
from anime_oscilloscope.policies import evaluate_eligibility
from anime_oscilloscope.sync_store import PostgresSyncStore


def quarter_bounds(year: int, quarter: int) -> tuple[date, date]:
    if quarter not in {1, 2, 3, 4}:
        raise ValueError("quarter must be 1, 2, 3, or 4")
    start_month = 1 + (quarter - 1) * 3
    start = date(year, start_month, 1)
    end = date(year + 1, 1, 1) if quarter == 4 else date(year, start_month + 3, 1)
    return start, end


async def run(
    year: int, quarter: int, limit: int, offset: int, *, write: bool = False
) -> dict[str, object]:
    start, end = quarter_bounds(year, quarter)
    settings = get_settings()
    async with BangumiConnector(token=settings.bangumi_token) as connector:
        page = await connector.discover(
            start_date=start,
            end_date=end,
            limit=limit,
            offset=offset,
        )
    store = (
        PostgresSyncStore(PostgresDatabase(settings.database_url).connection) if write else None
    )
    run_id = (
        store.start_run("bangumi", "seasonal_discovery", page.total or len(page.items))
        if store
        else None
    )
    items = []
    succeeded = 0
    errors: list[str] = []
    for anime in page.items:
        decision = evaluate_eligibility(anime)
        stored_id = None
        if store:
            try:
                stored_id = store.upsert_bangumi(anime, decision)
                succeeded += 1
            except Exception as error:  # noqa: BLE001 - batch jobs must retain partial progress
                errors.append(f"{anime.external_id}: {error}")
        items.append(
            {
                "bangumi_id": anime.external_id,
                "title": anime.name_cn or anime.canonical_name,
                "air_date": anime.air_date.isoformat() if anime.air_date else None,
                "media_type": anime.media_type,
                "regions": sorted(anime.regions),
                "score": anime.rating.score if anime.rating else None,
                "votes": anime.rating.rating_count if anime.rating else None,
                "eligibility": decision.status,
                "eligibility_reason": decision.reason,
                "stored_id": stored_id,
            }
        )
    result = {
        "source": "bangumi",
        "query": {
            "year": year,
            "quarter": quarter,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
        },
        "total": page.total,
        "limit": page.limit,
        "offset": page.offset,
        "items": items,
        "writes_performed": write,
        "written_count": succeeded,
        "failed_count": len(errors),
        "errors": errors,
    }
    if store and run_id:
        store.finish_run(run_id, succeeded=succeeded, failed=len(errors), errors=errors)
        store.mark_connector("bangumi", error="; ".join(errors[:3]) if errors else None)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Bangumi seasonal discovery")
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--quarter", type=int, choices=(1, 2, 3, 4), required=True)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--write", action="store_true", help="Persist into APP_DATABASE_URL")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    result = asyncio.run(run(args.year, args.quarter, args.limit, args.offset, write=args.write))
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
