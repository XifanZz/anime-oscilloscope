# 番剧示波器 / Anime Oscilloscope

> 多源动画评分采样与分析平台
> A multi-source anime rating sampling and analytics platform.

番剧示波器把动画视作随时间变化的信号：平台评分是观测值，定时任务负责采样，跨站聚合负责估计，评分人数门槛负责降噪。

Anime Oscilloscope treats an anime title as a signal that changes over time: community ratings are observations, scheduled jobs sample them, and transparent weighting produces a combined estimate.

## Current phase / 当前阶段

Phase 2B adds the official MAL client contract and evidence-based Bangumi-to-MAL candidate matching. Live MAL reads remain disabled until a local `APP_MAL_CLIENT_ID` is configured; fixture-based CI is fully operational without secrets.

第二阶段 B 已加入 MAL 官方客户端契约，以及基于标题、日期、类型、集数和季度签名证据的跨站匹配。未配置本地 `APP_MAL_CLIENT_ID` 时不会请求 MAL；CI 完全使用固定响应，不依赖密钥。

## Architecture / 架构

- React + TypeScript + Vite frontend
- Python FastAPI backend
- Supabase PostgreSQL + pgvector
- GitHub Actions data jobs
- GitHub Pages frontend and Render API

See [docs/architecture.md](docs/architecture.md) for the system map and [docs/design-system.md](docs/design-system.md) for the visual language.

## Local development / 本地开发

### Web

```powershell
npm.cmd install
npm.cmd run dev
```

Open `http://localhost:5173`.

### API

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e "apps/api[dev]"
.venv\Scripts\python -m uvicorn anime_oscilloscope.main:app --app-dir apps/api/src --reload
```

Open `http://localhost:8000/docs` or `http://localhost:8000/api/v1/health`.

## Verification / 验证

```powershell
npm.cmd test
npm.cmd run typecheck
npm.cmd run build
.venv\Scripts\python -m pytest apps/api/tests
```

### Read-only Bangumi discovery / 只读季度发现

```powershell
.venv\Scripts\python -m anime_oscilloscope.jobs.discover_bangumi --year 2026 --quarter 3 --limit 5
```

The command calls the public API and prints normalized eligibility decisions. It performs no database writes.

### Read-only MAL candidate matching / 只读跨站匹配

Add your MAL client ID to the untracked `.env` file, then run:

```powershell
.venv\Scripts\python -m anime_oscilloscope.jobs.match_mal `
  --bangumi-id 255209 --limit 10
```

The command prints scored candidates and performs no database writes. Never paste or commit the client ID.

## Data policy / 数据政策

- Phase 1 enables no live rating connector.
- Bangumi and MAL are the first planned sources.
- Douban and Filmarks remain disabled until written authorization permits reuse.
- The site never asks for Bilibili credentials or session cookies.
- NSFW works and the complete *My Hero Academia* animation franchise are excluded from ingestion.

## License

Source licensing will be selected before the first public release. Third-party metadata and artwork retain their respective owners' rights and will be attributed per source requirements.
