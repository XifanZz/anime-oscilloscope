import type {
  Anime,
  DetailResponse,
  HistoryResponse,
  RankedAnime,
  RankingResponse,
  SemanticResponse,
  SourceCode,
} from "./client";

const sampledAt = "2026-06-30T08:00:00Z";

const rating = (source: SourceCode, score: number, rating_count: number) => ({
  source,
  score,
  rating_count,
  sampled_at: sampledAt,
});

export const demoCatalog: Anime[] = [
  {
    id: "demo-aurora", canonical_name: "Aurora Frequency", name_cn: "极光频率", aliases: ["オーロラ周波数"],
    summary: "用于验证多源排行榜与评分走势的虚构科幻音乐动画。", image_url: null, air_date: "2026-04-04", end_date: null,
    media_type: "tv", status: "airing", regions: ["JP"], episode_count: 12, tags: ["科幻", "音乐"],
    ratings: [rating("bangumi", 8.8, 12480), rating("mal", 8.6, 84210)], external_links: {}, updated_at: sampledAt,
  },
  {
    id: "demo-tidal", canonical_name: "Tidal Archive", name_cn: "潮汐档案", aliases: ["潮汐アーカイブ"],
    summary: "用于验证地区、类型与门槛筛选的虚构中日合拍悬疑 WEB 动画。", image_url: null, air_date: "2026-05-16", end_date: null,
    media_type: "web", status: "airing", regions: ["CN", "JP"], episode_count: 10, tags: ["悬疑", "合拍"],
    ratings: [rating("bangumi", 8.6, 7021), rating("mal", 8.2, 46908)], external_links: {}, updated_at: sampledAt,
  },
  {
    id: "demo-lantern", canonical_name: "Lanterns Beyond Orbit", name_cn: "轨道外的灯", aliases: ["궤도 밖의 등불"],
    summary: "用于验证单一来源、数据完整度与电影筛选的虚构韩国动画。", image_url: null, air_date: "2025-10-02", end_date: "2025-10-02",
    media_type: "movie", status: "finished", regions: ["KR"], episode_count: 1, tags: ["太空", "剧情"],
    ratings: [rating("bangumi", 8.3, 2604)], external_links: {}, updated_at: sampledAt,
  },
  {
    id: "demo-paper-moon", canonical_name: "Paper Moon Protocol", name_cn: "纸月协议", aliases: ["ペーパームーン・プロトコル"],
    summary: "用于验证评分人数门槛的虚构奇幻 OVA。", image_url: null, air_date: "2026-06-01", end_date: "2026-06-01",
    media_type: "ova", status: "finished", regions: ["JP"], episode_count: 2, tags: ["奇幻"],
    ratings: [rating("bangumi", 7.9, 480), rating("mal", 8.1, 6500)], external_links: {}, updated_at: sampledAt,
  },
];

function composite(anime: Anime): number {
  const weighted = anime.ratings.map((item) => {
    const weight = (item.source === "bangumi" ? 1.5 : 1) * Math.log1p(item.rating_count);
    return { value: item.score * weight, weight };
  });
  return weighted.reduce((sum, item) => sum + item.value, 0) / weighted.reduce((sum, item) => sum + item.weight, 0);
}

function ranked(anime: Anime): RankedAnime {
  const sources = new Set(anime.ratings.map((item) => item.source));
  const missing_sources = (["bangumi", "mal"] as SourceCode[]).filter((source) => !sources.has(source));
  return { rank: 0, anime, composite_score: composite(anime), completeness: (2 - missing_sources.length) * 50, missing_sources };
}

function ranking(url: URL): RankingResponse {
  const year = Number(url.searchParams.get("year") || 0);
  const quarter = Number(url.searchParams.get("quarter") || 0);
  const region = url.searchParams.get("region");
  const mediaType = url.searchParams.get("media_type");
  const threshold = url.searchParams.get("mode") === "threshold";
  const bangumiMin = Number(url.searchParams.get("bangumi_min") || 1000);
  const malMin = Number(url.searchParams.get("mal_min") || 20000);
  const items = demoCatalog.filter((anime) => {
    const date = new Date(`${anime.air_date}T00:00:00Z`);
    if (year && date.getUTCFullYear() !== year) return false;
    if (quarter && Math.floor(date.getUTCMonth() / 3) + 1 !== quarter) return false;
    if (region && !anime.regions.includes(region)) return false;
    if (mediaType && anime.media_type !== mediaType) return false;
    if (!threshold) return true;
    const counts = Object.fromEntries(anime.ratings.map((item) => [item.source, item.rating_count]));
    return (counts.bangumi ?? 0) >= bangumiMin && (counts.mal ?? 0) >= malMin;
  }).map(ranked).sort((left, right) => right.composite_score - left.composite_score)
    .map((item, index) => ({ ...item, rank: index + 1 }));
  return { data_mode: "demo", generated_at: sampledAt, total: items.length, page: 1, page_size: 20, items };
}

function detail(anime: Anime): DetailResponse {
  const item = ranked(anime);
  return { data_mode: "demo", anime, composite_score: item.composite_score, completeness: item.completeness, missing_sources: item.missing_sources };
}

const historyDates = ["2026-04-05", "2026-04-19", "2026-05-03", "2026-05-17", "2026-06-07", "2026-06-30"];

function history(): HistoryResponse {
  const makePoints = (scores: number[], start: number, end: number) => scores.map((score, index) => ({
    sampled_at: `${historyDates[index]}T08:00:00Z`, score,
    rating_count: Math.round(start + ((end - start) * index) / (scores.length - 1)),
  }));
  const bangumi = makePoints([8.12, 8.28, 8.41, 8.55, 8.71, 8.8], 860, 12480);
  const mal = makePoints([8.34, 8.29, 8.37, 8.43, 8.51, 8.6], 12400, 84210);
  return {
    data_mode: "demo",
    history: {
      anime_id: "demo-aurora", series: [{ source: "bangumi", points: bangumi }, { source: "mal", points: mal }],
      composite: bangumi.map((point, index) => ({ sampled_at: point.sampled_at, score: Number(((point.score * 1.5 + mal[index].score) / 2.5).toFixed(2)), source_count: 2 })),
      episodes: Array.from({ length: 12 }, (_, index) => ({ episode_number: index + 1, air_date: new Date(Date.UTC(2026, 3, 4 + index * 7, 12)).toISOString(), title: `第 ${index + 1} 话` })),
      freshness: [
        { source: "bangumi", status: "fresh", last_success_at: sampledAt, last_attempt_at: sampledAt, message: null },
        { source: "mal", status: "stale", last_success_at: sampledAt, last_attempt_at: "2026-06-30T12:00:00Z", message: "演示：最近一次请求失败，继续展示上次成功快照。" },
      ],
    },
    sampling_policy: { airing: "daily", finished_0_3_months: "weekly", finished_3_months_3_years: "monthly", older_than_3_years: "yearly" },
  };
}

function semantic(query: string): SemanticResponse {
  const lowered = query.toLowerCase();
  const regions = lowered.includes("中日合拍") ? ["CN", "JP"] : lowered.includes("韩国") ? ["KR"] : lowered.includes("日本") ? ["JP"] : [];
  const mediaTypes: Anime["media_type"][] = lowered.includes("web") || lowered.includes("网番") ? ["web"] : lowered.includes("电影") ? ["movie"] : [];
  const tags = ["科幻", "音乐", "悬疑", "合拍", "太空", "剧情", "奇幻"].filter((tag) => query.includes(tag));
  const statuses: Anime["status"][] = lowered.includes("连载") || lowered.includes("在播") ? ["airing"] : lowered.includes("完结") ? ["finished"] : [];
  const results = demoCatalog.filter((anime) =>
    (!regions.length || regions.every((region) => anime.regions.includes(region))) &&
    (!mediaTypes.length || mediaTypes.includes(anime.media_type)) &&
    (!tags.length || tags.some((tag) => anime.tags.includes(tag))) &&
    (!statuses.length || statuses.includes(anime.status)),
  ).map((anime) => ({ anime, confidence: 0.91, reasons: [
    ...(regions.length ? [`制作地区匹配：${regions.join(" / ")}`] : []),
    ...(mediaTypes.length ? [`作品类型匹配：${anime.media_type.toUpperCase()}`] : []),
    ...(tags.length ? [`标签匹配：${tags.filter((tag) => anime.tags.includes(tag)).join("、")}`] : []),
    "静态演示语义索引匹配",
  ] }));
  return {
    data_mode: "demo", query, engine: "hash-512-static-demo", model_name: "deterministic-character-ngram",
    parsed_intent: { year: null, regions, media_types: mediaTypes, statuses, tags }, results, elapsed_ms: 0.4,
  };
}

export async function demoFallback(path: string, init?: RequestInit): Promise<unknown> {
  const url = new URL(path, "https://demo.invalid");
  if (url.pathname === "/rankings") return ranking(url);
  if (url.pathname === "/anime/index") return { data_mode: "demo", total: demoCatalog.length, items: demoCatalog };
  if (url.pathname === "/anime/search") {
    const query = (url.searchParams.get("q") || "").toLowerCase();
    const items = demoCatalog.filter((anime) => [anime.name_cn, anime.canonical_name, ...anime.aliases].some((name) => name?.toLowerCase().includes(query)));
    return { data_mode: "demo", query, total: items.length, items };
  }
  if (url.pathname.endsWith("/ratings/history")) return history();
  if (url.pathname === "/anime/semantic-search") {
    const body = JSON.parse(String(init?.body || "{}")) as { query?: string };
    return semantic(body.query || "");
  }
  const match = url.pathname.match(/^\/anime\/([^/]+)$/);
  if (match) {
    const anime = demoCatalog.find((item) => item.id === decodeURIComponent(match[1]));
    if (anime) return detail(anime);
  }
  throw new Error("演示数据中没有此条目");
}
