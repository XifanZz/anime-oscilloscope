from anime_oscilloscope.domain import NormalizedAnime, SourceCode
from anime_oscilloscope.policies import EligibilityStatus, evaluate_eligibility


def anime(**overrides: object) -> NormalizedAnime:
    values: dict[str, object] = {
        "source": SourceCode.BANGUMI,
        "external_id": "1",
        "canonical_name": "Test Anime",
        "regions": {"JP"},
        "source_url": "https://bgm.tv/subject/1",
    }
    values.update(overrides)
    return NormalizedAnime.model_validate(values)


def test_accepts_cjk_participation_in_a_coproduction() -> None:
    decision = evaluate_eligibility(anime(regions={"CN", "US"}))

    assert decision.status is EligibilityStatus.ELIGIBLE


def test_unknown_region_goes_to_review_instead_of_being_deleted() -> None:
    decision = evaluate_eligibility(anime(regions=set()))

    assert decision.status is EligibilityStatus.REVIEW
    assert decision.reason == "region_missing"


def test_excludes_nsfw_before_ingestion() -> None:
    decision = evaluate_eligibility(anime(is_nsfw=True))

    assert decision.status is EligibilityStatus.EXCLUDED
    assert decision.reason == "nsfw"


def test_excludes_the_configured_franchise_using_aliases() -> None:
    decision = evaluate_eligibility(anime(aliases=["Boku no Hero Academia: Fixture"]))

    assert decision.status is EligibilityStatus.EXCLUDED
    assert decision.reason == "excluded_franchise"


def test_excludes_titles_with_only_outside_regions() -> None:
    decision = evaluate_eligibility(anime(regions={"US", "FR"}))

    assert decision.status is EligibilityStatus.EXCLUDED
    assert decision.reason == "outside_target_regions"
