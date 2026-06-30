from enum import StrEnum

from pydantic import BaseModel, Field

from anime_oscilloscope.domain.source import SourceCode


class MatchDisposition(StrEnum):
    AUTOMATIC = "automatic"
    REVIEW = "review"
    REJECT = "reject"


class MatchEvidence(BaseModel):
    title_similarity: float = Field(ge=0, le=1)
    date_similarity: float = Field(ge=0, le=1)
    media_similarity: float = Field(ge=0, le=1)
    episode_similarity: float = Field(ge=0, le=1)
    installment_conflict: bool = False
    reasons: list[str] = Field(default_factory=list)


class MatchCandidate(BaseModel):
    source: SourceCode
    external_id: str
    title: str
    confidence: float = Field(ge=0, le=1)
    disposition: MatchDisposition
    evidence: MatchEvidence


class MatchResult(BaseModel):
    primary_source: SourceCode
    primary_external_id: str
    query_terms: list[str]
    candidates: list[MatchCandidate]

    @property
    def selected(self) -> MatchCandidate | None:
        if self.candidates and self.candidates[0].disposition is MatchDisposition.AUTOMATIC:
            return self.candidates[0]
        return None
