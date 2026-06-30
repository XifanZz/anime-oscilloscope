from __future__ import annotations

import re
from math import sqrt
from time import perf_counter
from typing import Protocol

from pydantic import BaseModel, Field

from anime_oscilloscope.catalog import CatalogAnime, CatalogRepository
from anime_oscilloscope.domain import AirStatus, MediaType

VECTOR_DIMENSIONS = 512


class SemanticSearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=200)
    limit: int = Field(default=10, ge=1, le=20)


class ParsedIntent(BaseModel):
    year: int | None = None
    regions: list[str] = Field(default_factory=list)
    media_types: list[MediaType] = Field(default_factory=list)
    statuses: list[AirStatus] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class SemanticMatch(BaseModel):
    anime: CatalogAnime
    confidence: float = Field(ge=0, le=1)
    reasons: list[str]


class SemanticSearchResponse(BaseModel):
    data_mode: str
    query: str
    engine: str
    model_name: str
    parsed_intent: ParsedIntent
    results: list[SemanticMatch]
    elapsed_ms: float = Field(ge=0)


class EmbeddingProvider(Protocol):
    name: str
    model_name: str

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class HashEmbeddingProvider:
    name = "hash-512-demo"
    model_name = "deterministic-character-ngram"

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [_hash_embedding(text) for text in texts]


class FastEmbedBgeProvider:
    name = "fastembed-onnx"

    def __init__(self, model_name: str = "BAAI/bge-small-zh-v1.5") -> None:
        try:
            from fastembed import TextEmbedding
        except ImportError as error:
            raise RuntimeError(
                "Install the API with the [ai] extra to enable the BGE backend"
            ) from error
        self.model_name = model_name
        self._model = TextEmbedding(model_name=model_name)

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [vector.tolist() for vector in self._model.embed(texts)]


def create_embedding_provider(backend: str, model_name: str) -> EmbeddingProvider:
    if backend == "bge":
        return FastEmbedBgeProvider(model_name)
    return HashEmbeddingProvider()


def _hash_embedding(text: str) -> list[float]:
    normalized = re.sub(r"\s+", "", text.casefold())
    tokens = [normalized[index : index + 2] for index in range(max(1, len(normalized) - 1))]
    vector = [0.0] * VECTOR_DIMENSIONS
    for token in tokens:
        token_hash = sum(
            (position + 1) * ord(character) for position, character in enumerate(token)
        )
        index = token_hash % VECTOR_DIMENSIONS
        vector[index] += 1.0
    norm = sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


def _cosine(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=False))


REGION_TERMS = {
    "中日合拍": ["CN", "JP"],
    "中韩合拍": ["CN", "KR"],
    "日本": ["JP"],
    "日漫": ["JP"],
    "国产": ["CN"],
    "国漫": ["CN"],
    "中国": ["CN"],
    "韩国": ["KR"],
    "韩漫": ["KR"],
}
MEDIA_TERMS = {
    "tv": MediaType.TV,
    "电视": MediaType.TV,
    "web": MediaType.WEB,
    "网番": MediaType.WEB,
    "电影": MediaType.MOVIE,
    "剧场版": MediaType.MOVIE,
    "ova": MediaType.OVA,
    "特别篇": MediaType.SPECIAL,
}
STATUS_TERMS = {
    "连载": AirStatus.AIRING,
    "在播": AirStatus.AIRING,
    "完结": AirStatus.FINISHED,
}


def parse_intent(query: str, known_tags: set[str]) -> ParsedIntent:
    lowered = query.casefold()
    year_match = re.search(r"(?:19|20)\d{2}", lowered)
    regions: list[str] = []
    for term, codes in REGION_TERMS.items():
        if term in lowered:
            regions.extend(codes)
    media_types = [media for term, media in MEDIA_TERMS.items() if term in lowered]
    statuses = [status for term, status in STATUS_TERMS.items() if term in lowered]
    tags = [tag for tag in sorted(known_tags) if tag.casefold() in lowered]
    return ParsedIntent(
        year=int(year_match.group()) if year_match else None,
        regions=list(dict.fromkeys(regions)),
        media_types=list(dict.fromkeys(media_types)),
        statuses=list(dict.fromkeys(statuses)),
        tags=tags,
    )


def _document(anime: CatalogAnime) -> str:
    return " ".join(
        [
            anime.name_cn or "",
            anime.canonical_name,
            *anime.aliases,
            *anime.tags,
            anime.summary,
            *anime.regions,
            anime.media_type.value,
            str(anime.air_date.year),
        ]
    )


def _rule_evidence(anime: CatalogAnime, intent: ParsedIntent) -> tuple[bool, float, list[str]]:
    score = 0.0
    reasons: list[str] = []
    if intent.year is not None:
        if anime.air_date.year != intent.year:
            return False, 0, []
        score += 0.12
        reasons.append(f"符合 {intent.year} 年条件")
    if intent.regions:
        if not set(intent.regions).issubset(anime.regions):
            return False, 0, []
        score += 0.18
        reasons.append(f"制作地区匹配：{' / '.join(intent.regions)}")
    if intent.media_types:
        if anime.media_type not in intent.media_types:
            return False, 0, []
        score += 0.16
        reasons.append(f"作品类型匹配：{anime.media_type.value.upper()}")
    if intent.statuses:
        if anime.status not in intent.statuses:
            return False, 0, []
        score += 0.12
        reasons.append("播出状态符合条件")
    if intent.tags:
        matched_tags = sorted(set(intent.tags) & set(anime.tags))
        if not matched_tags:
            return False, 0, []
        score += min(0.28, 0.14 * len(matched_tags))
        reasons.append(f"标签匹配：{'、'.join(matched_tags)}")
    return True, score, reasons


class SemanticSearchService:
    def __init__(self, repository: CatalogRepository, provider: EmbeddingProvider) -> None:
        self.repository = repository
        self.provider = provider

    def search(self, request: SemanticSearchRequest) -> SemanticSearchResponse:
        started = perf_counter()
        catalog = self.repository.list_all()
        known_tags = {tag for anime in catalog for tag in anime.tags}
        intent = parse_intent(request.query, known_tags)
        vectors = self.provider.embed([request.query, *[_document(anime) for anime in catalog]])
        if any(len(vector) != VECTOR_DIMENSIONS for vector in vectors):
            raise RuntimeError(
                f"Embedding provider must return {VECTOR_DIMENSIONS}-dimensional vectors"
            )
        query_vector, document_vectors = vectors[0], vectors[1:]
        matches: list[SemanticMatch] = []

        for anime, vector in zip(catalog, document_vectors, strict=True):
            eligible, rule_score, reasons = _rule_evidence(anime, intent)
            if not eligible:
                continue
            similarity = max(0.0, _cosine(query_vector, vector))
            confidence = min(0.99, 0.2 + rule_score + 0.42 * similarity)
            if similarity > 0:
                reasons.append(f"语义内容相似度 {similarity:.2f}")
            if not reasons:
                reasons.append("标题、简介或标签与描述存在语义关联")
            matches.append(
                SemanticMatch(anime=anime, confidence=round(confidence, 3), reasons=reasons)
            )

        matches.sort(key=lambda match: match.confidence, reverse=True)
        return SemanticSearchResponse(
            data_mode=self.repository.data_mode,
            query=request.query,
            engine=self.provider.name,
            model_name=self.provider.model_name,
            parsed_intent=intent,
            results=matches[: request.limit],
            elapsed_ms=round((perf_counter() - started) * 1000, 3),
        )
