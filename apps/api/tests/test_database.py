from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

from anime_oscilloscope.config import Settings
from anime_oscilloscope.database import (
    catalog_anime_from_rows,
    create_repositories,
    normalize_dsn,
    source_freshness_from_row,
)


def test_catalog_mapper_converts_postgres_rows_to_api_contract() -> None:
    anime_id = UUID("4f8f28a0-b2a9-4b28-94b3-513ac223d111")
    now = datetime(2026, 7, 1, tzinfo=UTC)
    anime = catalog_anime_from_rows(
        {
            "id": anime_id,
            "canonical_name": "Aurora Frequency",
            "name_cn": "极光频率",
            "aliases": ["オーロラ周波数"],
            "summary": "真实仓储映射测试",
            "image_url": None,
            "air_date": date(2026, 4, 4),
            "end_date": None,
            "media_type": "tv",
            "status": "airing",
            "regions": ["JP"],
            "episode_count": 12,
            "tags": ["科幻"],
            "updated_at": now,
        },
        [
            {
                "source": "bangumi",
                "score": Decimal("8.80"),
                "rating_count": 12480,
                "source_rank": 10,
                "sampled_at": now,
            }
        ],
        [{"source": "bangumi", "external_id": "12345"}],
    )

    assert anime.id == str(anime_id)
    assert anime.ratings[0].score == 8.8
    assert anime.external_links["bangumi"] == "https://bgm.tv/subject/12345"


def test_database_url_and_source_freshness_are_normalized() -> None:
    assert normalize_dsn("postgresql+psycopg://user:pass@host/db") == (
        "postgresql://user:pass@host/db"
    )
    freshness = source_freshness_from_row(
        {
            "source": "mal",
            "last_success_at": datetime(2026, 6, 30, tzinfo=UTC),
            "last_attempt_at": datetime(2026, 7, 1, tzinfo=UTC),
            "last_error": "upstream timeout; retaining the last snapshot",
        }
    )
    assert freshness.status == "stale"
    assert freshness.message is not None


def test_demo_repository_remains_the_safe_default() -> None:
    catalog, history = create_repositories(Settings())

    assert catalog.data_mode == "demo"
    assert history.data_mode == "demo"
