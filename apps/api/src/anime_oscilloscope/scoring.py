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


def composite_score(ratings: list[RatingObservation]) -> float | None:
    """Return the weighted score without treating an absent source as zero."""
    usable = [rating for rating in ratings if rating.rating_count > 0]
    if not usable:
        return None

    numerator = sum(
        rating.score * PLATFORM_COEFFICIENTS[rating.source] * log1p(rating.rating_count)
        for rating in usable
    )
    denominator = sum(
        PLATFORM_COEFFICIENTS[rating.source] * log1p(rating.rating_count)
        for rating in usable
    )
    return round(numerator / denominator, 3)


def meets_thresholds(
    ratings: list[RatingObservation], thresholds: dict[SourceCode, int]
) -> bool:
    ratings_by_source = {rating.source: rating for rating in ratings}
    return all(
        source in ratings_by_source
        and ratings_by_source[source].rating_count > minimum
        for source, minimum in thresholds.items()
    )
