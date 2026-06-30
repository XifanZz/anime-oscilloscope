type RankingPreview = {
  rank: number;
  title: string;
  titleOriginal: string;
  score: string;
  bangumi: string;
  mal: string;
  signal: "up" | "steady" | "new";
};

const previewRankings: RankingPreview[] = [
  {
    rank: 1,
    title: "演示动画 α",
    titleOriginal: "DESIGN PREVIEW ALPHA",
    score: "8.72",
    bangumi: "8.8 · 12,480人",
    mal: "8.6 · 84,210人",
    signal: "up",
  },
  {
    rank: 2,
    title: "演示动画 β",
    titleOriginal: "DESIGN PREVIEW BETA",
    score: "8.41",
    bangumi: "8.6 · 7,021人",
    mal: "8.2 · 46,908人",
    signal: "steady",
  },
  {
    rank: 3,
    title: "演示动画 γ",
    titleOriginal: "DESIGN PREVIEW GAMMA",
    score: "8.18",
    bangumi: "8.3 · 2,604人",
    mal: "8.0 · 23,117人",
    signal: "new",
  },
];

const navigation = ["当季信号", "综合榜单", "评分示波器", "从夯到拉", "AI 找番"];

function OscilloscopeMark() {
  return (
    <svg aria-hidden="true" className="brand-mark" viewBox="0 0 52 52">
      <rect x="2" y="2" width="48" height="48" rx="14" />
      <path d="M9 27h8l4-11 8 23 6-18 4 6h5" />
      <circle cx="29" cy="39" r="2.5" />
    </svg>
  );
}

function App() {
  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="番剧示波器首页">
          <OscilloscopeMark />
          <span>
            <strong>番剧示波器</strong>
            <small>ANIME OSCILLOSCOPE</small>
          </span>
        </a>

        <nav aria-label="主要导航">
          {navigation.map((item, index) => (
            <a className={index === 0 ? "active" : ""} href={`#section-${index}`} key={item}>
              {item}
            </a>
          ))}
        </nav>

        <div className="freshness" title="第一阶段使用设计预览数据">
          <i />
          <span>结构信号正常</span>
        </div>
      </header>

      <main id="top">
        <section className="hero" id="section-0">
          <div className="hero-copy">
            <p className="eyebrow">2026 · SUMMER SIGNAL PREVIEW</p>
            <h1>
              <span className="headline-line">听见评分的噪声，</span>
              <span className="headline-line signal-text">看见番剧的信号。</span>
            </h1>
            <p className="hero-description">
              从 Bangumi 与 MyAnimeList 采样社区评分，用透明的权重和时间序列观察一部动画如何被看见、讨论与重新评价。
            </p>
            <div className="hero-actions">
              <a className="button primary" href="#rankings">查看当季榜单</a>
              <a className="button ghost" href="#methodology">评分方法</a>
            </div>
          </div>

          <div className="signal-panel" aria-label="评分信号设计预览">
            <div className="signal-panel-header">
              <span>LIVE SIGNAL / 设计预览</span>
              <span className="channel-pill">CH A+B</span>
            </div>
            <svg className="signal-chart" viewBox="0 0 640 260" role="img" aria-label="示意评分曲线">
              <defs>
                <linearGradient id="signalGlow" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0" stopColor="#7ef7c7" />
                  <stop offset="1" stopColor="#73b7ff" />
                </linearGradient>
              </defs>
              <path className="signal-area" d="M0 210 C80 198 105 124 172 148 S260 188 320 104 S430 78 474 118 S558 70 640 44 V260 H0Z" />
              <path className="signal-line secondary" d="M0 202 C90 185 116 156 174 165 S268 194 329 128 S438 101 486 133 S564 96 640 82" />
              <path className="signal-line primary-line" d="M0 210 C80 198 105 124 172 148 S260 188 320 104 S430 78 474 118 S558 70 640 44" />
              {[172, 320, 474, 592].map((x) => (
                <circle cx={x} cy={x === 172 ? 148 : x === 320 ? 104 : x === 474 ? 118 : 65} key={x} r="5" />
              ))}
            </svg>
            <div className="signal-legend">
              <span><i className="legend-line bangumi" />Bangumi × 1.5</span>
              <span><i className="legend-line mal" />MAL × 1.0</span>
              <strong>8.72<small>综合信号</small></strong>
            </div>
          </div>
        </section>

        <section className="metrics" aria-label="项目状态">
          <article>
            <span>数据源</span>
            <strong>2<small>个已规划连接器</small></strong>
          </article>
          <article>
            <span>采样节律</span>
            <strong>24h<small>连载期每日</small></strong>
          </article>
          <article>
            <span>评分透明度</span>
            <strong>100%<small>公开权重与来源</small></strong>
          </article>
          <article>
            <span>当前阶段</span>
            <strong>01<small>骨架与设计系统</small></strong>
          </article>
        </section>

        <section className="ranking-section" id="rankings">
          <div className="section-heading">
            <div>
              <p className="eyebrow">CURRENT SEASON / DESIGN CONTRACT</p>
              <h2>当季综合信号</h2>
              <p>以下为第一阶段的界面设计数据，第二阶段接入真实数据源。</p>
            </div>
            <div className="filter-preview" aria-label="筛选控件预览">
              <button className="selected" type="button">2026 夏</button>
              <button type="button">全部地区</button>
              <button type="button">全部类型</button>
              <button type="button">无限制榜</button>
            </div>
          </div>

          <div className="ranking-table" role="table" aria-label="排行榜设计预览">
            <div className="ranking-row heading-row" role="row">
              <span>排名</span><span>动画信号</span><span>来源采样</span><span>综合分</span><span>趋势</span>
            </div>
            {previewRankings.map((anime) => (
              <article className="ranking-row" key={anime.rank} role="row">
                <strong className="rank">{String(anime.rank).padStart(2, "0")}</strong>
                <div className="anime-title">
                  <span className="poster-placeholder">{anime.title.slice(-1)}</span>
                  <span><strong>{anime.title}</strong><small>{anime.titleOriginal}</small></span>
                </div>
                <div className="sources">
                  <span><b>B</b>{anime.bangumi}</span>
                  <span><b>M</b>{anime.mal}</span>
                </div>
                <strong className="score">{anime.score}<small>/ 10</small></strong>
                <span className={`trend ${anime.signal}`}>
                  {anime.signal === "up" ? "↗ 上行" : anime.signal === "new" ? "● 新信号" : "→ 稳定"}
                </span>
              </article>
            ))}
          </div>
        </section>

        <section className="methodology" id="methodology">
          <div>
            <p className="eyebrow">OPEN METHODOLOGY</p>
            <h2>不是神秘算法，<br />是一台透明仪器。</h2>
          </div>
          <div className="formula-card">
            <code>Σ(score × α × log(1 + votes))</code>
            <span />
            <code>Σ(α × log(1 + votes))</code>
            <p>Bangumi α = 1.5 · MAL α = 1.0</p>
          </div>
          <p className="method-copy">
            评分人数先取对数，避免单个平台凭借体量完全淹没其他社区；同时提升 Bangumi 权重，使中文动画社区的观察更清晰。
          </p>
        </section>
      </main>

      <footer>
        <span>番剧示波器 · Phase 01</span>
        <span>数据尚未接入 · 当前页面为设计系统验收稿</span>
      </footer>
    </div>
  );
}

export default App;
