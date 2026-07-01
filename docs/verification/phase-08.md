# Phase 08 verification

## Live-data readiness

- `APP_REPOSITORY_BACKEND` explicitly selects demo or PostgreSQL reads.
- PostgreSQL rows are mapped into the same typed catalog/history contracts used by the UI.
- Bangumi catalog, ratings, daily snapshots, episode markers, MAL mappings, and review candidates use idempotent upserts.
- Sync attempts and partial failures are retained in `sync_run` and `source_connector`.
- Snapshot selection enforces the launch date and daily/weekly/monthly/yearly cadence.
- The daily workflow remains disabled until `LIVE_SYNC_ENABLED=true` and required secrets exist.
- The public Pages fallback remains available while Supabase and Render are unprovisioned.

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

No database password, source credential, cookie, or user viewing record is committed. Live mode is not enabled merely by merging this phase; Supabase migrations, repository secrets, an initial sync, and Render configuration are separate explicit operations.
