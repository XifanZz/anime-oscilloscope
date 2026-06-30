import type { Anime } from "../api/client";
import { matchViewingRecords, parseViewingFile } from "./parser";

const catalog = [
  {
    id: "tidal",
    canonical_name: "Tidal Archive",
    name_cn: "潮汐档案",
    aliases: ["潮汐アーカイブ"],
    summary: "",
    image_url: null,
    air_date: "2026-05-16",
    end_date: null,
    media_type: "web",
    status: "airing",
    regions: ["CN", "JP"],
    episode_count: 10,
    tags: ["悬疑"],
    ratings: [],
    external_links: {},
    updated_at: "2026-06-30T00:00:00Z",
  },
] satisfies Anime[];

describe("Bilibili local import parser", () => {
  it("parses quoted CSV, maps fields, and removes duplicate titles", () => {
    const records = parseViewingFile(
      "history.csv",
      '番剧名称,观看进度,观看时间\r\n"潮汐档案","第 8 话","2026-06-01"\r\n潮汐档案,第 9 话,2026-06-08',
    );

    expect(records).toHaveLength(1);
    expect(records[0]).toMatchObject({ title: "潮汐档案", progress: "第 9 话" });
  });

  it("parses records-wrapped JSON and rejects credential fields", () => {
    expect(parseViewingFile("history.json", JSON.stringify({ records: [{ title: "潮汐档案" }] }))).toHaveLength(1);
    expect(() => parseViewingFile("unsafe.json", JSON.stringify([{ title: "潮汐档案", SESSDATA: "secret" }]))).toThrow("凭证字段");
  });

  it("produces evidence and requires confirmation even for exact matches", () => {
    const matches = matchViewingRecords([{ title: "潮汐档案" }], catalog);

    expect(matches[0].candidates[0]).toMatchObject({ confidence: 1, evidence: "标题或别名完全一致" });
    expect(matches[0].selectedAnimeId).toBe("tidal");
    expect(matches[0].confirmed).toBe(false);
  });
});
