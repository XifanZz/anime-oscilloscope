import { FormEvent, useEffect, useState } from "react";
import {
  Anime,
  DetailResponse,
  RankingFilters,
  RankingResponse,
  getAnime,
  getRankings,
  searchAnime,
} from "./api/client";

const initialFilters: RankingFilters = {
  year: "2026",
  quarter: "2",
  region: "",
  mediaType: "",
  mode: "unrestricted",
  bangumiMin: "1000",
  malMin: "20000",
};

const sourceLabels = { bangumi: "Bangumi", mal: "MAL", douban: "豆瓣", filmarks: "Filmarks" };

function OscilloscopeMark() {
  return (
    <svg aria-hidden="true" className="brand-mark" viewBox="0 0 52 52">
      <rect x="2" y="2" width="48" height="48" rx="14" />
      <path d="M9 27h8l4-11 8 23 6-18 4 6h5" />
      <circle cx="29" cy="39" r="2.5" />
    </svg>
  );
}

function SignalChart() {
  return (
    <div className="signal-panel" aria-label="评分信号视觉预览">
      <div className="signal-panel-header"><span>COMPOSITE SIGNAL / PHASE 03</span><span className="channel-pill">CH B+M</span></div>
      <svg className="signal-chart" viewBox="0 0 640 260" role="img" aria-label="示意评分曲线">
        <defs><linearGradient id="signalGlow" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stopColor="#7ef7c7" /><stop offset="1" stopColor="#73b7ff" /></linearGradient></defs>
        <path className="signal-area" d="M0 210 C80 198 105 124 172 148 S260 188 320 104 S430 78 474 118 S558 70 640 44 V260 H0Z" />
        <path className="signal-line secondary" d="M0 202 C90 185 116 156 174 165 S268 194 329 128 S438 101 486 133 S564 96 640 82" />
        <path className="signal-line primary-line" d="M0 210 C80 198 105 124 172 148 S260 188 320 104 S430 78 474 118 S558 70 640 44" />
      </svg>
      <div className="signal-legend"><span><i className="legend-line bangumi" />Bangumi × 1.5</span><span><i className="legend-line mal" />MAL × 1.0</span><strong>Σ<small>透明加权</small></strong></div>
    </div>
  );
}

function SourceRatings({ anime }: { anime: Anime }) {
  return (
    <div className="sources">
      {anime.ratings.map((rating) => (
        <span key={rating.source}><b>{rating.source === "bangumi" ? "B" : "M"}</b>{rating.score.toFixed(1)} · {rating.rating_count.toLocaleString("zh-CN")}人</span>
      ))}
      {anime.ratings.length < 2 && <span className="missing-source">MAL · 暂无匹配数据</span>}
    </div>
  );
}

function App() {
  const [filters, setFilters] = useState(initialFilters);
  const [rankings, setRankings] = useState<RankingResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState<Anime[] | null>(null);
  const [detail, setDetail] = useState<DetailResponse | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    getRankings(filters)
      .then((data) => active && setRankings(data))
      .catch((reason: Error) => active && setError(reason.message))
      .finally(() => active && setLoading(false));
    return () => { active = false; };
  }, [filters]);

  const updateFilter = (key: keyof RankingFilters, value: string) => {
    setFilters((current) => ({ ...current, [key]: value }));
  };

  const submitSearch = async (event: FormEvent) => {
    event.preventDefault();
    if (!query.trim()) return;
    setError("");
    try {
      const response = await searchAnime(query.trim());
      setSearchResults(response.items);
    } catch (reason) {
      setError((reason as Error).message);
    }
  };

  const openDetail = async (animeId: string) => {
    setError("");
    try {
      setDetail(await getAnime(animeId));
    } catch (reason) {
      setError((reason as Error).message);
    }
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="番剧示波器首页"><OscilloscopeMark /><span><strong>番剧示波器</strong><small>ANIME OSCILLOSCOPE</small></span></a>
        <nav aria-label="主要导航"><a className="active" href="#rankings">综合榜单</a><a href="#search">动画搜索</a><a href="#methodology">评分方法</a><a aria-disabled="true" href="#roadmap">评分走势 · 即将上线</a></nav>
        <div className="freshness"><i /><span>API 契约已连接</span></div>
      </header>

      <main id="top">
        {rankings?.data_mode === "demo" && <div className="demo-banner" role="status"><strong>演示数据模式</strong><span>当前条目均为虚构测试数据，用于验证产品交互；接入 Supabase 后才会切换为真实目录。</span></div>}
        <section className="hero">
          <div className="hero-copy"><p className="eyebrow">MULTI-SOURCE ANIME ANALYTICS</p><h1><span className="headline-line">听见评分的噪声，</span><span className="headline-line signal-text">看见番剧的信号。</span></h1><p className="hero-description">采样 Bangumi 与 MyAnimeList 社区评分，用透明的权重、门槛和数据完整度，观察一部动画如何被看见、讨论与重新评价。</p><div className="hero-actions"><a className="button primary" href="#rankings">查看当季榜单</a><a className="button ghost" href="#methodology">评分方法</a></div></div>
          <SignalChart />
        </section>

        <section className="metrics" aria-label="项目状态"><article><span>当前数据模式</span><strong>{rankings?.data_mode === "demo" ? "DEMO" : "—"}<small>不伪装成实时数据</small></strong></article><article><span>目录条目</span><strong>{rankings?.total ?? "—"}<small>筛选后的可比较信号</small></strong></article><article><span>评分透明度</span><strong>100%<small>公开公式与来源缺失</small></strong></article><article><span>当前阶段</span><strong>03<small>排行榜、搜索与详情</small></strong></article></section>

        <section className="ranking-section" id="rankings">
          <div className="section-heading"><div><p className="eyebrow">CURRENT SEASON / API DRIVEN</p><h2>综合信号排行榜</h2><p>综合分不会将缺失来源记为零分；数据完整度会与结果同时展示。</p></div></div>
          <div className="filter-bar" aria-label="榜单筛选">
            <label>年份<select aria-label="年份" value={filters.year} onChange={(e) => updateFilter("year", e.target.value)}><option value="">全时期</option><option value="2026">2026</option><option value="2025">2025</option></select></label>
            <label>季度<select aria-label="季度" value={filters.quarter} onChange={(e) => updateFilter("quarter", e.target.value)}><option value="">全部季度</option><option value="1">冬</option><option value="2">春</option><option value="3">夏</option><option value="4">秋</option></select></label>
            <label>地区<select aria-label="地区" value={filters.region} onChange={(e) => updateFilter("region", e.target.value)}><option value="">全部地区</option><option value="CN">中国</option><option value="JP">日本</option><option value="KR">韩国</option></select></label>
            <label>类型<select aria-label="类型" value={filters.mediaType} onChange={(e) => updateFilter("mediaType", e.target.value)}><option value="">全部类型</option><option value="tv">TV</option><option value="web">WEB</option><option value="movie">电影</option><option value="ova">OVA</option></select></label>
            <label>门槛<select aria-label="门槛" value={filters.mode} onChange={(e) => updateFilter("mode", e.target.value)}><option value="unrestricted">无限制榜</option><option value="threshold">默认门槛榜</option></select></label>
            {filters.mode === "threshold" && <><label>Bangumi 人数 ＞<input aria-label="Bangumi 最低评分人数" type="number" min="0" value={filters.bangumiMin} onChange={(e) => updateFilter("bangumiMin", e.target.value)} /></label><label>MAL 人数 ＞<input aria-label="MAL 最低评分人数" type="number" min="0" value={filters.malMin} onChange={(e) => updateFilter("malMin", e.target.value)} /></label></>}
          </div>

          {error && <div className="error-state" role="alert">{error}。请确认本地 API 已启动。</div>}
          {loading ? <div className="empty-state">正在校准信号…</div> : (
            <div className="ranking-table" role="table" aria-label="综合排行榜">
              <div className="ranking-row heading-row" role="row"><span>排名</span><span>动画信号</span><span>来源采样</span><span>综合分</span><span>完整度</span></div>
              {rankings?.items.map((item) => <div className="ranking-row" key={item.anime.id} role="row"><strong className="rank">{String(item.rank).padStart(2, "0")}</strong><button className="anime-title anime-button" type="button" onClick={() => openDetail(item.anime.id)}><span className="poster-placeholder">{item.anime.name_cn?.slice(0, 1) ?? "A"}</span><span><strong>{item.anime.name_cn ?? item.anime.canonical_name}</strong><small>{item.anime.canonical_name} · {item.anime.media_type.toUpperCase()}</small></span></button><SourceRatings anime={item.anime} /><strong className="score">{item.composite_score.toFixed(2)}<small>/ 10</small></strong><span className={`completeness ${item.completeness < 100 ? "partial" : ""}`}>{item.completeness}%<small>{item.missing_sources.length ? `缺 ${item.missing_sources.map((source) => sourceLabels[source]).join("、")}` : "双源完整"}</small></span></div>)}
              {!rankings?.items.length && <div className="empty-state">当前筛选下没有信号，换个条件试试。</div>}
            </div>
          )}
        </section>

        <section className="search-section" id="search"><div><p className="eyebrow">CATALOG SEARCH</p><h2>搜索动画目录</h2><p>中文名、原名、别名和标签均可匹配。</p></div><form className="search-form" onSubmit={submitSearch}><input aria-label="动画搜索" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="例如：潮汐、太空、悬疑" /><button type="submit">搜索信号</button></form>{searchResults !== null && <div className="search-results">{searchResults.map((anime) => <button type="button" key={anime.id} onClick={() => openDetail(anime.id)}><strong>{anime.name_cn ?? anime.canonical_name}</strong><span>{anime.canonical_name}</span></button>)}{searchResults.length === 0 && <p>没有找到匹配条目。</p>}</div>}</section>

        <section className="methodology" id="methodology"><div><p className="eyebrow">OPEN METHODOLOGY</p><h2>不是神秘算法，<br />是一台透明仪器。</h2></div><div className="formula-card"><code>Σ(score × α × log(1 + votes))</code><span /><code>Σ(α × log(1 + votes))</code><p>Bangumi α = 1.5 · MAL α = 1.0</p></div><p className="method-copy">评分人数取对数，避免单个平台仅凭体量完全淹没其他社区。无限制榜允许单源条目，但始终标注完整度；门槛榜要求 Bangumi ＞ 1000、MAL ＞ 20000。</p></section>
      </main>

      {detail && <div className="detail-backdrop" role="presentation" onMouseDown={() => setDetail(null)}><aside className="detail-panel" role="dialog" aria-modal="true" aria-labelledby="detail-title" onMouseDown={(e) => e.stopPropagation()}><button className="close-button" aria-label="关闭详情" type="button" onClick={() => setDetail(null)}>×</button><p className="eyebrow">SIGNAL DETAIL</p><h2 id="detail-title">{detail.anime.name_cn ?? detail.anime.canonical_name}</h2><p className="original-title">{detail.anime.canonical_name}</p><div className="detail-score"><strong>{detail.composite_score?.toFixed(2) ?? "—"}</strong><span>综合分<small>{detail.completeness}% 数据完整度</small></span></div><p>{detail.anime.summary}</p><div className="detail-meta"><span>{detail.anime.air_date}</span><span>{detail.anime.media_type.toUpperCase()}</span><span>{detail.anime.regions.join(" / ")}</span><span>{detail.anime.episode_count ? `${detail.anime.episode_count} 集` : "集数未知"}</span></div><SourceRatings anime={detail.anime} /><p className="demo-note">本详情为交互验证数据，不代表 Bangumi 或 MAL 的真实评价。</p></aside></div>}

      <footer><span>番剧示波器 · Phase 03</span><span>演示目录 · API 驱动 · 数据状态透明标注</span></footer>
    </div>
  );
}

export default App;
