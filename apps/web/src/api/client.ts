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

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/v1").replace(/\/$/, "");

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, { headers: { Accept: "application/json" } });
  if (!response.ok) {
    throw new Error(`API 请求失败（${response.status}）`);
  }
  return response.json() as Promise<T>;
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

export function getRankings(filters: RankingFilters): Promise<RankingResponse> {
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
  return request<RankingResponse>(`/rankings?${params.toString()}`);
}

export function searchAnime(query: string): Promise<SearchResponse> {
  return request<SearchResponse>(`/anime/search?q=${encodeURIComponent(query)}`);
}

export function getAnime(animeId: string): Promise<DetailResponse> {
  return request<DetailResponse>(`/anime/${encodeURIComponent(animeId)}`);
}

export function getRatingHistory(animeId: string): Promise<HistoryResponse> {
  return request<HistoryResponse>(`/anime/${encodeURIComponent(animeId)}/ratings/history`);
}
