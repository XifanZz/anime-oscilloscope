import argparse
import asyncio
import json
import sys

from anime_oscilloscope.config import get_settings
from anime_oscilloscope.connectors import BangumiConnector, MALConnector
from anime_oscilloscope.matching import CrossSourceMatcher


async def run(bangumi_id: str, limit: int) -> dict[str, object]:
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
    return {
        "primary": {
            "source": primary.source,
            "external_id": primary.external_id,
            "title": primary.name_cn or primary.canonical_name,
        },
        "query_terms": result.query_terms,
        "selected": result.selected.model_dump(mode="json") if result.selected else None,
        "candidates": [candidate.model_dump(mode="json") for candidate in result.candidates],
        "writes_performed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only Bangumi to MAL candidate matching")
    parser.add_argument("--bangumi-id", required=True)
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        result = asyncio.run(run(args.bangumi_id, args.limit))
    except RuntimeError as exc:
        parser.exit(2, f"Configuration error: {exc}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
