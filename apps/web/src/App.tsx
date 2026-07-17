import { FormEvent, useEffect, useState } from "react";
import {
  Anime,
  DataQualityResponse,
  DetailResponse,
  HistoryResponse,
  RankingFilters,
  RankingResponse,
  getAnime,
  getCatalogIndex,
  getDataQuality,
  getRankings,
  getRatingHistory,
  searchAnime,
} from "./api/client";
import { TierList } from "./tier-list/TierList";
import { AiSearch } from "./ai-search/AiSearch";

export function currentSeason(now = new Date()): Pick<RankingFilters, "year" | "quarter"> {
  return {
    year: String(now.getUTCFullYear()),
    quarter: String(Math.floor(now.getUTCMonth() / 3) + 1),
  };
}

const initialFilters: RankingFilters = {
  year: "",
  quarter: "",
  region: "",
  mediaType: "",
  mode: "unrestricted",
  bangumiMin: "1000",
  malMin: "20000",
};

export function rankingYears(now = new Date()) {
  return Array.from(
    { length: now.getUTCFullYear() - 1917 + 1 },
    (_, index) => String(now.getUTCFullYear() - index),
  );
}

export function shouldFallbackToAllTime(
  response: RankingResponse,
  filters: RankingFilters,
  now = new Date(),
) {
  const season = currentSeason(now);
  return response.items.length === 0
    && filters.year === season.year
    && filters.quarter === season.quarter
    && !filters.region
    && !filters.mediaType
    && filters.mode === "unrestricted";
}

const sourceLabels = { bangumi: "Bangumi", mal: "MAL", douban: "豆瓣", filmarks: "Filmarks" };

const qualityStatusLabels = {
  fresh: "正常",
  stale: "部分过期",
  unavailable: "未启用",
};

function formatNumber(value: number) {
  return value.toLocaleString("zh-CN");
}

function formatDateTime(value: string | null) {
  if (!value) return "暂无记录";
  return new Date(value).toLocaleString("zh-CN", { hour12: false });
}

function DataQualityPanel({ quality }: { quality: DataQualityResponse | null }) {
  if (!quality) {
    return <section className="data-quality-section" aria-label="数据质量与同步状态"><div className="empty-state">正在读取数据状态…</div></section>;
  }
  const malCoverage = quality.eligible_anime
    ? Math.round((100 * quality.with_mal_rating) / quality.eligible_anime)
    : 0;
  return (
    <section className="data-quality-section" id="data-quality" aria-label="数据质量与同步状态">
      <div className="section-heading">
        <div>
          <p className="eyebrow">DATA QUALITY / SYNC RADAR</p>
          <h2>数据质量与同步状态</h2>
          <p>把采集进度、来源覆盖率和缺失原因直接摊开，榜单可信度就不靠“玄学滤镜”。</p>
        </div>
        <time>生成时间：{formatDateTime(quality.generated_at)}</time>
      </div>
      <div className="quality-grid">
        <article className="quality-card primary">
          <span>可收录动画</span>
          <strong>{formatNumber(quality.eligible_anime)}</strong>
          <small>总目录 {formatNumber(quality.total_anime)} · 可排行 {formatNumber(quality.rankable_anime)}</small>
        </article>
        <article className="quality-card">
          <span>Bangumi 评分覆盖</span>
          <strong>{formatNumber(quality.with_bangumi_rating)}</strong>
          <small>最近采样：{formatDateTime(quality.latest_rating_sampled_at)}</small>
        </article>
        <article className="quality-card">
          <span>MAL 评分覆盖</span>
          <strong>{malCoverage}%</strong>
          <small>{formatNumber(quality.with_mal_rating)} 已评分 · {formatNumber(quality.missing_mal)} 待匹配</small>
        </article>
        <article className="quality-card">
          <span>双源完整条目</span>
          <strong>{formatNumber(quality.with_both_core_sources)}</strong>
          <small>NSFW 排除 {formatNumber(quality.nsfw_anime)} · 规则排除 {formatNumber(quality.excluded_anime)}</small>
        </article>
      </div>
      {quality.backfill && (
        <div className="backfill-card">
          <div>
            <span>Bangumi 全历史回填</span>
            <strong>{quality.backfill.completed ? "已完成" : `进行到 ${quality.backfill.next_year} 年`}</strong>
            <small>
              {quality.backfill.start_year}–{quality.backfill.end_year} · 已处理 {formatNumber(quality.backfill.processed_pages)} 页 · 发现 {formatNumber(quality.backfill.discovered_count)} 条
            </small>
          </div>
          <div className="progress-meter" aria-label={`历史回填进度 ${quality.backfill.progress_percent}%`}>
            <span style={{ width: `${quality.backfill.progress_percent}%` }} />
          </div>
          {quality.backfill.last_error && <p className="quality-warning">{quality.backfill.last_error}</p>}
        </div>
      )}
      <div className="connector-grid">
        {quality.connectors.map((connector) => (
          <article className={`connector-card ${connector.status}`} key={connector.source}>
            <span>{connector.label}</span>
            <strong>{qualityStatusLabels[connector.status]}</strong>
            <small>
              映射 {formatNumber(connector.mapped_count)} · 评分 {formatNumber(connector.rated_count)}
            </small>
            <time>成功：{formatDateTime(connector.last_success_at)}</time>
            {connector.message && <p>{connector.message}</p>}
          </article>
        ))}
      </div>
      {!!quality.recent_runs.length && (
        <div className="sync-run-strip">
          {quality.recent_runs.slice(0, 3).map((run) => (
            <span key={`${run.source}-${run.job_type}-${run.started_at}`}>
              {sourceLabels[run.source]} / {run.job_type}：{run.status} · +{run.succeeded_count} / !{run.failed_count}
            </span>
          ))}
        </div>
      )}
      <ul className="quality-notes">
        {quality.notes.map((note) => <li key={note}>{note}</li>)}
      </ul>
    </section>
  );
}

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
      <div className="signal-panel-header"><span>COMPOSITE SIGNAL / RELEASE 0.7</span><span className="channel-pill">CH B+M</span></div>
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

type ChartPoint = { sampled_at: string; score: number };

function HistoryChart({ data }: { data: HistoryResponse }) {
  const width = 960;
  const height = 360;
  const left = 58;
  const right = 28;
  const top = 28;
  const bottom = 58;
  const allPoints: ChartPoint[] = [
    ...data.history.series.flatMap((series) => series.points),
    ...data.history.composite,
  ];
  const times = [
    ...allPoints.map((point) => new Date(point.sampled_at).getTime()),
    ...data.history.episodes.map((episode) => new Date(episode.air_date).getTime()),
  ];
  const minTime = Math.min(...times);
  const maxTime = Math.max(...times);
  const scores = allPoints.map((point) => point.score);
  const minScore = Math.floor((Math.min(...scores) - 0.15) * 10) / 10;
  const maxScore = Math.ceil((Math.max(...scores) + 0.15) * 10) / 10;
  const x = (time: string) => left + ((new Date(time).getTime() - minTime) / (maxTime - minTime || 1)) * (width - left - right);
  const y = (score: number) => top + ((maxScore - score) / (maxScore - minScore || 1)) * (height - top - bottom);
  const path = (points: ChartPoint[]) => points.map((point, index) => `${index ? "L" : "M"}${x(point.sampled_at).toFixed(1)} ${y(point.score).toFixed(1)}`).join(" ");
  const gridScores = Array.from({ length: 5 }, (_, index) => minScore + ((maxScore - minScore) * index) / 4);

  return (
    <div className="history-chart-wrap">
      <svg className="history-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Bangumi、MAL 与综合评分历史曲线及分集时间轴">
        {gridScores.map((score) => <g key={score}><line className="chart-grid" x1={left} x2={width - right} y1={y(score)} y2={y(score)} /><text className="chart-axis-label" x={10} y={y(score) + 4}>{score.toFixed(1)}</text></g>)}
        {data.history.episodes.map((episode) => <g className="episode-marker" key={episode.episode_number}><line x1={x(episode.air_date)} x2={x(episode.air_date)} y1={top} y2={height - bottom + 10} /><circle cx={x(episode.air_date)} cy={height - bottom + 16} r="11" /><text x={x(episode.air_date)} y={height - bottom + 20}>{episode.episode_number}</text><title>{episode.title ?? `第 ${episode.episode_number} 话`} · {new Date(episode.air_date).toLocaleDateString("zh-CN")}</title></g>)}
        {data.history.series.map((series) => <g key={series.source}><path className={`history-line ${series.source}`} d={path(series.points)} />{series.points.map((point) => <circle className={`history-dot ${series.source}`} key={point.sampled_at} cx={x(point.sampled_at)} cy={y(point.score)} r="4"><title>{sourceLabels[series.source]} · {point.score.toFixed(2)} · {new Date(point.sampled_at).toLocaleDateString("zh-CN")}</title></circle>)}</g>)}
        <path className="history-line composite" d={path(data.history.composite)} />
      </svg>
    </div>
  );
}

function App() {
  const [filters, setFilters] = useState(initialFilters);
  const [rankings, setRankings] = useState<RankingResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState<Anime[] | null>(null);
  const [detail, setDetail] = useState<DetailResponse | null>(null);
  const [history, setHistory] = useState<HistoryResponse | null>(null);
  const [historyError, setHistoryError] = useState("");
  const [catalogIndex, setCatalogIndex] = useState<Anime[]>([]);
  const [dataQuality, setDataQuality] = useState<DataQualityResponse | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    getRankings(filters)
      .then((data) => {
        if (!active) return;
        if (shouldFallbackToAllTime(data, filters)) {
          setFilters((current) => ({ ...current, year: "", quarter: "" }));
          return;
        }
        setRankings(data);
      })
      .catch((reason: Error) => active && setError(reason.message))
      .finally(() => active && setLoading(false));
    return () => { active = false; };
  }, [filters]);

  useEffect(() => {
    let active = true;
    getRatingHistory("demo-aurora")
      .then((data) => active && setHistory(data))
      .catch((reason: Error) => active && setHistoryError(reason.message));
    return () => { active = false; };
  }, []);

  useEffect(() => {
    getCatalogIndex().then((response) => setCatalogIndex(response.items)).catch(() => setCatalogIndex([]));
  }, []);

  useEffect(() => {
    getDataQuality().then((response) => setDataQuality(response)).catch(() => setDataQuality(null));
  }, []);

  useEffect(() => {
    if (!detail) return undefined;
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setDetail(null);
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [detail]);

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

  const loadMoreRankings = async () => {
    if (!rankings || loadingMore || rankings.items.length >= rankings.total) return;
    setLoadingMore(true);
    setError("");
    try {
      const next = await getRankings(filters, rankings.page + 1, rankings.page_size);
      setRankings({ ...next, items: [...rankings.items, ...next.items] });
    } catch (reason) {
      setError((reason as Error).message);
    } finally {
      setLoadingMore(false);
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
    <div className="app-shell" id="top">
      <a className="skip-link" href="#main-content">跳到主要内容</a>
      <header className="topbar">
        <a className="brand" href="#top" aria-label="番剧示波器首页"><OscilloscopeMark /><span><strong>番剧示波器</strong><small>ANIME OSCILLOSCOPE</small></span></a>
        <nav aria-label="主要导航"><a className="active" href="#rankings">综合榜单</a><a href="#oscilloscope">评分走势</a><a href="#search">动画搜索</a><a href="#ai-search">AI 找番</a><a href="#tier-list">从夯到拉</a><a href="#methodology">评分方法</a></nav>
        <div className="freshness"><i /><span>API / 静态演示就绪</span></div>
      </header>

      <main id="main-content">
        {rankings?.data_mode === "demo" && <div className="demo-banner" role="status"><strong>演示数据模式</strong><span>当前条目均为虚构测试数据，用于验证产品交互；接入 Supabase 后才会切换为真实目录。</span></div>}
        <section className="hero">
          <div className="hero-copy"><p className="eyebrow">MULTI-SOURCE ANIME ANALYTICS</p><h1><span className="headline-line">听见评分的噪声，</span><span className="headline-line signal-text">看见番剧的信号。</span></h1><p className="hero-description">采样 Bangumi 与 MyAnimeList 社区评分，用透明的权重、门槛和数据完整度，观察一部动画如何被看见、讨论与重新评价。</p><div className="hero-actions"><a className="button primary" href="#rankings">查看全历史榜单</a><a className="button ghost" href="#methodology">评分方法</a></div></div>
          <SignalChart />
        </section>

        <section className="metrics" aria-label="项目状态"><article><span>语义向量维度</span><strong>512<small>BGE / 演示回退同维</small></strong></article><article><span>历史采样点</span><strong>{history?.history.composite.length ?? "—"}<small>双源与综合分序列</small></strong></article><article><span>质量门禁</span><strong>88<small>66 API + 18 Web + 4 E2E</small></strong></article><article><span>当前版本</span><strong>0.7<small>作品集演示发布</small></strong></article></section>

        <DataQualityPanel quality={dataQuality} />

        <section className="ranking-section" id="rankings">
          <div className="section-heading"><div><p className="eyebrow">ALL TIME / API DRIVEN</p><h2>全历史综合信号排行榜</h2><p>默认展示全时期，并支持按年份、季度、地区与类型筛选；综合分不会将缺失来源记为零分。</p></div></div>
          <div className="filter-bar" aria-label="榜单筛选">
            <label>年份<select aria-label="年份" value={filters.year} onChange={(e) => updateFilter("year", e.target.value)}><option value="">全时期</option>{rankingYears().map((year) => <option key={year} value={year}>{year}</option>)}</select></label>
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
              {rankings && rankings.items.length < rankings.total && <button className="load-more-rankings" type="button" disabled={loadingMore} onClick={loadMoreRankings}>{loadingMore ? "正在加载…" : `加载更多（已显示 ${rankings.items.length} / ${rankings.total}）`}</button>}
            </div>
          )}
        </section>

        <section className="oscilloscope-section" id="oscilloscope">
          <div className="section-heading"><div><p className="eyebrow">RATING HISTORY / EPISODE TIMELINE</p><h2>历史评分示波器</h2><p>正在观察：极光频率 · 连载期演示序列。圆形节点对应分集播出日期。</p></div><div className="history-legend"><span><i className="bangumi" />Bangumi</span><span><i className="mal" />MAL</span><span><i className="composite" />综合分</span></div></div>
          {historyError && <div className="error-state" role="alert">{historyError}</div>}
          {!history && !historyError && <div className="empty-state">正在读取历史信号…</div>}
          {history && <div className="oscilloscope-card"><HistoryChart data={history} /><div className="history-summary">{history.history.series.map((series) => { const latest = series.points[series.points.length - 1]; const freshness = history.history.freshness.find((item) => item.source === series.source); return <article key={series.source}><span>{sourceLabels[series.source]}</span><strong>{latest?.score.toFixed(2) ?? "—"}</strong><small>{latest?.rating_count.toLocaleString("zh-CN")} 人评分</small><time>{freshness?.last_success_at ? `最后成功更新 ${new Date(freshness.last_success_at).toLocaleString("zh-CN", { hour12: false })}` : "暂无成功采样"}</time><em className={freshness?.status}>{freshness?.status === "fresh" ? "来源正常" : freshness?.status === "stale" ? "使用上次成功快照" : "来源不可用"}</em>{freshness?.message && <p>{freshness.message}</p>}</article>; })}<article className="sampling-card"><span>当前采样节律</span><strong>24h</strong><small>连载期每日采样</small><time>87 个逐日快照</time><em>完结后自动降频并永久保留</em></article></div></div>}
        </section>

        <section className="search-section" id="search"><div><p className="eyebrow">CATALOG SEARCH</p><h2>搜索动画目录</h2><p>中文名、原名、别名和标签均可匹配。</p></div><form className="search-form" onSubmit={submitSearch}><input aria-label="动画搜索" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="例如：潮汐、太空、悬疑" /><button type="submit">搜索信号</button></form>{searchResults !== null && <div className="search-results">{searchResults.map((anime) => <button type="button" key={anime.id} onClick={() => openDetail(anime.id)}><strong>{anime.name_cn ?? anime.canonical_name}</strong><span>{anime.canonical_name}</span></button>)}{searchResults.length === 0 && <p>没有找到匹配条目。</p>}</div>}</section>

        <AiSearch />

        <TierList catalog={rankings?.items.map((item) => item.anime) ?? []} catalogIndex={catalogIndex} />

        <section className="methodology" id="methodology"><div><p className="eyebrow">OPEN METHODOLOGY</p><h2>不是神秘算法，<br />是一台透明仪器。</h2></div><div className="formula-card"><code>Σ(score × α × log(1 + votes))</code><span /><code>Σ(α × log(1 + votes))</code><p>Bangumi α = 1.5 · MAL α = 1.0</p></div><p className="method-copy">评分人数取对数，避免单个平台仅凭体量完全淹没其他社区。无限制榜允许单源条目，但始终标注完整度；门槛榜要求 Bangumi ＞ 1000、MAL ＞ 20000。</p></section>
      </main>

      {detail && <div className="detail-backdrop" role="presentation" onMouseDown={() => setDetail(null)}><aside className="detail-panel" role="dialog" aria-modal="true" aria-labelledby="detail-title" onMouseDown={(e) => e.stopPropagation()}><button className="close-button" aria-label="关闭详情" type="button" onClick={() => setDetail(null)}>×</button><p className="eyebrow">SIGNAL DETAIL</p><h2 id="detail-title">{detail.anime.name_cn ?? detail.anime.canonical_name}</h2><p className="original-title">{detail.anime.canonical_name}</p><div className="detail-score"><strong>{detail.composite_score?.toFixed(2) ?? "—"}</strong><span>综合分<small>{detail.completeness}% 数据完整度</small></span></div><p>{detail.anime.summary}</p><div className="detail-meta"><span>{detail.anime.air_date}</span><span>{detail.anime.media_type.toUpperCase()}</span><span>{detail.anime.regions.join(" / ")}</span><span>{detail.anime.episode_count ? `${detail.anime.episode_count} 集` : "集数未知"}</span></div><SourceRatings anime={detail.anime} /><p className="demo-note">本详情为交互验证数据，不代表 Bangumi 或 MAL 的真实评价。</p></aside></div>}

      <footer><span>番剧示波器 · v0.7.0-demo</span><span>66 API · 18 Web · 4 E2E · Recall@10 0.98</span></footer>
    </div>
  );
}

export default App;
