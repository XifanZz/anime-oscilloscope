import re
from enum import StrEnum

from pydantic import BaseModel

from anime_oscilloscope.domain import NormalizedAnime

TARGET_REGIONS = {"CN", "JP", "KR"}
_MY_HERO_PATTERNS = (
    "我的英雄学院",
    "僕のヒーローアカデミア",
    "ぼくのヒーローアカデミア",
    "boku no hero academia",
    "my hero academia",
    "ヒロアカ",
    "vigilantes my hero academia illegals",
    "ヴィジランテ 僕のヒーローアカデミア illegals",
    "正义使者 我的英雄学院之非法英雄",
)


class EligibilityStatus(StrEnum):
    ELIGIBLE = "eligible"
    EXCLUDED = "excluded"
    REVIEW = "review"


class EligibilityDecision(BaseModel):
    status: EligibilityStatus
    reason: str


def _search_text(anime: NormalizedAnime) -> str:
    raw = " ".join(
        part
        for part in [anime.canonical_name, anime.name_cn or "", *anime.aliases]
        if part
    ).casefold()
    return re.sub(r"[^\w\u3040-\u30ff\u3400-\u9fff]+", " ", raw)


def is_excluded_franchise(anime: NormalizedAnime) -> bool:
    text = _search_text(anime)
    return any(pattern.casefold() in text for pattern in _MY_HERO_PATTERNS)


def evaluate_eligibility(anime: NormalizedAnime) -> EligibilityDecision:
    if anime.is_nsfw:
        return EligibilityDecision(status=EligibilityStatus.EXCLUDED, reason="nsfw")
    if is_excluded_franchise(anime):
        return EligibilityDecision(
            status=EligibilityStatus.EXCLUDED,
            reason="excluded_franchise",
        )
    if not anime.regions:
        return EligibilityDecision(
            status=EligibilityStatus.REVIEW,
            reason="region_missing",
        )
    if anime.regions & TARGET_REGIONS:
        return EligibilityDecision(status=EligibilityStatus.ELIGIBLE, reason="target_region")
    return EligibilityDecision(status=EligibilityStatus.EXCLUDED, reason="outside_target_regions")
