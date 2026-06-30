import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, vi } from "vitest";
import App from "./App";

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

function jsonResponse(payload: unknown) {
  return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(payload) });
}

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn((input: string | URL | Request) => {
    const url = String(input);
    if (url.includes("/anime/search")) return jsonResponse({ data_mode: "demo", query: "极光", total: 1, items: [anime] });
    if (url.includes("/ratings/history")) return jsonResponse(historyPayload);
    if (url.includes("/anime/demo-aurora")) return jsonResponse({ data_mode: "demo", anime, composite_score: 8.72, completeness: 100, missing_sources: [] });
    return jsonResponse(rankingPayload);
  }));
});

afterEach(() => vi.unstubAllGlobals());

describe("App", () => {
  it("loads API rankings and clearly labels demo data", async () => {
    render(<App />);

    expect(await screen.findByText("极光频率")).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("演示数据模式");
    expect(screen.getByText("8.72")).toBeInTheDocument();
  });

  it("renders dual-source history, composite signal, episodes, and stale-source status", async () => {
    render(<App />);

    expect(await screen.findByRole("img", { name: "Bangumi、MAL 与综合评分历史曲线及分集时间轴" })).toBeInTheDocument();
    expect(screen.getByText("使用上次成功快照")).toBeInTheDocument();
    expect(screen.getByText("继续展示上次成功快照。")).toBeInTheDocument();
  });

  it("requests a new ranking when filters change", async () => {
    render(<App />);
    await screen.findByText("极光频率");

    fireEvent.change(screen.getByLabelText("地区"), { target: { value: "JP" } });

    await waitFor(() => expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("region=JP"),
      expect.any(Object),
    ));
  });

  it("exposes custom source thresholds in threshold mode", async () => {
    render(<App />);
    await screen.findByText("极光频率");

    fireEvent.change(screen.getByLabelText("门槛"), { target: { value: "threshold" } });
    fireEvent.change(await screen.findByLabelText("Bangumi 最低评分人数"), { target: { value: "2500" } });

    await waitFor(() => expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("bangumi_min=2500"),
      expect.any(Object),
    ));
  });

  it("searches the catalog and opens a detail panel", async () => {
    render(<App />);
    await screen.findByText("极光频率");

    fireEvent.change(screen.getByLabelText("动画搜索"), { target: { value: "极光" } });
    fireEvent.click(screen.getByRole("button", { name: "搜索信号" }));
    const resultButtons = await screen.findAllByRole("button", { name: /极光频率/ });
    fireEvent.click(resultButtons.at(-1)!);

    expect(await screen.findByRole("dialog")).toHaveTextContent("100% 数据完整度");
  });
});
