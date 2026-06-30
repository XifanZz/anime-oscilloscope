import type { Anime } from "../api/client";

export const tierDefinitions = [
  { id: "s", label: "夯", description: "反复回味", color: "#ff6f91" },
  { id: "a", label: "顶", description: "强烈推荐", color: "#f6b96d" },
  { id: "b", label: "人", description: "值得一看", color: "#f6df7a" },
  { id: "c", label: "还行", description: "有亮点", color: "#7ef7c7" },
  { id: "d", label: "拉", description: "不太合拍", color: "#73b7ff" },
] as const;

export type TierId = (typeof tierDefinitions)[number]["id"];
export type TierLocation = TierId | "pool";

export type TierAnime = Pick<Anime, "id" | "canonical_name" | "name_cn" | "media_type" | "air_date">;

export type TierLibrary = {
  id: string;
  name: string;
  entries: Record<TierLocation, TierAnime[]>;
};

export type TierState = {
  version: 1;
  activeLibraryId: string;
  libraries: TierLibrary[];
};

export const STORAGE_KEY = "anime-oscilloscope:tier-libraries:v1";
const locations: TierLocation[] = ["s", "a", "b", "c", "d", "pool"];

const emptyEntries = (): TierLibrary["entries"] => ({ s: [], a: [], b: [], c: [], d: [], pool: [] });

export function createLibrary(name = "我的片库", id = `library-${Date.now()}`): TierLibrary {
  return { id, name: name.trim() || "未命名片库", entries: emptyEntries() };
}

function isTierState(value: unknown): value is TierState {
  if (!value || typeof value !== "object") return false;
  const state = value as Partial<TierState>;
  if (state.version !== 1 || typeof state.activeLibraryId !== "string" || !Array.isArray(state.libraries) || !state.libraries.length) return false;
  return state.libraries.every((library) => Boolean(
    library
    && typeof library.id === "string"
    && typeof library.name === "string"
    && library.entries
    && locations.every((location) => Array.isArray(library.entries[location])),
  )) && state.libraries.some((library) => library.id === state.activeLibraryId);
}

export function createInitialTierState(): TierState {
  const library = createLibrary("我的片库", "default");
  return { version: 1, activeLibraryId: library.id, libraries: [library] };
}

export function loadTierState(storage: Pick<Storage, "getItem"> = localStorage): TierState {
  try {
    const raw = storage.getItem(STORAGE_KEY);
    if (!raw) return createInitialTierState();
    const parsed: unknown = JSON.parse(raw);
    return isTierState(parsed) ? parsed : createInitialTierState();
  } catch {
    return createInitialTierState();
  }
}

export function saveTierState(state: TierState, storage: Pick<Storage, "setItem"> = localStorage) {
  storage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function updateLibrary(state: TierState, libraryId: string, update: (library: TierLibrary) => TierLibrary): TierState {
  return { ...state, libraries: state.libraries.map((library) => library.id === libraryId ? update(library) : library) };
}

export function moveAnime(
  state: TierState,
  libraryId: string,
  anime: TierAnime,
  target: TierLocation,
  targetIndex?: number,
): TierState {
  return updateLibrary(state, libraryId, (library) => {
    const entries = Object.fromEntries(Object.entries(library.entries).map(([tier, items]) => [tier, items.filter((item) => item.id !== anime.id)])) as TierLibrary["entries"];
    const insertAt = Math.max(0, Math.min(targetIndex ?? entries[target].length, entries[target].length));
    entries[target] = [...entries[target].slice(0, insertAt), anime, ...entries[target].slice(insertAt)];
    return { ...library, entries };
  });
}

export function removeAnime(state: TierState, libraryId: string, animeId: string): TierState {
  return updateLibrary(state, libraryId, (library) => ({
    ...library,
    entries: Object.fromEntries(Object.entries(library.entries).map(([tier, items]) => [tier, items.filter((item) => item.id !== animeId)])) as TierLibrary["entries"],
  }));
}

export function reorderAnime(state: TierState, libraryId: string, tier: TierLocation, animeId: string, offset: -1 | 1): TierState {
  return updateLibrary(state, libraryId, (library) => {
    const items = [...library.entries[tier]];
    const index = items.findIndex((item) => item.id === animeId);
    const target = index + offset;
    if (index < 0 || target < 0 || target >= items.length) return library;
    [items[index], items[target]] = [items[target], items[index]];
    return { ...library, entries: { ...library.entries, [tier]: items } };
  });
}

export function toTierAnime(anime: Anime): TierAnime {
  const { id, canonical_name, name_cn, media_type, air_date } = anime;
  return { id, canonical_name, name_cn, media_type, air_date };
}
