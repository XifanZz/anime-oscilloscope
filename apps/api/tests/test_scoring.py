from math import log1p

from anime_oscilloscope.domain import RatingObservation, SourceCode
from anime_oscilloscope.scoring import composite_score, meets_thresholds


def observation(source: SourceCode, score: float, count: int) -> RatingObservation:
    return RatingObservation(source=source, score=score, rating_count=count)


def test_composite_score_uses_platform_coefficients_and_log_votes() -> None:
    ratings = [
        observation(SourceCode.BANGUMI, 8.8, 1_000),
        observation(SourceCode.MAL, 8.2, 20_000),
    ]
    expected = (
        8.8 * 1.5 * log1p(1_000) + 8.2 * log1p(20_000)
    ) / (1.5 * log1p(1_000) + log1p(20_000))

    assert composite_score(ratings) == round(expected, 3)


def test_missing_source_is_not_treated_as_zero() -> None:
    assert composite_score([observation(SourceCode.BANGUMI, 8.4, 2_000)]) == 8.4
    assert composite_score([]) is None


def test_single_source_low_vote_scores_are_confidence_guarded() -> None:
    assert composite_score([observation(SourceCode.BANGUMI, 8.8, 4)]) == 5.152
    assert composite_score([observation(SourceCode.BANGUMI, 4.7, 100)]) == 4.7


def test_thresholds_require_every_selected_source_and_strictly_greater_votes() -> None:
    thresholds = {SourceCode.BANGUMI: 1_000, SourceCode.MAL: 20_000}
    assert meets_thresholds(
        [
            observation(SourceCode.BANGUMI, 8.0, 1_001),
            observation(SourceCode.MAL, 8.0, 20_001),
        ],
        thresholds,
    )
    assert not meets_thresholds(
        [
            observation(SourceCode.BANGUMI, 8.0, 1_000),
            observation(SourceCode.MAL, 8.0, 20_001),
        ],
        thresholds,
    )
    assert not meets_thresholds(
        [observation(SourceCode.BANGUMI, 8.0, 1_001)],
        thresholds,
    )
