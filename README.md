# 番剧示波器 / Anime Oscilloscope

> 多源动画评分采样与分析平台
> A multi-source anime rating sampling and analytics platform.

番剧示波器把动画视作随时间变化的信号：平台评分是观测值，定时任务负责采样，跨站聚合负责估计，评分人数门槛负责降噪。

Anime Oscilloscope treats an anime title as a signal that changes over time: community ratings are observations, scheduled jobs sample them, and transparent weighting produces a combined estimate.

## Current phase / 当前阶段

Phase 1 establishes the monorepo, visual system, API boundary, database schema, CI, and deployment templates. Live Bangumi and MAL synchronization begins in Phase 2.

第一阶段建立项目骨架、视觉系统、API 边界、数据库结构、CI 和部署模板。Bangumi 与 MAL 的实时同步将在第二阶段实现。

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

## Data policy / 数据政策

- Phase 1 enables no live rating connector.
- Bangumi and MAL are the first planned sources.
- Douban and Filmarks remain disabled until written authorization permits reuse.
- The site never asks for Bilibili credentials or session cookies.
- NSFW works and the complete *My Hero Academia* animation franchise are excluded from ingestion.

## License

Source licensing will be selected before the first public release. Third-party metadata and artwork retain their respective owners' rights and will be attributed per source requirements.
