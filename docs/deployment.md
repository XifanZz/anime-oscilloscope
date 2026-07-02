# Deployment runbook

## Release boundary

`v0.7.0-demo` deploys fictional, clearly labelled data by default. The PostgreSQL read repository and idempotent sync writer are available but activate only when `APP_REPOSITORY_BACKEND=postgres`; a live public launch still requires migrations, approved credentials, and an initial successful sync.

## Vercel API

1. Import `XifanZz/anime-oscilloscope` into a personal Vercel Hobby account.
2. Set the project Root Directory to `apps/api` and Framework Preset to **FastAPI**; Vercel reads the conventional `app.py` entrypoint.
3. Add `APP_DATABASE_URL`, `APP_MAL_CLIENT_ID`, `APP_ENV=production`, `APP_REPOSITORY_BACKEND=postgres`, `APP_SEMANTIC_BACKEND=hash`, and `APP_CORS_ORIGINS=["https://xifanzz.github.io"]`.
4. Deploy with project name `anime-oscilloscope-api`.
5. Verify that `/api/v1/health` reports `data_mode: live`, then check `/docs` and the semantic-search rate-limit headers.

Vercel Functions are stateless; long-running discovery and sampling remain in GitHub Actions. The frontend retains browser-local Tier data and falls back to bundled fictional demo responses if the hosted API is unavailable. Set `VITE_DISABLE_DEMO_FALLBACK=true` in strict environments where API failure should be fatal.

## GitHub Pages

1. Create the public `XifanZz/anime-oscilloscope` repository.
2. Enable Pages with **GitHub Actions** as the source.
3. Set repository variable `VITE_API_BASE_URL` to the deployed API URL ending in `/api/v1`.
4. Push `main`. The Pages workflow builds with base path `/anime-oscilloscope/`.
5. Verify `https://xifanzz.github.io/anime-oscilloscope/` in a clean browser profile.

The workflow falls back to `https://anime-oscilloscope-api.vercel.app/api/v1` when the variable is absent.

## Supabase migration order

Apply SQL files in lexical order:

1. `001_initial_schema.sql`
2. `002_source_payload_cache.sql`
3. `003_mapping_candidates.sql`
4. `004_live_repository.sql`
5. `005_catalog_backfill.sql`

## Scheduled synchronization

The `Live data sync` workflow is inert by default. Add repository secrets `APP_DATABASE_URL`, `APP_BANGUMI_TOKEN`, and `APP_MAL_CLIENT_ID`, then set repository variable `LIVE_SYNC_ENABLED=true`. It runs at 03:17 China Standard Time, rotates through seven seasonal discovery pages across the week, and can also be started manually with an explicit offset. Each execution records `sync_run`, applies the configured sampling cadence, keeps failed-source snapshots intact, and writes ambiguous MAL matches to `mapping_candidate`.

The `Historical catalog backfill` workflow is separately guarded by `HISTORY_BACKFILL_ENABLED=true`. It applies migration `005` idempotently, resumes a durable PostgreSQL cursor, and processes bounded Bangumi pages from 1917 through the current year. Re-running the workflow is safe: catalog and rating writes are upserts, and a crash repeats at most the last page. The scheduled run processes ten pages every six hours; manual dispatch can raise or lower that bound without losing progress.

Use a dedicated service role only in backend jobs. Never expose database or source credentials through Vite variables.

## Release checklist

- `npm ci` and all verification commands pass.
- Chromium E2E is green and no secrets appear in tracked files.
- Vercel health check reports `data_mode: live`.
- Pages requests the deployed API rather than localhost.
- Demo/live mode and active semantic engine are visible.
- Git tag and changelog version match.
