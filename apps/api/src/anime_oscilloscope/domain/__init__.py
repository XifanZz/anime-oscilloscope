"""Domain types shared by connectors, jobs, and HTTP routes."""

from anime_oscilloscope.domain.mapping import (
    MatchCandidate,
    MatchDisposition,
    MatchEvidence,
    MatchResult,
)
from anime_oscilloscope.domain.source import (
    AirStatus,
    MediaType,
    NormalizedAnime,
    NormalizedEpisode,
    RatingObservation,
    SourceCode,
    SubjectPage,
)

__all__ = [
    "AirStatus",
    "MediaType",
    "MatchCandidate",
    "MatchDisposition",
    "MatchEvidence",
    "MatchResult",
    "NormalizedAnime",
    "NormalizedEpisode",
    "RatingObservation",
    "SourceCode",
    "SubjectPage",
]
