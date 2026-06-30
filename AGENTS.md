# Repository guidance

## Product boundaries

- This repository is the new **Anime Oscilloscope / 番剧示波器** project.
- Never modify or overwrite the separate `XifanZz.github.io` repository.
- Do not scrape Douban or Filmarks. Their connectors remain disabled until written permission exists.
- Never request, store, log, or transmit Bilibili passwords, cookies, or `SESSDATA`.
- Exclude NSFW entries and the complete *My Hero Academia* animation franchise during ingestion.

## Repository layout

- `apps/web`: React + TypeScript + Vite frontend.
- `apps/api`: FastAPI backend and Python domain logic.
- `database/migrations`: forward-only PostgreSQL migrations.
- `docs`: architecture, decisions, data contracts, and verification evidence.

## Commands

- Install frontend dependencies: `npm.cmd install`
- Run frontend: `npm.cmd run dev`
- Test frontend: `npm.cmd test`
- Build frontend: `npm.cmd run build`
- Create API environment: `python -m venv .venv`
- Install API: `.venv\\Scripts\\python -m pip install -e "apps/api[dev]"`
- Test API: `.venv\\Scripts\\python -m pytest apps/api/tests`

## Working agreements

- Keep data-source clients behind the `SourceConnector` interface.
- Use fixture responses in CI; CI must not call live third-party APIs.
- Preserve the last successful data snapshot when a source is unavailable.
- Add tests for scoring, thresholds, scheduling, exclusion, or mapping behavior before changing it.
- Complete one implementation phase at a time and record its verification before starting the next phase.
