import type { Anime } from "../api/client";
import { buildExportLayout } from "./export";
import {
  STORAGE_KEY,
  createInitialTierState,
  createLibrary,
  loadTierState,
  moveAnime,
  removeAnime,
  reorderAnime,
  saveTierState,
  toTierAnime,
} from "./model";

const anime = toTierAnime({
  id: "anime-1",
  canonical_name: "Signal One",
  name_cn: "信号一号",
  aliases: [],
  summary: "",
  image_url: null,
  air_date: "2026-04-01",
  end_date: null,
  media_type: "tv",
  status: "airing",
  regions: ["JP"],
  episode_count: 12,
  tags: [],
  ratings: [],
  external_links: {},
  updated_at: "2026-06-30T00:00:00Z",
} satisfies Anime);

describe("tier list model", () => {
  it("moves an anime without duplicating it across locations", () => {
    const initial = createInitialTierState();
    const pooled = moveAnime(initial, "default", anime, "pool");
    const ranked = moveAnime(pooled, "default", anime, "s");

    expect(ranked.libraries[0].entries.pool).toHaveLength(0);
    expect(ranked.libraries[0].entries.s.map((item) => item.id)).toEqual(["anime-1"]);
  });

  it("reorders within a tier and removes entries", () => {
    const second = { ...anime, id: "anime-2", name_cn: "信号二号" };
    let state = createInitialTierState();
    state = moveAnime(state, "default", anime, "a");
    state = moveAnime(state, "default", second, "a");
    state = reorderAnime(state, "default", "a", "anime-2", -1);
    expect(state.libraries[0].entries.a.map((item) => item.id)).toEqual(["anime-2", "anime-1"]);

    state = removeAnime(state, "default", "anime-2");
    expect(state.libraries[0].entries.a.map((item) => item.id)).toEqual(["anime-1"]);
  });

  it("persists versioned state and recovers from invalid storage", () => {
    const memory = new Map<string, string>();
    const storage = {
      getItem: (key: string) => memory.get(key) ?? null,
      setItem: (key: string, value: string) => memory.set(key, value),
    };
    const state = createInitialTierState();
    saveTierState(state, storage);
    expect(loadTierState(storage)).toEqual(state);

    memory.set(STORAGE_KEY, "not-json");
    expect(loadTierState(storage).activeLibraryId).toBe("default");

    memory.set(STORAGE_KEY, JSON.stringify({ version: 1, activeLibraryId: "broken", libraries: [{ id: "broken", name: "残缺" }] }));
    expect(loadTierState(storage).activeLibraryId).toBe("default");
  });

  it("grows export height when a tier wraps to another card row", () => {
    const library = createLibrary("测试", "test");
    const initialHeight = buildExportLayout(library).height;
    library.entries.s = Array.from({ length: 7 }, (_, index) => ({ ...anime, id: `anime-${index}` }));

    expect(buildExportLayout(library).height).toBeGreaterThan(initialHeight);
  });
});
