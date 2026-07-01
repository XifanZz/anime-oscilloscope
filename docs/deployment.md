# Deployment runbook

## Release boundary

`v0.7.0-demo` deploys fictional, clearly labelled data. Configuring a database URL alone does not switch the current in-memory read repository to live mode. A live public launch additionally requires the production repository/sync implementation and approved credentials.

## Render API

1. Create a new Blueprint from `render.yaml`.
2. Keep `APP_SEMANTIC_BACKEND=hash` on the free demo instance.
3. Configure `APP_DATABASE_URL`, `APP_BANGUMI_TOKEN`, and `APP_MAL_CLIENT_ID` only in Render secrets when live ingestion is implemented.
4. Verify `/api/v1/health`, `/docs`, and the semantic-search rate-limit headers.

Free instances may cold-start. The frontend surfaces API errors and retains browser-local Tier data.

Until Render is provisioned, the Pages build falls back to bundled fictional demo responses for ranking, history, search, AI retrieval, and local imports. The `demo` data-mode disclosure remains visible. Set `VITE_DISABLE_DEMO_FALLBACK=true` in strict environments where an unavailable API should be a hard failure.

## GitHub Pages

1. Create the public `XifanZz/anime-oscilloscope` repository.
2. Enable Pages with **GitHub Actions** as the source.
3. Set repository variable `VITE_API_BASE_URL` to the deployed API URL ending in `/api/v1`.
4. Push `main`. The Pages workflow builds with base path `/anime-oscilloscope/`.
5. Verify `https://xifanzz.github.io/anime-oscilloscope/` in a clean browser profile.

The workflow falls back to `https://anime-oscilloscope-api.onrender.com/api/v1` when the variable is absent.

## Supabase migration order

Apply SQL files in lexical order:

1. `001_initial_schema.sql`
2. `002_source_payload_cache.sql`
3. `003_mapping_candidates.sql`

Use a dedicated service role only in backend jobs. Never expose database or source credentials through Vite variables.

## Release checklist

- `npm ci` and all verification commands pass.
- Chromium E2E is green and no secrets appear in tracked files.
- Render health check succeeds after cold start.
- Pages requests the deployed API rather than localhost.
- Demo/live mode and active semantic engine are visible.
- Git tag and changelog version match.
