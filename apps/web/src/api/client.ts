export type SourceCode = "bangumi" | "mal" | "douban" | "filmarks";

export type Rating = {
  source: SourceCode;
  score: number;
  rating_count: number;
  sampled_at: string | null;
};

export type Anime = {
  id: string;
  canonical_name: string;
  name_cn: string | null;
  aliases: string[];
  summary: string;
  image_url: string | null;
  air_date: string;
  end_date: string | null;
  media_type: "tv" | "web" | "movie" | "ova" | "special" | "other";
  status: "upcoming" | "airing" | "finished" | "unknown";
  regions: string[];
  episode_count: number | null;
  tags: string[];
  ratings: Rating[];
  external_links: Partial<Record<SourceCode, string>>;
  updated_at: string;
};

export type RankedAnime = {
  rank: number;
  anime: Anime;
  composite_score: number;
  completeness: number;
  missing_sources: SourceCode[];
};

export type RankingResponse = {
  data_mode: "demo" | "live";
  generated_at: string;
  total: number;
  page: number;
  page_size: number;
  items: RankedAnime[];
};

export type SearchResponse = {
  data_mode: "demo" | "live";
  query: string;
  total: number;
  items: Anime[];
};

export type DetailResponse = {
  data_mode: "demo" | "live";
  anime: Anime;
  composite_score: number | null;
  completeness: number;
  missing_sources: SourceCode[];
};

export type DataQualityResponse = {
  data_mode: "demo" | "live";
  generated_at: string;
  total_anime: number;
  eligible_anime: number;
  rankable_anime: number;
  excluded_anime: number;
  nsfw_anime: number;
  with_bangumi_rating: number;
  with_mal_rating: number;
  with_both_core_sources: number;
  missing_mal: number;
  latest_rating_sampled_at: string | null;
  latest_catalog_updated_at: string | null;
  connectors: {
    source: SourceCode;
    label: string;
    enabled: boolean;
    status: "fresh" | "stale" | "unavailable";
    mapped_count: number;
    rated_count: number;
    latest_sampled_at: string | null;
    last_success_at: string | null;
    last_attempt_at: string | null;
    message: string | null;
  }[];
  backfill: {
    source: SourceCode;
    start_year: number;
    end_year: number;
    next_year: number;
    next_offset: number;
    processed_pages: number;
    discovered_count: number;
    completed: boolean;
    progress_percent: number;
    last_error: string | null;
    updated_at: string;
  } | null;
  recent_runs: {
    source: SourceCode;
    job_type: string;
    status: string;
    succeeded_count: number;
    failed_count: number;
    started_at: string;
    finished_at: string | null;
  }[];
  notes: string[];
};

export type MappingCandidatePage = {
  data_mode: "demo" | "live";
  generated_at: string;
  total: number;
  limit: number;
  offset: number;
  summary: {
    source: SourceCode;
    unresolved_review_count: number;
    automatic_count: number;
    rejected_count: number;
    approved_mapping_count: number;
    unmapped_rankable_count: number;
  };
  items: {
    id: number;
    anime: {
      id: string;
      bangumi_id: number | null;
      canonical_name: string;
      name_cn: string | null;
      image_url: string | null;
      air_date: string | null;
      media_type: Anime["media_type"];
      status: Anime["status"];
      regions: string[];
      episode_count: number | null;
    };
    source: SourceCode;
    external_id: string;
    external_url: string;
    title: string;
    confidence: number;
    disposition: "automatic" | "review" | "reject";
    evidence: {
      title_similarity?: number;
      date_similarity?: number;
      media_similarity?: number;
      episode_similarity?: number;
      installment_conflict?: boolean;
      reasons?: string[];
      [key: string]: unknown;
    };
    generated_at: string;
    resolved_at: string | null;
    current_review_status: string | null;
  }[];
};

export type MappingResolutionResponse = {
  data_mode: "demo" | "live";
  candidate_id: number;
  decision: "approved" | "rejected";
  external_mapping_id: number | null;
  resolved_at: string;
};

export type HistoryPoint = {
  sampled_at: string;
  score: number;
  rating_count: number;
};

export type HistoryResponse = {
  data_mode: "demo" | "live";
  history: {
    anime_id: string;
    series: { source: SourceCode; points: HistoryPoint[] }[];
    composite: { sampled_at: string; score: number; source_count: number }[];
    episodes: { episode_number: number; air_date: string; title: string | null }[];
    freshness: {
      source: SourceCode;
      status: "fresh" | "stale" | "unavailable";
      last_success_at: string | null;
      last_attempt_at: string | null;
      message: string | null;
    }[];
  };
  sampling_policy: Record<string, string>;
};

import { demoFallback } from "./demoFallback";

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/v1").replace(/\/$/, "");

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: { Accept: "application/json", ...init?.headers },
    });
    if (!response.ok) throw new Error(`API 请求失败（${response.status}）`);
    return response.json() as Promise<T>;
  } catch (error) {
    if (import.meta.env.VITE_DISABLE_DEMO_FALLBACK === "true") throw error;
    return demoFallback(path, init) as Promise<T>;
  }
}

export type RankingFilters = {
  year: string;
  quarter: string;
  region: string;
  mediaType: string;
  mode: "unrestricted" | "threshold";
  bangumiMin: string;
  malMin: string;
};

export function getRankings(
  filters: RankingFilters,
  page = 1,
  pageSize = 50,
): Promise<RankingResponse> {
  const params = new URLSearchParams();
  if (filters.year) params.set("year", filters.year);
  if (filters.quarter) params.set("quarter", filters.quarter);
  if (filters.region) params.set("region", filters.region);
  if (filters.mediaType) params.set("media_type", filters.mediaType);
  params.set("mode", filters.mode);
  if (filters.mode === "threshold") {
    params.set("bangumi_min", filters.bangumiMin || "1000");
    params.set("mal_min", filters.malMin || "20000");
  }
  params.set("page", String(page));
  params.set("page_size", String(pageSize));
  return request<RankingResponse>(`/rankings?${params.toString()}`);
}

export function searchAnime(query: string): Promise<SearchResponse> {
  return request<SearchResponse>(`/anime/search?q=${encodeURIComponent(query)}&limit=50`);
}

export function getAnime(animeId: string): Promise<DetailResponse> {
  return request<DetailResponse>(`/anime/${encodeURIComponent(animeId)}`);
}

export function getDataQuality(): Promise<DataQualityResponse> {
  return request<DataQualityResponse>("/data/quality");
}

export function getMappingCandidates(
  offset = 0,
  limit = 25,
): Promise<MappingCandidatePage> {
  return request<MappingCandidatePage>(
    `/mappings/candidates?source=mal&disposition=review&unresolved_only=true&limit=${limit}&offset=${offset}`,
  );
}

export function resolveMappingCandidate(
  candidateId: number,
  decision: "approved" | "rejected",
  token: string,
): Promise<MappingResolutionResponse> {
  return request<MappingResolutionResponse>(`/mappings/candidates/${candidateId}/resolve`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Review-Token": token },
    body: JSON.stringify({ decision }),
  });
}

export type SemanticResponse = {
  data_mode: "demo" | "live";
  query: string;
  engine: string;
  model_name: string;
  parsed_intent: {
    year: number | null;
    regions: string[];
    media_types: Anime["media_type"][];
    statuses: Anime["status"][];
    tags: string[];
  };
  results: { anime: Anime; confidence: number; reasons: string[] }[];
  elapsed_ms: number;
};

export function semanticSearch(query: string): Promise<SemanticResponse> {
  return request<SemanticResponse>("/anime/semantic-search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, limit: 10 }),
  });
}

export function getCatalogIndex(): Promise<{ data_mode: "demo" | "live"; total: number; items: Anime[] }> {
  return request("/anime/index?limit=500");
}

export function getRatingHistory(animeId: string): Promise<HistoryResponse> {
  return request<HistoryResponse>(`/anime/${encodeURIComponent(animeId)}/ratings/history`);
}
