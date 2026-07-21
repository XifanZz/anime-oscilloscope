from math import log1p

from anime_oscilloscope.domain import RatingObservation, SourceCode

PLATFORM_COEFFICIENTS: dict[SourceCode, float] = {
    SourceCode.BANGUMI: 1.5,
    SourceCode.MAL: 1.0,
    SourceCode.DOUBAN: 1.0,
    SourceCode.FILMARKS: 1.0,
}

DEFAULT_VOTE_THRESHOLDS: dict[SourceCode, int] = {
    SourceCode.BANGUMI: 1_000,
    SourceCode.MAL: 20_000,
    SourceCode.DOUBAN: 5_000,
    SourceCode.FILMARKS: 1_000,
}

SINGLE_SOURCE_CONFIDENT_VOTES: dict[SourceCode, int] = {
    SourceCode.BANGUMI: 100,
    SourceCode.MAL: 1_000,
    SourceCode.DOUBAN: 500,
    SourceCode.FILMARKS: 200,
}

NEUTRAL_SCORE = 5.0


def composite_score(ratings: list[RatingObservation]) -> float | None:
    """Return the weighted score without treating an absent source as zero."""
    usable = [rating for rating in ratings if rating.rating_count > 0]
    if not usable:
        return None
    if len(usable) == 1:
        return single_source_score(usable[0])

    numerator = sum(
        rating.score * PLATFORM_COEFFICIENTS[rating.source] * log1p(rating.rating_count)
        for rating in usable
    )
    denominator = sum(
        PLATFORM_COEFFICIENTS[rating.source] * log1p(rating.rating_count)
        for rating in usable
    )
    return round(numerator / denominator, 3)


def single_source_score(rating: RatingObservation) -> float:
    """Return one-source score with a low-vote confidence guard.

    If Bangumi is the only available source and has enough votes, the composite
    score remains the Bangumi score. Very early, tiny-population snapshots are
    pulled toward a neutral 5.0 so they cannot outrank stable two-source titles.
    """
    confident_votes = SINGLE_SOURCE_CONFIDENT_VOTES[rating.source]
    if rating.rating_count >= confident_votes:
        return round(rating.score, 3)
    confidence = max(0.0, min(1.0, rating.rating_count / confident_votes))
    return round(NEUTRAL_SCORE + (rating.score - NEUTRAL_SCORE) * confidence, 3)


def meets_thresholds(
    ratings: list[RatingObservation], thresholds: dict[SourceCode, int]
) -> bool:
    ratings_by_source = {rating.source: rating for rating in ratings}
    return all(
        source in ratings_by_source
        and ratings_by_source[source].rating_count > minimum
        for source, minimum in thresholds.items()
    )
