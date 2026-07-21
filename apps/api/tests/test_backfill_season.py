from anime_oscilloscope.jobs.backfill_season import next_offset


def test_season_backfill_continues_when_page_is_full_and_total_remains() -> None:
    assert next_offset(offset=0, item_count=100, total=224, limit=100) == (100, False)


def test_season_backfill_completes_on_last_partial_page() -> None:
    assert next_offset(offset=200, item_count=24, total=224, limit=100) == (224, True)


def test_season_backfill_completes_when_source_returns_empty_page() -> None:
    assert next_offset(offset=300, item_count=0, total=224, limit=100) == (300, True)
