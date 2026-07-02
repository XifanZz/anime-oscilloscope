import argparse
import asyncio
import json
import sys
from datetime import UTC, date, datetime

from anime_oscilloscope.config import get_settings
from anime_oscilloscope.connectors import BangumiConnector
from anime_oscilloscope.database import PostgresDatabase
from anime_oscilloscope.domain import SourceCode
from anime_oscilloscope.policies import evaluate_eligibility
from anime_oscilloscope.sync_store import PostgresSyncStore


def next_position(
    *,
    year: int,
    offset: int,
    item_count: int,
    total: int,
    end_year: int,
) -> tuple[int, int, bool]:
    next_offset = offset + item_count
    if item_count and next_offset < total:
        return year, next_offset, False
    next_year = year + 1
    return next_year, 0, next_year > end_year


async def run(
    *,
    start_year: int,
    end_year: int,
    page_size: int,
    max_pages: int,
    reset: bool = False,
    throttle_seconds: float = 0.75,
) -> dict[str, object]:
    if not 1900 <= start_year <= end_year <= datetime.now(UTC).year:
        raise ValueError("backfill years must be between 1900 and the current year")
    if not 1 <= page_size <= 200:
        raise ValueError("page_size must be between 1 and 200")
    if not 1 <= max_pages <= 50:
        raise ValueError("max_pages must be between 1 and 50")

    settings = get_settings()
    if settings.repository_backend != "postgres":
        raise RuntimeError("APP_REPOSITORY_BACKEND must be postgres for catalog backfill")
    store = PostgresSyncStore(PostgresDatabase(settings.database_url).connection)
    state = store.initialize_backfill(
        start_year=start_year,
        end_year=end_year,
        reset=reset,
    )
    if state["completed"]:
        return {
            "status": "already_completed",
            "next_year": state["next_year"],
            "processed_pages": state["processed_pages"],
            "discovered_count": state["discovered_count"],
        }

    run_id = store.start_run("bangumi", "historical_catalog_backfill", max_pages * page_size)
    year = int(state["next_year"])
    offset = int(state["next_offset"])
    pages = 0
    written = 0
    excluded = 0
    errors: list[str] = []
    completed = False

    try:
        async with BangumiConnector(token=settings.bangumi_token) as connector:
            while pages < max_pages and year <= end_year:
                page = await connector.discover(
                    start_date=date(year, 1, 1),
                    end_date=date(year + 1, 1, 1),
                    limit=page_size,
                    offset=offset,
                )
                page_errors: list[str] = []
                for anime in page.items:
                    decision = evaluate_eligibility(anime)
                    try:
                        store.upsert_bangumi(anime, decision)
                        written += 1
                        excluded += int(decision.status.value != "eligible")
                    except Exception as error:  # noqa: BLE001 - keep page progress idempotent
                        page_errors.append(f"{anime.external_id}: {error}")
                next_year, next_offset, completed = next_position(
                    year=year,
                    offset=offset,
                    item_count=len(page.items),
                    total=page.total,
                    end_year=end_year,
                )
                errors.extend(page_errors)
                store.advance_backfill(
                    next_year=next_year,
                    next_offset=next_offset,
                    discovered=len(page.items),
                    completed=completed,
                    error="; ".join(page_errors[:3]) if page_errors else None,
                )
                pages += 1
                year, offset = next_year, next_offset
                if completed:
                    break
                if throttle_seconds:
                    await asyncio.sleep(throttle_seconds)
    except Exception as error:
        store.fail_backfill(str(error))
        store.finish_run(
            run_id,
            succeeded=written,
            failed=max(1, len(errors)),
            errors=[*errors, str(error)],
        )
        raise

    store.finish_run(run_id, succeeded=written, failed=len(errors), errors=errors)
    store.mark_connector(
        SourceCode.BANGUMI,
        error="; ".join(errors[:3]) if errors else None,
    )
    return {
        "status": "completed" if completed else "in_progress",
        "pages_processed": pages,
        "items_written": written,
        "items_excluded": excluded,
        "failed_count": len(errors),
        "next_year": year,
        "next_offset": offset,
        "errors": errors[:20],
    }


def main() -> None:
    current_year = datetime.now(UTC).year
    parser = argparse.ArgumentParser(description="Resume the full Bangumi history backfill")
    parser.add_argument("--start-year", type=int, default=1917)
    parser.add_argument("--end-year", type=int, default=current_year)
    parser.add_argument("--page-size", type=int, default=100)
    parser.add_argument("--max-pages", type=int, default=10)
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--throttle-seconds", type=float, default=0.75)
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    result = asyncio.run(
        run(
            start_year=args.start_year,
            end_year=args.end_year,
            page_size=args.page_size,
            max_pages=args.max_pages,
            reset=args.reset,
            throttle_seconds=args.throttle_seconds,
        )
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    if result.get("failed_count"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
