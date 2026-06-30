# 番剧示波器 / Anime Oscilloscope

> 多源动画评分采样与分析平台
> A multi-source anime rating sampling and analytics platform.

番剧示波器把动画视作随时间变化的信号：平台评分是观测值，定时任务负责采样，跨站聚合负责估计，评分人数门槛负责降噪。

Anime Oscilloscope treats an anime title as a signal that changes over time: community ratings are observations, scheduled jobs sample them, and transparent weighting produces a combined estimate.

## Current phase / 当前阶段

Phase 6 adds explainable Chinese natural-language retrieval and privacy-preserving Bilibili file import. Production can enable quantized ONNX `BAAI/bge-small-zh-v1.5`; deterministic demo/CI retrieval always discloses that it is a fallback engine. CSV/JSON viewing records are parsed and matched locally, and every candidate requires confirmation.

第六阶段已加入可解释的中文自然语言找番和保护隐私的 B站文件导入。生产环境可启用量化 ONNX `BAAI/bge-small-zh-v1.5`；演示与 CI 使用确定性回退引擎并明确标注。CSV/JSON 观看记录只在本地解析和匹配，每个候选都必须确认。

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

Start both services to exercise the interactive ranking. The web app defaults to `http://127.0.0.1:8000/api/v1`; deployment can override it with `VITE_API_BASE_URL`.

To enable the optional quantized BGE backend:

```powershell
.venv\Scripts\python -m pip install -e "apps/api[ai]"
$env:APP_SEMANTIC_BACKEND="bge"
```

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

- The Phase 6 interactive catalog and history are explicitly fictional demo data until the database read repository is enabled.
- Tier libraries are versioned browser-local data and never sent to the API.
- Imported viewing files and raw titles stay in the browser; password, Cookie, `SESSDATA`, and token fields are rejected.
- Bangumi and MAL are the only enabled connector contracts in the first release.
- Douban and Filmarks remain disabled until written authorization permits reuse.
- The site never asks for Bilibili credentials or session cookies.
- NSFW works and the complete *My Hero Academia* animation franchise are excluded from ingestion.

## License

Source licensing will be selected before the first public release. Third-party metadata and artwork retain their respective owners' rights and will be attributed per source requirements.
