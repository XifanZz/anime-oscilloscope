# Phase 10 verification

## MAL review queue

- Added `GET /api/v1/mappings/candidates` for unresolved MAL review candidates.
- Added protected `POST /api/v1/mappings/candidates/{id}/resolve`.
- Review writes are disabled unless `APP_REVIEW_ADMIN_TOKEN` is configured on the API host and the request includes `X-Review-Token`.
- Added a homepage MAL review dashboard with candidate evidence, risk reasons, and approve/reject actions.
- Added `anime_oscilloscope.jobs.bulk_match_mal` to generate review candidates from rankable Bangumi entries that do not already have approved MAL mappings or open candidates.
- Added the guarded `MAL review candidate matching` workflow, enabled only by repository variable `MAL_MATCH_ENABLED=true`.

## Verification target

```text
API unit/integration: 74 passed
API ruff:             passed
Web component/model:  23 passed
TypeScript:           passed
Vite production build: passed
Chromium E2E:         4 passed
```

## Safety boundary

No public visitor can mutate mappings by default. The dashboard is useful as a transparent review queue without a token; write actions require a server-side secret configured separately from Vite variables.
