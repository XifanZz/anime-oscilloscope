import { afterEach, expect, it, vi } from "vitest";
import { getCatalogIndex, getRankings, semanticSearch } from "./client";

afterEach(() => vi.unstubAllGlobals());

it("falls back to an explicit static demo when the hosted API is unavailable", async () => {
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("network unavailable")));

  const rankings = await getRankings({ year: "2026", quarter: "2", region: "", mediaType: "", mode: "unrestricted", bangumiMin: "1000", malMin: "20000" });
  const catalog = await getCatalogIndex();
  const semantic = await semanticSearch("中日合拍的悬疑 WEB 连载动画");

  expect(rankings.data_mode).toBe("demo");
  expect(rankings.items[0].anime.name_cn).toBe("极光频率");
  expect(catalog.total).toBe(4);
  expect(semantic.results[0].anime.name_cn).toBe("潮汐档案");
  expect(semantic.engine).toBe("hash-512-static-demo");
});
