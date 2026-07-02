from anime_oscilloscope.jobs.backfill_catalog import next_position


def test_backfill_stays_in_year_when_page_has_more_results() -> None:
    assert next_position(
        year=2001,
        offset=100,
        item_count=100,
        total=350,
        end_year=2026,
    ) == (2001, 200, False)


def test_backfill_advances_year_after_last_page() -> None:
    assert next_position(
        year=2001,
        offset=200,
        item_count=45,
        total=245,
        end_year=2026,
    ) == (2002, 0, False)


def test_backfill_marks_completion_after_end_year() -> None:
    assert next_position(
        year=2026,
        offset=0,
        item_count=0,
        total=0,
        end_year=2026,
    ) == (2027, 0, True)
