import argparse
import asyncio
import json
import sys

from anime_oscilloscope.config import get_settings
from anime_oscilloscope.connectors import BangumiConnector, MALConnector
from anime_oscilloscope.database import PostgresDatabase
from anime_oscilloscope.matching import CrossSourceMatcher
from anime_oscilloscope.sync_store import PostgresSyncStore


async def run(bangumi_id: str, limit: int, *, write: bool = False) -> dict[str, object]:
    settings = get_settings()
    if not settings.mal_client_id:
        raise RuntimeError(
            "APP_MAL_CLIENT_ID is not configured. Create a MAL API client and store its ID "
            "in the local .env file; never commit the value."
        )
    async with (
        BangumiConnector(token=settings.bangumi_token) as bangumi,
        MALConnector(client_id=settings.mal_client_id) as mal,
    ):
        primary = await bangumi.fetch_subject(bangumi_id)
        result = await CrossSourceMatcher(mal).match(primary, limit=limit)
        selected_anime = (
            await mal.fetch_subject(result.selected.external_id) if result.selected else None
        )
    rating_written = False
    if write:
        store = PostgresSyncStore(PostgresDatabase(settings.database_url).connection)
        run_id = store.start_run("mal", "cross_source_match", 1)
        try:
            store.record_match_result(bangumi_id, result)
            rating_written = bool(selected_anime and store.upsert_mapped_rating(selected_anime))
            store.finish_run(run_id, succeeded=1, failed=0)
            store.mark_connector("mal")
        except Exception as error:
            store.finish_run(run_id, succeeded=0, failed=1, errors=[str(error)])
            store.mark_connector("mal", error=str(error))
            raise
    return {
        "primary": {
            "source": primary.source,
            "external_id": primary.external_id,
            "title": primary.name_cn or primary.canonical_name,
        },
        "query_terms": result.query_terms,
        "selected": result.selected.model_dump(mode="json") if result.selected else None,
        "candidates": [candidate.model_dump(mode="json") for candidate in result.candidates],
        "writes_performed": write,
        "rating_written": rating_written,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Bangumi to MAL candidate matching")
    parser.add_argument("--bangumi-id", required=True)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--write", action="store_true", help="Persist into APP_DATABASE_URL")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        result = asyncio.run(run(args.bangumi_id, args.limit, write=args.write))
    except RuntimeError as exc:
        parser.exit(2, f"Configuration error: {exc}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
