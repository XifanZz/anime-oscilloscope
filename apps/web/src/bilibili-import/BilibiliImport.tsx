import { ChangeEvent, useState } from "react";
import type { Anime } from "../api/client";
import { matchViewingRecords, parseViewingFile, type ImportMatch } from "./parser";

export function BilibiliImport({ catalog, onConfirm }: { catalog: Anime[]; onConfirm: (anime: Anime[]) => void }) {
  const [matches, setMatches] = useState<ImportMatch[]>([]);
  const [error, setError] = useState("");
  const [filename, setFilename] = useState("");

  const readFile = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setError("");
    try {
      const records = parseViewingFile(file.name, await file.text());
      setMatches(matchViewingRecords(records, catalog));
      setFilename(file.name);
    } catch (reason) {
      setMatches([]);
      setError((reason as Error).message);
    } finally {
      event.target.value = "";
    }
  };

  const confirmedAnime = matches.flatMap((match) => {
    if (!match.confirmed || !match.selectedAnimeId) return [];
    const candidate = match.candidates.find((item) => item.anime.id === match.selectedAnimeId);
    return candidate ? [candidate.anime] : [];
  });

  const updateMatch = (index: number, update: Partial<ImportMatch>) => {
    setMatches((current) => current.map((match, matchIndex) => matchIndex === index ? { ...match, ...update } : match));
  };

  return (
    <div className="bili-import">
      <div className="bili-import-heading"><div><p className="eyebrow">BILIBILI LOCAL IMPORT</p><h3>B站片单文件导入</h3><p>CSV/JSON 在浏览器本地解析。本站不接收密码、Cookie、SESSDATA 或观看记录原文。</p></div><label className={`file-button ${catalog.length ? "" : "disabled"}`}>{catalog.length ? "选择 CSV / JSON" : "目录索引加载中"}<input aria-label="选择B站片单文件" type="file" accept=".csv,.json,text/csv,application/json" disabled={!catalog.length} onChange={readFile} /></label></div>
      {error && <p className="import-error" role="alert">{error}</p>}
      {matches.length > 0 && <><div className="import-summary"><span>{filename}</span><strong>{matches.length} 条去重记录</strong><small>{matches.filter((match) => match.candidates.length).length} 条有候选 · 必须逐条确认</small></div><div className="import-candidates">{matches.map((match, index) => <article key={`${match.record.title}-${index}`}><label className="confirm-import"><input aria-label={`确认导入 ${match.record.title}`} type="checkbox" disabled={!match.candidates.length} checked={match.confirmed} onChange={(event) => updateMatch(index, { confirmed: event.target.checked })} /><span>{match.record.title}<small>{match.record.progress ? `进度：${match.record.progress}` : "来自本地文件"}</small></span></label>{match.candidates.length ? <select aria-label={`匹配候选 ${match.record.title}`} value={match.selectedAnimeId ?? ""} onChange={(event) => updateMatch(index, { selectedAnimeId: event.target.value, confirmed: false })}>{match.candidates.map((candidate) => <option key={candidate.anime.id} value={candidate.anime.id}>{candidate.anime.name_cn ?? candidate.anime.canonical_name} · {Math.round(candidate.confidence * 100)}% · {candidate.evidence}</option>)}</select> : <span className="no-candidate">暂无本地目录候选</span>}</article>)}</div><button className="confirm-import-button" type="button" disabled={!confirmedAnime.length} onClick={() => { onConfirm(confirmedAnime); setMatches([]); }}>将已确认的 {confirmedAnime.length} 部加入当前片库</button></>}
    </div>
  );
}
