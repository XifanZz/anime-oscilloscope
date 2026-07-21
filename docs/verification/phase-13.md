# Phase 13 verification - Seasonal catalog backfill

Date: 2026-07-21

Scope:

- Added a dedicated GitHub Actions workflow for selected year/quarter Bangumi catalog backfills.
- Kept the backfill independent from MAL matching so Bangumi-only seasonal entries can appear in rankings.
- Used heat-sorted Bangumi discovery for seasonal catalog fill, while preserving composite-score sorting in the public ranking UI.

Validation commands:

```powershell
.venv\Scripts\python -m ruff check apps/api
.venv\Scripts\python -m pytest apps/api/tests
npm.cmd run typecheck
npm.cmd test -- --run
npm.cmd run build
```

Expected live operations smoke:

```powershell
gh workflow run backfill-season.yml --repo XifanZz/anime-oscilloscope --ref main -f year=2026 -f quarter=1 -f limit=100 -f start_offset=0 -f max_pages=10
gh workflow run backfill-season.yml --repo XifanZz/anime-oscilloscope --ref main -f year=2026 -f quarter=2 -f limit=100 -f start_offset=0 -f max_pages=10
```
