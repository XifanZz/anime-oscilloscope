from datetime import UTC, datetime, timedelta
from math import pi, sin

from anime_oscilloscope.domain import SourceCode
from anime_oscilloscope.history import (
    EpisodeMarker,
    InMemoryHistoryRepository,
    RatingHistory,
    RatingPoint,
    RatingSeries,
    SourceFreshness,
    build_composite_series,
)


def at(month: int, day: int, hour: int = 12) -> datetime:
    return datetime(2026, month, day, hour, tzinfo=UTC)


def daily_series(
    source: SourceCode,
    *,
    start_score: float,
    end_score: float,
    start_count: int,
    end_count: int,
) -> RatingSeries:
    start = at(4, 5, 8)
    end = at(6, 30, 8)
    total_days = (end - start).days
    points = []
    for day in range(total_days + 1):
        progress = day / total_days
        sampled_at = start + timedelta(days=day)
        wave = sin(progress * 4 * pi) * 0.06
        points.append(
            RatingPoint(
                sampled_at=sampled_at,
                score=round(start_score + (end_score - start_score) * progress + wave, 2),
                rating_count=round(start_count + (end_count - start_count) * progress),
            )
        )
    return RatingSeries(source=source, points=points)


bangumi = daily_series(
    SourceCode.BANGUMI,
    start_score=8.12,
    end_score=8.8,
    start_count=860,
    end_count=12480,
)

mal = daily_series(
    SourceCode.MAL,
    start_score=8.34,
    end_score=8.6,
    start_count=12400,
    end_count=84210,
)

aurora_history = RatingHistory(
    anime_id="demo-aurora",
    series=[bangumi, mal],
    composite=build_composite_series([bangumi, mal]),
    episodes=[
        EpisodeMarker(
            episode_number=number,
            air_date=at(4, 4) + timedelta(days=7 * (number - 1)),
            title=f"第 {number} 话",
        )
        for number in range(1, 13)
    ],
    freshness=[
        SourceFreshness(
            source=SourceCode.BANGUMI,
            status="fresh",
            last_success_at=at(6, 30, 8),
            last_attempt_at=at(6, 30, 8),
        ),
        SourceFreshness(
            source=SourceCode.MAL,
            status="stale",
            last_success_at=at(6, 30, 8),
            last_attempt_at=at(6, 30, 12),
            message="演示：最近一次请求失败，继续展示上次成功快照。",
        ),
    ],
)

DEMO_HISTORY = InMemoryHistoryRepository([aurora_history])
