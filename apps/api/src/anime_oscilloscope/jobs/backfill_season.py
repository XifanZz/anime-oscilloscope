import argparse
import asyncio
import json
import sys
from datetime import UTC, datetime

from anime_oscilloscope.config import get_settings
from anime_oscilloscope.connectors import BangumiConnector
from anime_oscilloscope.database import PostgresDatabase
from anime_oscilloscope.domain import MediaType, SourceCode
from anime_oscilloscope.jobs.discover_bangumi import quarter_bounds
from anime_oscilloscope.policies import EligibilityStatus, evaluate_eligibility
from anime_oscilloscope.sync_store import PostgresSyncStore


def next_offset(
    *,
    offset: int,
    item_count: int,
    total: int | None,
    limit: int,
) -> tuple[int, bool]:
    """Return the next Bangumi discovery offset and whether the season is complete."""
    if item_count <= 0:
        return offset, True
    candidate = offset + item_count
    if total is not None and candidate >= total:
        return candidate, True
    if item_count < limit:
        return candidate, True
    return candidate, False


async def run(
    *,
    year: int,
    quarter: int,
    limit: int,
    start_offset: int = 0,
    max_pages: int = 10,
    throttle_seconds: float = 0.75,
) -> dict[str, object]:
    """Backfill one selected Bangumi season without MAL matching or global sampling."""
    if not 1900 <= year <= datetime.now(UTC).year + 2:
        raise ValueError("year must be between 1900 and two years after the current year")
    if not 1 <= limit <= 200:
        raise ValueError("limit must be between 1 and 200")
    if start_offset < 0:
        raise ValueError("start_offset must be non-negative")
    if not 1 <= max_pages <= 50:
        raise ValueError("max_pages must be between 1 and 50")

    settings = get_settings()
    if settings.repository_backend != "postgres":
        raise RuntimeError("APP_REPOSITORY_BACKEND must be postgres for seasonal backfill")

    start_date, end_date = quarter_bounds(year, quarter)
    store = PostgresSyncStore(PostgresDatabase(settings.database_url).connection)
    run_id = store.start_run(SourceCode.BANGUMI, "seasonal_catalog_backfill", limit * max_pages)

    offset = start_offset
    pages = 0
    discovered = 0
    written = 0
    eligible = 0
    excluded = 0
    jp_tv = 0
    total: int | None = None
    completed = False
    errors: list[str] = []

    try:
        async with BangumiConnector(token=settings.bangumi_token) as connector:
            while pages < max_pages:
                page = await connector.discover(
                    start_date=start_date,
                    end_date=end_date,
                    limit=limit,
                    offset=offset,
                    sort="heat",
                )
                total = page.total
                for anime in page.items:
                    decision = evaluate_eligibility(anime)
                    try:
                        store.upsert_bangumi(anime, decision)
                        written += 1
                        if decision.status is EligibilityStatus.ELIGIBLE:
                            eligible += 1
                        else:
                            excluded += 1
                        if anime.media_type is MediaType.TV and "JP" in anime.regions:
                            jp_tv += 1
                    except Exception as error:  # noqa: BLE001 - preserve partial season progress
                        errors.append(f"{anime.external_id}: {error}")
                discovered += len(page.items)
                pages += 1
                offset, completed = next_offset(
                    offset=offset,
                    item_count=len(page.items),
                    total=page.total,
                    limit=page.limit,
                )
                if completed:
                    break
                if throttle_seconds:
                    await asyncio.sleep(throttle_seconds)
    except Exception as error:
        store.finish_run(
            run_id,
            succeeded=written,
            failed=max(1, len(errors)),
            errors=[*errors, str(error)],
        )
        raise

    store.finish_run(run_id, succeeded=written, failed=len(errors), errors=errors)
    store.mark_connector(SourceCode.BANGUMI, error="; ".join(errors[:3]) if errors else None)
    return {
        "status": "completed" if completed else "in_progress",
        "year": year,
        "quarter": quarter,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "sort": "heat",
        "total": total,
        "pages_processed": pages,
        "discovered_count": discovered,
        "items_written": written,
        "eligible_count": eligible,
        "excluded_count": excluded,
        "jp_tv_count_in_processed_pages": jp_tv,
        "failed_count": len(errors),
        "next_offset": offset,
        "errors": errors[:20],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill one Bangumi season catalog")
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--quarter", type=int, choices=(1, 2, 3, 4), required=True)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--start-offset", type=int, default=0)
    parser.add_argument("--max-pages", type=int, default=10)
    parser.add_argument("--throttle-seconds", type=float, default=0.75)
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        result = asyncio.run(
            run(
                year=args.year,
                quarter=args.quarter,
                limit=args.limit,
                start_offset=args.start_offset,
                max_pages=args.max_pages,
                throttle_seconds=args.throttle_seconds,
            )
        )
    except RuntimeError as error:
        parser.exit(2, f"Configuration error: {error}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    if result.get("failed_count"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
