# Phase 08 verification

## Live-data readiness

- `APP_REPOSITORY_BACKEND` explicitly selects demo or PostgreSQL reads.
- PostgreSQL rows are mapped into the same typed catalog/history contracts used by the UI.
- Bangumi catalog, ratings, daily snapshots, episode markers, MAL mappings, and review candidates use idempotent upserts.
- Sync attempts and partial failures are retained in `sync_run` and `source_connector`.
- Snapshot selection enforces the launch date and daily/weekly/monthly/yearly cadence.
- The daily workflow remains disabled until `LIVE_SYNC_ENABLED=true` and required secrets exist.
- The public Pages fallback remains available while the Vercel API is unprovisioned.

## Verification target

```text
API unit/integration: 66 passed
Web component/model:   18 passed
Chromium E2E:            4 passed
TypeScript:              passed
Ruff:                    passed
Vite production build:  passed
```

## External boundary

No database password, source credential, cookie, or user viewing record is committed. Live mode requires Supabase migrations, repository secrets, an initial sync, and Vercel environment configuration as separate explicit operations.

## Production smoke evidence

On 2026-07-01 the guarded workflow completed its first authenticated Supabase sync:

- [5-title smoke run](https://github.com/XifanZz/anime-oscilloscope/actions/runs/28500348974): 5 catalog writes, 44 episode markers, 5 MAL matching attempts, 0 failures.
- [20-title seed run](https://github.com/XifanZz/anime-oscilloscope/actions/runs/28500531329): completed successfully.
- [final seasonal page](https://github.com/XifanZz/anime-oscilloscope/actions/runs/28500580542): completed successfully.

The remaining seasonal pages are filled by the guarded daily offset rotation. Workflow logs mask database and MAL credentials.
