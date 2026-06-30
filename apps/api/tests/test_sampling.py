from datetime import UTC, date, datetime, timedelta

from anime_oscilloscope.domain import AirStatus
from anime_oscilloscope.sampling import (
    SamplingCadence,
    is_sample_due,
    is_tracking_candidate,
    sampling_cadence,
)


def test_only_tracks_titles_premiering_from_launch_date() -> None:
    launch = date(2026, 7, 1)

    assert not is_tracking_candidate(date(2026, 6, 30), launch)
    assert is_tracking_candidate(date(2026, 7, 1), launch)


def test_airing_titles_are_sampled_daily() -> None:
    assert sampling_cadence(
        status=AirStatus.AIRING, end_date=None, today=date(2026, 8, 1)
    ) == SamplingCadence.DAILY


def test_completed_title_cadence_transitions() -> None:
    today = date(2026, 6, 30)

    assert sampling_cadence(
        status=AirStatus.FINISHED, end_date=today - timedelta(days=90), today=today
    ) == SamplingCadence.WEEKLY
    assert sampling_cadence(
        status=AirStatus.FINISHED, end_date=today - timedelta(days=91), today=today
    ) == SamplingCadence.MONTHLY
    assert sampling_cadence(
        status=AirStatus.FINISHED, end_date=today - timedelta(days=3 * 365 + 1), today=today
    ) == SamplingCadence.YEARLY


def test_unknown_or_upcoming_titles_are_not_scheduled() -> None:
    assert sampling_cadence(
        status=AirStatus.UPCOMING, end_date=None, today=date(2026, 6, 30)
    ) is None


def test_due_check_respects_last_successful_sample() -> None:
    now = datetime(2026, 6, 30, tzinfo=UTC)

    assert is_sample_due(cadence=SamplingCadence.DAILY, last_sampled_at=None, now=now)
    assert is_sample_due(
        cadence=SamplingCadence.DAILY,
        last_sampled_at=now - timedelta(days=1),
        now=now,
    )
    assert not is_sample_due(
        cadence=SamplingCadence.WEEKLY,
        last_sampled_at=now - timedelta(days=6),
        now=now,
    )
