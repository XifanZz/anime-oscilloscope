import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, vi } from "vitest";
import App, { currentSeason, rankingYears, shouldFallbackToAllTime } from "./App";

const anime = {
  id: "demo-aurora",
  canonical_name: "Aurora Frequency",
  name_cn: "极光频率",
  aliases: ["オーロラ周波数"],
  summary: "虚构动画条目。",
  image_url: null,
  air_date: "2026-04-04",
  end_date: null,
  media_type: "tv",
  status: "airing",
  regions: ["JP"],
  episode_count: 12,
  tags: ["科幻"],
  ratings: [
    { source: "bangumi", score: 8.8, rating_count: 12480, sampled_at: "2026-06-30T08:00:00Z" },
    { source: "mal", score: 8.6, rating_count: 84210, sampled_at: "2026-06-30T08:00:00Z" },
  ],
  external_links: {},
  updated_at: "2026-06-30T08:00:00Z",
};

const rankingPayload = {
  data_mode: "demo",
  generated_at: "2026-06-30T08:00:00Z",
  total: 1,
  page: 1,
  page_size: 20,
  items: [{ rank: 1, anime, composite_score: 8.72, completeness: 100, missing_sources: [] }],
};

const historyPayload = {
  data_mode: "demo",
  history: {
    anime_id: "demo-aurora",
    series: [
      { source: "bangumi", points: [{ sampled_at: "2026-04-05T12:00:00Z", score: 8.1, rating_count: 860 }, { sampled_at: "2026-04-12T12:00:00Z", score: 8.3, rating_count: 2150 }] },
      { source: "mal", points: [{ sampled_at: "2026-04-05T12:00:00Z", score: 8.3, rating_count: 12400 }, { sampled_at: "2026-04-12T12:00:00Z", score: 8.2, rating_count: 23100 }] },
    ],
    composite: [{ sampled_at: "2026-04-05T12:00:00Z", score: 8.18, source_count: 2 }, { sampled_at: "2026-04-12T12:00:00Z", score: 8.26, source_count: 2 }],
    episodes: [{ episode_number: 1, air_date: "2026-04-04T12:00:00Z", title: "第 1 话" }],
    freshness: [
      { source: "bangumi", status: "fresh", last_success_at: "2026-04-12T12:00:00Z", last_attempt_at: "2026-04-12T12:00:00Z", message: null },
      { source: "mal", status: "stale", last_success_at: "2026-04-12T12:00:00Z", last_attempt_at: "2026-04-13T12:00:00Z", message: "继续展示上次成功快照。" },
    ],
  },
  sampling_policy: { airing: "daily" },
};

const semanticPayload = {
  data_mode: "demo",
  query: "中日合拍的悬疑WEB动画",
  engine: "hash-512-demo",
  model_name: "deterministic-character-ngram",
  parsed_intent: { year: null, regions: ["CN", "JP"], media_types: ["web"], statuses: [], tags: ["悬疑"] },
  results: [{ anime, confidence: 0.91, reasons: ["制作地区匹配：CN / JP", "标签匹配：悬疑"] }],
  elapsed_ms: 1.2,
};

const dataQualityPayload = {
  data_mode: "demo",
  generated_at: "2026-06-30T08:00:00Z",
  total_anime: 4,
  eligible_anime: 4,
  rankable_anime: 4,
  excluded_anime: 0,
  nsfw_anime: 0,
  with_bangumi_rating: 4,
  with_mal_rating: 3,
  with_both_core_sources: 3,
  missing_mal: 1,
  latest_rating_sampled_at: "2026-06-30T08:00:00Z",
  latest_catalog_updated_at: "2026-06-30T08:00:00Z",
  connectors: [
    { source: "bangumi", label: "Bangumi", enabled: true, status: "fresh", mapped_count: 4, rated_count: 4, latest_sampled_at: "2026-06-30T08:00:00Z", last_success_at: "2026-06-30T08:00:00Z", last_attempt_at: "2026-06-30T08:00:00Z", message: null },
    { source: "mal", label: "MyAnimeList", enabled: true, status: "fresh", mapped_count: 3, rated_count: 3, latest_sampled_at: "2026-06-30T08:00:00Z", last_success_at: "2026-06-30T08:00:00Z", last_attempt_at: "2026-06-30T08:00:00Z", message: null },
  ],
  backfill: { source: "bangumi", start_year: 1917, end_year: 2026, next_year: 1937, next_offset: 0, processed_pages: 20, discovered_count: 143, completed: false, progress_percent: 18, last_error: null, updated_at: "2026-06-30T08:00:00Z" },
  recent_runs: [],
  notes: ["MAL 缺失不会被当作 0 分。"],
};

const mappingCandidatePayload = {
  data_mode: "demo",
  generated_at: "2026-06-30T08:00:00Z",
  total: 1,
  limit: 25,
  offset: 0,
  summary: {
    source: "mal",
    unresolved_review_count: 1,
    automatic_count: 0,
    rejected_count: 0,
    approved_mapping_count: 3,
    unmapped_rankable_count: 1,
  },
  items: [{
    id: 1001,
    anime: {
      id: anime.id,
      bangumi_id: 12345,
      canonical_name: anime.canonical_name,
      name_cn: anime.name_cn,
      image_url: anime.image_url,
      air_date: anime.air_date,
      media_type: anime.media_type,
      status: anime.status,
      regions: anime.regions,
      episode_count: anime.episode_count,
    },
    source: "mal",
    external_id: "60001",
    external_url: "https://myanimelist.net/anime/60001",
    title: "Aurora Frequency Season 1",
    confidence: 0.7421,
    disposition: "review",
    evidence: {
      title_similarity: 0.81,
      date_similarity: 0.9,
      media_similarity: 1,
      episode_similarity: 1,
      installment_conflict: true,
      reasons: ["installment_signature_conflict"],
    },
    generated_at: "2026-06-30T08:00:00Z",
    resolved_at: null,
    current_review_status: null,
  }],
};

function jsonResponse(payload: unknown) {
  return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(payload) });
}

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn((input: string | URL | Request) => {
    const url = String(input);
    if (url.includes("/anime/search")) return jsonResponse({ data_mode: "demo", query: "极光", total: 1, items: [anime] });
    if (url.includes("/anime/semantic-search")) return jsonResponse(semanticPayload);
    if (url.includes("/data/quality")) return jsonResponse(dataQualityPayload);
    if (url.includes("/mappings/candidates")) return jsonResponse(mappingCandidatePayload);
    if (url.includes("/anime/index")) return jsonResponse({ data_mode: "demo", total: 1, items: [anime] });
    if (url.includes("/ratings/history")) return jsonResponse(historyPayload);
    if (url.includes("/anime/demo-aurora")) return jsonResponse({ data_mode: "demo", anime, composite_score: 8.72, completeness: 100, missing_sources: [] });
    return jsonResponse(rankingPayload);
  }));
});

afterEach(() => {
  localStorage.clear();
  vi.unstubAllGlobals();
});

describe("App", () => {
  it("derives the default ranking season from the current date", () => {
    expect(currentSeason(new Date("2026-07-02T00:00:00Z"))).toEqual({
      year: "2026",
      quarter: "3",
    });
  });

  it("offers every historical ranking year from the present back to 1917", () => {
    const years = rankingYears(new Date("2026-07-02T00:00:00Z"));
    expect(years[0]).toBe("2026");
    expect(years.at(-1)).toBe("1917");
    expect(years).toHaveLength(110);
  });

  it("falls back to all-time only when the automatic current season is empty", () => {
    const filters = {
      year: "2026",
      quarter: "3",
      region: "",
      mediaType: "",
      mode: "unrestricted" as const,
      bangumiMin: "1000",
      malMin: "20000",
    };
    const emptyResponse = { ...rankingPayload, data_mode: "demo" as const, total: 0, items: [] };

    expect(shouldFallbackToAllTime(
      emptyResponse,
      filters,
      new Date("2026-07-02T00:00:00Z"),
    )).toBe(true);
    expect(shouldFallbackToAllTime(
      emptyResponse,
      { ...filters, region: "KR" },
      new Date("2026-07-02T00:00:00Z"),
    )).toBe(false);
  });

  it("loads API rankings and clearly labels demo data", async () => {
    render(<App />);

    expect((await screen.findAllByText("极光频率")).length).toBeGreaterThan(1);
    expect(screen.getByRole("status")).toHaveTextContent("演示数据模式");
    expect(screen.getByText("8.72")).toBeInTheDocument();
  });

  it("shows data quality coverage and historical backfill progress", async () => {
    render(<App />);

    expect(await screen.findByText("数据质量与同步状态")).toBeInTheDocument();
    expect(screen.getByText("MAL 评分覆盖")).toBeInTheDocument();
    expect(screen.getByText("进行到 1937 年")).toBeInTheDocument();
  });

  it("renders the MAL human review queue with candidate evidence", async () => {
    render(<App />);

    expect(await screen.findByText("MAL 人工复核清单")).toBeInTheDocument();
    expect(screen.getByText("Aurora Frequency Season 1")).toBeInTheDocument();
    expect(screen.getByText("季度 / 剧场版 / Part 特征冲突")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "确认映射" })).toBeInTheDocument();
  });

  it("renders dual-source history, composite signal, episodes, and stale-source status", async () => {
    render(<App />);

    expect(await screen.findByRole("img", { name: "Bangumi、MAL 与综合评分历史曲线及分集时间轴" })).toBeInTheDocument();
    expect(screen.getByText("使用上次成功快照")).toBeInTheDocument();
    expect(screen.getByText("继续展示上次成功快照。")).toBeInTheDocument();
  });

  it("explains natural-language retrieval results and discloses the active engine", async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "分析这句话" }));

    expect(await screen.findByText("hash-512-demo")).toBeInTheDocument();
    expect(screen.getByText("制作地区匹配：CN / JP")).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("/anime/semantic-search"),
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("requests a new ranking when filters change", async () => {
    render(<App />);
    await screen.findAllByText("极光频率");

    fireEvent.change(screen.getByLabelText("地区"), { target: { value: "JP" } });

    await waitFor(() => expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("region=JP"),
      expect.any(Object),
    ));
  });

  it("exposes custom source thresholds in threshold mode", async () => {
    render(<App />);
    await screen.findAllByText("极光频率");

    fireEvent.change(screen.getByLabelText("门槛"), { target: { value: "threshold" } });
    fireEvent.change(await screen.findByLabelText("Bangumi 最低评分人数"), { target: { value: "2500" } });

    await waitFor(() => expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("bangumi_min=2500"),
      expect.any(Object),
    ));
  });

  it("searches the catalog and opens a detail panel", async () => {
    render(<App />);
    await screen.findAllByText("极光频率");

    fireEvent.change(screen.getByLabelText("动画搜索"), { target: { value: "极光" } });
    fireEvent.click(screen.getByRole("button", { name: "搜索信号" }));
    const resultButtons = await screen.findAllByRole("button", { name: /极光频率/ });
    fireEvent.click(resultButtons.at(-1)!);

    expect(await screen.findByRole("dialog")).toHaveTextContent("100% 数据完整度");
    fireEvent.keyDown(window, { key: "Escape" });
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("adds ranking entries to a local library and moves them into a tier", async () => {
    render(<App />);
    await screen.findByText("从当前榜单批量加入");

    fireEvent.click(screen.getByLabelText("选择 极光频率"));
    fireEvent.click(screen.getByRole("button", { name: "加入所选（1）" }));
    const moveSelect = await screen.findByLabelText("移动 极光频率");
    fireEvent.change(moveSelect, { target: { value: "s" } });

    expect(moveSelect).toHaveValue("s");
    await waitFor(() => expect(localStorage.getItem("anime-oscilloscope:tier-libraries:v1")).toContain('"s":[{"id":"demo-aurora"'));
  });

  it("creates and renames an independent local library", async () => {
    render(<App />);
    await screen.findByText("从当前榜单批量加入");

    fireEvent.change(screen.getByLabelText("新片库名称"), { target: { value: "2026 春番" } });
    fireEvent.click(screen.getByRole("button", { name: "新建片库" }));
    expect(screen.getByRole("tab", { name: /2026 春番/ })).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("片库名称"), { target: { value: "春番补完" } });

    expect(screen.getByRole("tab", { name: /春番补完/ })).toBeInTheDocument();
  });

  it("imports a local JSON file only after explicit candidate confirmation", async () => {
    render(<App />);
    await screen.findByText("B站片单文件导入");
    const file = new File([JSON.stringify([{ title: "极光频率", progress: "第 6 话" }])], "history.json", { type: "application/json" });
    Object.defineProperty(file, "text", { value: () => Promise.resolve(JSON.stringify([{ title: "极光频率", progress: "第 6 话" }])) });

    fireEvent.change(screen.getByLabelText("选择B站片单文件"), { target: { files: [file] } });
    const confirm = await screen.findByLabelText("确认导入 极光频率");
    expect(screen.getByRole("button", { name: "将已确认的 0 部加入当前片库" })).toBeDisabled();
    fireEvent.click(confirm);
    fireEvent.click(screen.getByRole("button", { name: "将已确认的 1 部加入当前片库" }));

    expect(await screen.findByLabelText("移动 极光频率")).toBeInTheDocument();
  });
});
