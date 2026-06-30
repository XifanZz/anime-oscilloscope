from datetime import date, datetime, timedelta
from enum import StrEnum

from anime_oscilloscope.domain import AirStatus


class SamplingCadence(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


CADENCE_INTERVALS = {
    SamplingCadence.DAILY: timedelta(days=1),
    SamplingCadence.WEEKLY: timedelta(days=7),
    SamplingCadence.MONTHLY: timedelta(days=30),
    SamplingCadence.YEARLY: timedelta(days=365),
}


def is_tracking_candidate(air_date: date, launch_date: date) -> bool:
    """Historical tracking starts only for shows premiering on or after product launch."""
    return air_date >= launch_date


def sampling_cadence(
    *, status: AirStatus, end_date: date | None, today: date
) -> SamplingCadence | None:
    if status == AirStatus.AIRING:
        return SamplingCadence.DAILY
    if status != AirStatus.FINISHED or end_date is None:
        return None

    days_since_completion = max(0, (today - end_date).days)
    if days_since_completion <= 90:
        return SamplingCadence.WEEKLY
    if days_since_completion <= 3 * 365:
        return SamplingCadence.MONTHLY
    return SamplingCadence.YEARLY


def is_sample_due(
    *, cadence: SamplingCadence | None, last_sampled_at: datetime | None, now: datetime
) -> bool:
    if cadence is None:
        return False
    if last_sampled_at is None:
        return True
    return now >= last_sampled_at + CADENCE_INTERVALS[cadence]
