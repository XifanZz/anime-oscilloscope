# Phase 04 verification

## Delivered contract

- Tracking eligibility for titles premiering on or after the configured product launch.
- Sampling cadence transitions: daily while airing, weekly for 90 days after completion, monthly through year three, then yearly.
- Due-time calculation based on the last successful sample.
- Historical rating API with Bangumi, MAL, composite, episode, freshness, and sampling-policy data.
- Composite history that never converts a missing source observation to zero.
- SVG oscilloscope with dual source lines, dashed composite line, daily points, and 12 episode markers.
- Visible stale-source state that keeps and labels the last successful snapshot.
- 87 deterministic daily demo snapshots from 2026-04-05 through 2026-06-30.

## Automated checks

```text
API:       50 tests passed
Web:        5 tests passed
Ruff:       passed
TypeScript: passed
Vite build: passed
```

All history shown in demo mode is fictional and explicitly labelled. No live source is called by automated tests.
