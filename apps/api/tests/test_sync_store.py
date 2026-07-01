from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from anime_oscilloscope.domain import (
    AirStatus,
    MediaType,
    NormalizedAnime,
    RatingObservation,
    SourceCode,
)
from anime_oscilloscope.policies import EligibilityDecision, EligibilityStatus
from anime_oscilloscope.sync_store import PostgresSyncStore, due_external_ids


class FakeResult:
    def __init__(self, row=None) -> None:
        self.row = row

    def fetchone(self):
        return self.row


class FakeConnection:
    def __init__(self) -> None:
        self.statements: list[tuple[str, tuple | None]] = []

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None

    def execute(self, sql: str, params: tuple | None = None) -> FakeResult:
        self.statements.append((" ".join(sql.split()), params))
        if "returning id" in sql and "insert into anime" in sql:
            return FakeResult({"id": UUID("4f8f28a0-b2a9-4b28-94b3-513ac223d111")})
        return FakeResult()


def test_bangumi_upsert_writes_catalog_mapping_current_rating_and_snapshot() -> None:
    connection = FakeConnection()
    store = PostgresSyncStore(lambda: connection)
    anime = NormalizedAnime(
        source=SourceCode.BANGUMI,
        external_id="12345",
        canonical_name="Aurora Frequency",
        name_cn="极光频率",
        air_date=date(2026, 4, 4),
        status=AirStatus.AIRING,
        media_type=MediaType.TV,
        regions={"JP"},
        tags=["科幻"],
        rating=RatingObservation(
            source=SourceCode.BANGUMI,
            score=8.8,
            rating_count=12480,
            sampled_at=datetime(2026, 7, 1, tzinfo=UTC),
        ),
        source_url="https://bgm.tv/subject/12345",
    )

    anime_id = store.upsert_bangumi(
        anime,
        EligibilityDecision(status=EligibilityStatus.ELIGIBLE, reason="target_region"),
    )

    sql = "\n".join(statement for statement, _ in connection.statements)
    assert anime_id == "4f8f28a0-b2a9-4b28-94b3-513ac223d111"
    assert "insert into anime" in sql
    assert "insert into external_mapping" in sql
    assert "insert into current_rating" in sql
    assert "insert into rating_snapshot" in sql


def test_due_mapping_selection_honors_launch_date_and_cadence() -> None:
    now = datetime(2026, 7, 8, tzinfo=UTC)
    rows = [
        {
            "external_id": "due",
            "air_date": date(2026, 7, 1),
            "status": AirStatus.AIRING,
            "end_date": None,
            "last_sampled_at": now - timedelta(days=1),
        },
        {
            "external_id": "not-due",
            "air_date": date(2026, 7, 1),
            "status": AirStatus.AIRING,
            "end_date": None,
            "last_sampled_at": now - timedelta(hours=8),
        },
        {
            "external_id": "before-launch",
            "air_date": date(2026, 6, 30),
            "status": AirStatus.AIRING,
            "end_date": None,
            "last_sampled_at": None,
        },
    ]

    assert due_external_ids(rows, launch_date=date(2026, 7, 1), now=now) == ["due"]
