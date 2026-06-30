import { DragEvent, FormEvent, useEffect, useMemo, useState, type CSSProperties } from "react";
import type { Anime } from "../api/client";
import { searchAnime } from "../api/client";
import { exportTierList } from "./export";
import {
  createInitialTierState,
  createLibrary,
  loadTierState,
  moveAnime,
  removeAnime,
  reorderAnime,
  saveTierState,
  tierDefinitions,
  toTierAnime,
  type TierAnime,
  type TierLibrary,
  type TierLocation,
} from "./model";

function findAnime(library: TierLibrary, animeId: string): TierAnime | undefined {
  return Object.values(library.entries).flat().find((anime) => anime.id === animeId);
}

type AnimeCardProps = {
  anime: TierAnime;
  location: TierLocation;
  onMove: (target: TierLocation) => void;
  onReorder: (offset: -1 | 1) => void;
  onRemove: () => void;
  onDragStart: (event: DragEvent) => void;
};

function TierAnimeCard({ anime, location, onMove, onReorder, onRemove, onDragStart }: AnimeCardProps) {
  const title = anime.name_cn ?? anime.canonical_name;
  return (
    <article className="tier-anime-card" draggable onDragStart={onDragStart} data-anime-id={anime.id}>
      <span className="tier-card-mark">{title.slice(0, 1)}</span>
      <div><strong>{title}</strong><small>{anime.media_type.toUpperCase()} · {anime.air_date.slice(0, 4)}</small></div>
      <select aria-label={`移动 ${title}`} value={location} onChange={(event) => onMove(event.target.value as TierLocation)}>
        <option value="pool">未分档</option>
        {tierDefinitions.map((tier) => <option key={tier.id} value={tier.id}>{tier.label}</option>)}
      </select>
      <div className="tier-card-actions"><button aria-label={`${title} 向前`} type="button" onClick={() => onReorder(-1)}>←</button><button aria-label={`${title} 向后`} type="button" onClick={() => onReorder(1)}>→</button><button aria-label={`移除 ${title}`} type="button" onClick={onRemove}>×</button></div>
    </article>
  );
}

export function TierList({ catalog }: { catalog: Anime[] }) {
  const [state, setState] = useState(loadTierState);
  const [newLibraryName, setNewLibraryName] = useState("");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Anime[]>([]);
  const [message, setMessage] = useState("");
  const activeLibrary = state.libraries.find((library) => library.id === state.activeLibraryId) ?? state.libraries[0];
  const existingIds = useMemo(() => new Set(Object.values(activeLibrary.entries).flat().map((anime) => anime.id)), [activeLibrary]);

  useEffect(() => saveTierState(state), [state]);

  const setActiveLibrary = (update: (library: TierLibrary) => TierLibrary) => {
    setState((current) => ({ ...current, libraries: current.libraries.map((library) => library.id === current.activeLibraryId ? update(library) : library) }));
  };

  const createNewLibrary = (event: FormEvent) => {
    event.preventDefault();
    const library = createLibrary(newLibraryName, `library-${Date.now()}`);
    setState((current) => ({ ...current, activeLibraryId: library.id, libraries: [...current.libraries, library] }));
    setNewLibraryName("");
  };

  const deleteActiveLibrary = () => {
    setState((current) => {
      const libraries = current.libraries.filter((library) => library.id !== current.activeLibraryId);
      if (!libraries.length) return createInitialTierState();
      return { ...current, activeLibraryId: libraries[0].id, libraries };
    });
  };

  const addAnime = (anime: Anime) => {
    setState((current) => moveAnime(current, current.activeLibraryId, toTierAnime(anime), "pool"));
    setMessage(`已将「${anime.name_cn ?? anime.canonical_name}」加入未分档区`);
  };

  const addSelected = () => {
    const selected = catalog.filter((anime) => selectedIds.has(anime.id));
    setState((current) => selected.reduce((next, anime) => moveAnime(next, next.activeLibraryId, toTierAnime(anime), "pool"), current));
    setSelectedIds(new Set());
    setMessage(`已批量加入 ${selected.length} 部动画`);
  };

  const submitSearch = async (event: FormEvent) => {
    event.preventDefault();
    if (!query.trim()) return;
    try {
      const response = await searchAnime(query.trim());
      setResults(response.items);
      setMessage(response.items.length ? `找到 ${response.items.length} 个目录条目` : "没有找到匹配条目");
    } catch (error) {
      setMessage((error as Error).message);
    }
  };

  const dropAnime = (event: DragEvent, target: TierLocation, targetIndex?: number) => {
    event.preventDefault();
    const anime = findAnime(activeLibrary, event.dataTransfer.getData("text/plain"));
    if (anime) setState((current) => moveAnime(current, current.activeLibraryId, anime, target, targetIndex));
  };

  const renderZone = (location: TierLocation, label: string, description: string, color?: string) => (
    <div className={`tier-row ${location === "pool" ? "pool-row" : ""}`} key={location} onDragOver={(event) => event.preventDefault()} onDrop={(event) => dropAnime(event, location)}>
      <div className="tier-label" style={{ "--tier-color": color ?? "#526e77" } as CSSProperties}><strong>{label}</strong><small>{description}</small></div>
      <div className="tier-dropzone">
        {activeLibrary.entries[location].map((anime, index) => <div key={anime.id} onDragOver={(event) => event.preventDefault()} onDrop={(event) => { event.stopPropagation(); dropAnime(event, location, index); }}><TierAnimeCard anime={anime} location={location} onDragStart={(event) => event.dataTransfer.setData("text/plain", anime.id)} onMove={(target) => setState((current) => moveAnime(current, current.activeLibraryId, anime, target))} onReorder={(offset) => setState((current) => reorderAnime(current, current.activeLibraryId, location, anime.id, offset))} onRemove={() => setState((current) => removeAnime(current, current.activeLibraryId, anime.id))} /></div>)}
        {!activeLibrary.entries[location].length && <span className="drop-hint">拖到这里</span>}
      </div>
    </div>
  );

  return (
    <section className="tier-section" id="tier-list">
      <div className="section-heading"><div><p className="eyebrow">LOCAL-FIRST TIER LAB</p><h2>从夯到拉</h2><p>创建自己的动画片库。拖拽分档、档内排序与所有改动仅保存在当前浏览器。</p></div><div className="privacy-pill">无账号 · 不上传</div></div>

      <div className="library-toolbar">
        <div className="library-tabs" role="tablist" aria-label="片库列表">{state.libraries.map((library) => <button className={library.id === activeLibrary.id ? "active" : ""} role="tab" aria-selected={library.id === activeLibrary.id} type="button" key={library.id} onClick={() => setState((current) => ({ ...current, activeLibraryId: library.id }))}>{library.name}<small>{Object.values(library.entries).flat().length} 部</small></button>)}</div>
        <form onSubmit={createNewLibrary}><input aria-label="新片库名称" value={newLibraryName} onChange={(event) => setNewLibraryName(event.target.value)} placeholder="新片库名称" /><button type="submit">新建片库</button></form>
      </div>

      <div className="library-meta">
        <label>片库名称<input aria-label="片库名称" value={activeLibrary.name} onChange={(event) => setActiveLibrary((library) => ({ ...library, name: event.target.value || "未命名片库" }))} /></label>
        <span>{Object.values(activeLibrary.entries).flat().length} 部动画 · 自动本地保存</span>
        <button type="button" onClick={() => exportTierList(activeLibrary).catch((error: Error) => setMessage(error.message))}>导出长图</button>
        <button className="danger-button" type="button" onClick={deleteActiveLibrary}>删除片库</button>
      </div>

      <div className="tier-source-panel">
        <div><p className="eyebrow">ADD FROM RANKING</p><h3>从当前榜单批量加入</h3><div className="candidate-grid">{catalog.map((anime) => <label className={existingIds.has(anime.id) ? "added" : ""} key={anime.id}><input type="checkbox" aria-label={`选择 ${anime.name_cn ?? anime.canonical_name}`} disabled={existingIds.has(anime.id)} checked={selectedIds.has(anime.id)} onChange={(event) => setSelectedIds((current) => { const next = new Set(current); event.target.checked ? next.add(anime.id) : next.delete(anime.id); return next; })} /><span><strong>{anime.name_cn ?? anime.canonical_name}</strong><small>{existingIds.has(anime.id) ? "已在片库" : anime.media_type.toUpperCase()}</small></span></label>)}</div><button className="add-selected" type="button" disabled={!selectedIds.size} onClick={addSelected}>加入所选（{selectedIds.size}）</button></div>
        <div><p className="eyebrow">CATALOG SEARCH</p><h3>搜索后加入</h3><form className="tier-search" onSubmit={submitSearch}><input aria-label="片库动画搜索" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="输入中文名、别名或标签" /><button type="submit">搜索</button></form><div className="tier-search-results">{results.map((anime) => <button type="button" disabled={existingIds.has(anime.id)} key={anime.id} onClick={() => addAnime(anime)}><span><strong>{anime.name_cn ?? anime.canonical_name}</strong><small>{anime.canonical_name}</small></span><b>{existingIds.has(anime.id) ? "已加入" : "+ 加入"}</b></button>)}</div></div>
      </div>
      {message && <p className="tier-message" role="status">{message}</p>}

      <div className="tier-board" data-testid="tier-board">
        {renderZone("pool", "待定", "未分档")}
        {tierDefinitions.map((tier) => renderZone(tier.id, tier.label, tier.description, tier.color))}
      </div>
    </section>
  );
}
