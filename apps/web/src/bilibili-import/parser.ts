import type { Anime } from "../api/client";

export type ViewingRecord = { title: string; watchedAt?: string; progress?: string };
export type ImportCandidate = { anime: Anime; confidence: number; evidence: string };
export type ImportMatch = { record: ViewingRecord; candidates: ImportCandidate[]; selectedAnimeId: string | null; confirmed: boolean };

const titleKeys = ["title", "name", "anime_title", "bangumi_title", "番剧名称", "标题", "名称"];
const watchedAtKeys = ["watched_at", "time", "date", "观看时间"];
const progressKeys = ["progress", "episode", "观看进度"];
const sensitiveKeys = new Set(["password", "cookie", "sessdata", "token", "access_token"]);

function normalizeKey(key: string) {
  return key.trim().replace(/^\uFEFF/, "").toLocaleLowerCase();
}

function normalizeTitle(title: string) {
  return title.toLocaleLowerCase().replace(/[\s\p{P}\p{S}]/gu, "");
}

function parseCsvRows(text: string): string[][] {
  const rows: string[][] = [];
  let row: string[] = [];
  let field = "";
  let quoted = false;
  for (let index = 0; index < text.length; index += 1) {
    const character = text[index];
    if (character === '"' && quoted && text[index + 1] === '"') {
      field += '"';
      index += 1;
    } else if (character === '"') {
      quoted = !quoted;
    } else if (character === "," && !quoted) {
      row.push(field.trim());
      field = "";
    } else if ((character === "\n" || character === "\r") && !quoted) {
      if (character === "\r" && text[index + 1] === "\n") index += 1;
      row.push(field.trim());
      if (row.some(Boolean)) rows.push(row);
      row = [];
      field = "";
    } else {
      field += character;
    }
  }
  row.push(field.trim());
  if (row.some(Boolean)) rows.push(row);
  return rows;
}

function recordsFromObjects(objects: Record<string, unknown>[]): ViewingRecord[] {
  const records: ViewingRecord[] = [];
  for (const object of objects) {
    const entries = Object.entries(object);
    const normalized = new Map(entries.map(([key, value]) => [normalizeKey(key), value]));
    if ([...normalized.keys()].some((key) => sensitiveKeys.has(key))) {
      throw new Error("文件包含凭证字段；请先删除密码、Cookie、SESSDATA 或 Token");
    }
    const valueFor = (keys: string[]) => keys.map((key) => normalized.get(normalizeKey(key))).find((value) => typeof value === "string" || typeof value === "number");
    const title = valueFor(titleKeys);
    if (title === undefined) continue;
    const watchedAt = valueFor(watchedAtKeys);
    const progress = valueFor(progressKeys);
    records.push({
      title: String(title).trim(),
      watchedAt: watchedAt === undefined ? undefined : String(watchedAt),
      progress: progress === undefined ? undefined : String(progress),
    });
  }
  return records.filter((record) => Boolean(record.title));
}

export function parseViewingFile(filename: string, text: string): ViewingRecord[] {
  let records: ViewingRecord[];
  if (filename.toLowerCase().endsWith(".json")) {
    const parsed: unknown = JSON.parse(text);
    const list = Array.isArray(parsed) ? parsed : (parsed && typeof parsed === "object" && Array.isArray((parsed as { records?: unknown }).records) ? (parsed as { records: unknown[] }).records : null);
    if (!list) throw new Error("JSON 必须是数组，或包含 records 数组");
    records = recordsFromObjects(list.filter((item): item is Record<string, unknown> => Boolean(item) && typeof item === "object" && !Array.isArray(item)));
  } else if (filename.toLowerCase().endsWith(".csv")) {
    const rows = parseCsvRows(text);
    if (rows.length < 2) throw new Error("CSV 至少需要表头和一条记录");
    const headers = rows[0];
    records = recordsFromObjects(rows.slice(1).map((row) => Object.fromEntries(headers.map((header, index) => [header, row[index] ?? ""]))));
  } else {
    throw new Error("仅支持 .csv 或 .json 文件");
  }
  const unique = new Map(records.map((record) => [normalizeTitle(record.title), record]));
  if (!unique.size) throw new Error("没有找到可识别的动画标题列");
  return [...unique.values()];
}

function levenshtein(left: string, right: string): number {
  const previous = Array.from({ length: right.length + 1 }, (_, index) => index);
  for (let leftIndex = 1; leftIndex <= left.length; leftIndex += 1) {
    const current = [leftIndex];
    for (let rightIndex = 1; rightIndex <= right.length; rightIndex += 1) {
      current[rightIndex] = Math.min(
        current[rightIndex - 1] + 1,
        previous[rightIndex] + 1,
        previous[rightIndex - 1] + (left[leftIndex - 1] === right[rightIndex - 1] ? 0 : 1),
      );
    }
    previous.splice(0, previous.length, ...current);
  }
  return previous[right.length];
}

function titleSimilarity(left: string, right: string): number {
  const normalizedLeft = normalizeTitle(left);
  const normalizedRight = normalizeTitle(right);
  if (!normalizedLeft || !normalizedRight) return 0;
  if (normalizedLeft === normalizedRight) return 1;
  if (normalizedLeft.includes(normalizedRight) || normalizedRight.includes(normalizedLeft)) return 0.88;
  return 1 - levenshtein(normalizedLeft, normalizedRight) / Math.max(normalizedLeft.length, normalizedRight.length);
}

export function matchViewingRecords(records: ViewingRecord[], catalog: Anime[]): ImportMatch[] {
  return records.map((record) => {
    const candidates = catalog.map((anime) => {
      const names = [anime.name_cn ?? "", anime.canonical_name, ...anime.aliases];
      const confidence = Math.max(...names.map((name) => titleSimilarity(record.title, name)));
      return {
        anime,
        confidence: Math.round(confidence * 1000) / 1000,
        evidence: confidence === 1 ? "标题或别名完全一致" : confidence >= 0.88 ? "标题包含关系" : "标题相似度候选",
      };
    }).filter((candidate) => candidate.confidence >= 0.45).sort((left, right) => right.confidence - left.confidence).slice(0, 3);
    return {
      record,
      candidates,
      selectedAnimeId: candidates[0]?.anime.id ?? null,
      confirmed: false,
    };
  });
}
