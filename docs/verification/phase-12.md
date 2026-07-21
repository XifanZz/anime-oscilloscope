# Phase 12 verification - seasonal sync and detail posters

Date: 2026-07-21

## Scope

- Detail panels display the Bangumi cover image when `anime.image_url` is present.
- Empty ranking copy explains that a selected year/quarter may still be waiting for synchronization.
- `sync-data.yml` accepts optional manual `year` and `quarter` inputs for targeted seasonal synchronization.

## Expected checks

```powershell
ruff check apps/api
.venv\Scripts\python -m pytest apps\api\tests
npm.cmd run typecheck
npm.cmd test -- --run
npm.cmd run build
```

## Acceptance notes

- The public ranking API can remain empty for a specific season until the corresponding Bangumi discovery page has been synchronized.
- Maintainers can now dispatch the live-data workflow for `year=2026`, `quarter=2`, and one or more offsets to fill the 2026 April cour directly.
