# Changelog

## Unreleased

Future portfolio milestones will be recorded here first, then moved into a dated release section and mirrored to a GitHub Release.

## 0.8.2 - 2026-07-21

- Add Bangumi cover posters to the anime detail panel.
- Clarify empty ranking results when a selected year/quarter has not yet been synchronized.
- Allow the live-data workflow to manually synchronize a selected year and quarter, enabling targeted seasonal backfills such as 2026 Q2.

## 0.8.1 - 2026-07-21

- Change ranking quarter labels from seasonal names to `1 月`, `4 月`, `7 月`, and `10 月`.
- Keep Bangumi as the displayed single-source authority when MAL is missing, but confidence-guard tiny early vote samples toward a neutral score so they do not outrank stable titles.
- Document release versioning cadence: major portfolio milestones use new minor versions, while focused fixes use patch versions.

## 0.8.0 - 2026-07-21

- Add explicit demo/PostgreSQL repository selection for catalog and history reads.
- Add idempotent catalog, mapping, rating snapshot, episode, and sync-run writes.
- Add a guarded daily live-data workflow and Phase 8 deployment instructions.
- Record successful authenticated Bangumi/MAL-to-Supabase production smoke runs.
- Replace the card-gated Render target with Vercel Hobby FastAPI deployment metadata.
- Add resumable full-history Bangumi catalog backfill with a durable database cursor.
- Replace the 20-row web limit with 50-row pages and explicit incremental loading.
- Add a data-quality dashboard for catalog coverage, MAL gaps, connector freshness, and backfill progress.
- Add a protected MAL mapping review queue with bulk candidate generation and dashboard evidence.
- Start a formal GitHub-visible versioning policy for portfolio releases.

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
