import json
from datetime import date
from pathlib import Path

from anime_oscilloscope.connectors.bangumi import normalize_subject
from anime_oscilloscope.connectors.mal import normalize_mal_anime
from anime_oscilloscope.domain import MatchDisposition, MediaType, NormalizedAnime, SourceCode
from anime_oscilloscope.matching import rank_candidates, score_candidate, title_similarity

FIXTURE_ROOT = Path(__file__).parent / "fixtures"


def fixture(path: str) -> dict[str, object]:
    return json.loads((FIXTURE_ROOT / path).read_text(encoding="utf-8"))


def anime(source: SourceCode, external_id: str, title: str, **values: object) -> NormalizedAnime:
    return NormalizedAnime(
        source=source,
        external_id=external_id,
        canonical_name=title,
        source_url=f"https://example.invalid/{external_id}",
        **values,
    )


def test_exact_alias_date_type_and_episode_count_match_automatically() -> None:
    primary = normalize_subject(fixture("bangumi/subject.json"), as_of=date(2026, 6, 30))
    candidate = normalize_mal_anime(fixture("mal/anime_details.json"))

    result = score_candidate(primary, candidate)

    assert title_similarity(primary, candidate) == 1
    assert result.confidence == 1
    assert result.disposition is MatchDisposition.AUTOMATIC
    assert result.evidence.reasons == []


def test_movie_with_similar_title_is_held_for_review() -> None:
    primary = anime(
        SourceCode.BANGUMI,
        "1",
        "Signal Anime",
        air_date=date(2026, 7, 3),
        media_type=MediaType.TV,
        episode_count=12,
    )
    movie = anime(
        SourceCode.MAL,
        "2",
        "Signal Anime Movie",
        aliases=["Signal Anime"],
        air_date=date(2026, 12, 1),
        media_type=MediaType.MOVIE,
        episode_count=1,
    )

    result = score_candidate(primary, movie)

    assert result.disposition is MatchDisposition.REVIEW
    assert "media_type_mismatch" in result.evidence.reasons
    assert "installment_signature_conflict" in result.evidence.reasons


def test_different_seasons_never_auto_match() -> None:
    first = anime(
        SourceCode.BANGUMI,
        "1",
        "Example 1st Season",
        air_date=date(2024, 1, 1),
        media_type=MediaType.TV,
    )
    second = anime(
        SourceCode.MAL,
        "2",
        "Example 2nd Season",
        air_date=date(2025, 1, 1),
        media_type=MediaType.TV,
    )

    result = score_candidate(first, second)

    assert result.disposition is not MatchDisposition.AUTOMATIC
    assert result.evidence.installment_conflict is True


def test_unrelated_candidates_are_rejected_and_ranked_last() -> None:
    primary = anime(SourceCode.BANGUMI, "1", "Signal Anime", media_type=MediaType.TV)
    exact = anime(
        SourceCode.MAL,
        "2",
        "Signal Anime",
        media_type=MediaType.TV,
    )
    unrelated = anime(
        SourceCode.MAL,
        "3",
        "Unrelated Cooking Show",
        media_type=MediaType.TV,
    )

    ranked = rank_candidates(primary, [unrelated, exact])

    assert ranked[0].external_id == "2"
    assert ranked[-1].disposition is MatchDisposition.REJECT
