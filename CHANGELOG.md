# Changelog

## Unreleased

- Add explicit demo/PostgreSQL repository selection for catalog and history reads.
- Add idempotent catalog, mapping, rating snapshot, episode, and sync-run writes.
- Add a guarded daily live-data workflow and Phase 8 deployment instructions.
- Record successful authenticated Bangumi/MAL-to-Supabase production smoke runs.
- Replace the card-gated Render target with Vercel Hobby FastAPI deployment metadata.
- Add resumable full-history Bangumi catalog backfill with a durable database cursor.
- Replace the 20-row web limit with 50-row pages and explicit incremental loading.
- Add a data-quality dashboard for catalog coverage, MAL gaps, connector freshness, and backfill progress.

## 0.7.0 - 2026-07-01

First portfolio demo release.

- Bangumi and MyAnimeList connector contracts with evidence-based mapping.
- Composite rankings, filters, search, detail views, and explicit data completeness.
- Historical rating oscilloscope with daily snapshots and episode markers.
- Browser-local multi-library Tier List with PNG export.
- Explainable Chinese natural-language retrieval and a 50-query evaluation set.
- Privacy-preserving CSV/JSON Bilibili file import with explicit confirmation.
- FastAPI rate limiting and security headers.
- Explicit static demo fallback keeps the Pages portfolio interactive before Render provisioning.
- Unit, API, and Chromium end-to-end test gates.

The deployed demo uses deterministic fictional catalog data until a live Supabase database and approved source credentials are configured.
