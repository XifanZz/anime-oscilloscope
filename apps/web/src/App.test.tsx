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

function jsonResponse(payload: unknown) {
  return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(payload) });
}

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn((input: string | URL | Request) => {
    const url = String(input);
    if (url.includes("/anime/search")) return jsonResponse({ data_mode: "demo", query: "极光", total: 1, items: [anime] });
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
