import re
import unicodedata
from difflib import SequenceMatcher

from anime_oscilloscope.connectors.mal import MALConnector
from anime_oscilloscope.domain import (
    MatchCandidate,
    MatchDisposition,
    MatchEvidence,
    MatchResult,
    NormalizedAnime,
)

_INSTALLMENT_PATTERNS = (
    re.compile(r"\b(?:season|series|part)\s*(\d+)\b", re.IGNORECASE),
    re.compile(r"\b(\d+)(?:st|nd|rd|th)\s*season\b", re.IGNORECASE),
    re.compile(r"第\s*(\d+)\s*[期季部章]"),
)
_FORMAT_MARKERS = {
    "movie": ("movie", "劇場版", "剧场版", "映画"),
    "ova": ("ova", "oad"),
}


def normalize_title(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    normalized = re.sub(r"[^\w\u3040-\u30ff\u3400-\u9fff]+", " ", normalized)
    return " ".join(normalized.split())


def title_variants(anime: NormalizedAnime) -> list[str]:
    values = [anime.canonical_name, anime.name_cn or "", *anime.aliases]
    return list(dict.fromkeys(normalize_title(value) for value in values if normalize_title(value)))


def title_similarity(left: NormalizedAnime, right: NormalizedAnime) -> float:
    left_variants = title_variants(left)
    right_variants = title_variants(right)
    if not left_variants or not right_variants:
        return 0.0
    if set(left_variants) & set(right_variants):
        return 1.0
    return max(
        SequenceMatcher(None, left_value, right_value).ratio()
        for left_value in left_variants
        for right_value in right_variants
    )


def _installment_signature(anime: NormalizedAnime) -> set[str]:
    text = " ".join([anime.canonical_name, anime.name_cn or "", *anime.aliases])
    signature: set[str] = set()
    for pattern in _INSTALLMENT_PATTERNS:
        signature.update(f"installment:{match}" for match in pattern.findall(text))
    normalized = text.casefold()
    for marker, tokens in _FORMAT_MARKERS.items():
        if any(token.casefold() in normalized for token in tokens):
            signature.add(f"format:{marker}")
    return signature


def _date_similarity(left: NormalizedAnime, right: NormalizedAnime) -> float:
    if not left.air_date or not right.air_date:
        return 0.5
    difference = abs((left.air_date - right.air_date).days)
    if difference == 0:
        return 1.0
    if difference <= 7:
        return 0.9
    if difference <= 31:
        return 0.7
    if difference <= 93:
        return 0.35
    return 0.0


def _episode_similarity(left: NormalizedAnime, right: NormalizedAnime) -> float:
    if left.episode_count is None or right.episode_count is None:
        return 0.5
    if left.episode_count == right.episode_count:
        return 1.0
    difference = abs(left.episode_count - right.episode_count)
    return 0.6 if difference <= 2 else 0.0


def score_candidate(primary: NormalizedAnime, candidate: NormalizedAnime) -> MatchCandidate:
    title_score = title_similarity(primary, candidate)
    date_score = _date_similarity(primary, candidate)
    media_score = 1.0 if primary.media_type == candidate.media_type else 0.0
    episode_score = _episode_similarity(primary, candidate)
    primary_signature = _installment_signature(primary)
    candidate_signature = _installment_signature(candidate)
    installment_conflict = bool(primary_signature or candidate_signature) and (
        primary_signature != candidate_signature
    )
    confidence = round(
        0.65 * title_score + 0.2 * date_score + 0.1 * media_score + 0.05 * episode_score,
        4,
    )
    reasons: list[str] = []
    if media_score == 0:
        reasons.append("media_type_mismatch")
    if date_score <= 0.35:
        reasons.append("air_date_far_apart")
    if episode_score == 0:
        reasons.append("episode_count_mismatch")
    if installment_conflict:
        reasons.append("installment_signature_conflict")

    if confidence >= 0.88 and title_score >= 0.92 and not reasons:
        disposition = MatchDisposition.AUTOMATIC
    elif confidence >= 0.58:
        disposition = MatchDisposition.REVIEW
    else:
        disposition = MatchDisposition.REJECT
    return MatchCandidate(
        source=candidate.source,
        external_id=candidate.external_id,
        title=candidate.canonical_name,
        confidence=confidence,
        disposition=disposition,
        evidence=MatchEvidence(
            title_similarity=round(title_score, 4),
            date_similarity=date_score,
            media_similarity=media_score,
            episode_similarity=episode_score,
            installment_conflict=installment_conflict,
            reasons=reasons,
        ),
    )


def rank_candidates(
    primary: NormalizedAnime,
    candidates: list[NormalizedAnime],
) -> list[MatchCandidate]:
    scored = [score_candidate(primary, candidate) for candidate in candidates]
    return sorted(scored, key=lambda candidate: candidate.confidence, reverse=True)


class CrossSourceMatcher:
    def __init__(self, mal: MALConnector) -> None:
        self.mal = mal

    @staticmethod
    def query_terms(primary: NormalizedAnime) -> list[str]:
        candidates = [primary.canonical_name, *primary.aliases, primary.name_cn or ""]
        return list(dict.fromkeys(value.strip() for value in candidates if value.strip()))[:2]

    async def match(self, primary: NormalizedAnime, *, limit: int = 10) -> MatchResult:
        queries = self.query_terms(primary)
        found: dict[str, NormalizedAnime] = {}
        for query in queries:
            for candidate in await self.mal.search(query, limit=limit):
                found[candidate.external_id] = candidate
            if found:
                break
        return MatchResult(
            primary_source=primary.source,
            primary_external_id=primary.external_id,
            query_terms=queries,
            candidates=rank_candidates(primary, list(found.values())),
        )
