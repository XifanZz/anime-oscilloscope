# Release history and GitHub versioning

Anime Oscilloscope uses Git tags, GitHub Releases, and `CHANGELOG.md` together so each portfolio milestone has a visible version number and update summary on GitHub.

## Policy

- Product milestones use `vMAJOR.MINOR.PATCH` tags, for example `v0.8.0`.
- Each release updates package versions, API `__version__`, the README release badge, and `CHANGELOG.md`.
- After the release commit reaches `main`, create an annotated Git tag and a GitHub Release using the same changelog notes.
- Older pre-policy commits are kept in Git history, but formal release notes start at `v0.8.0`.

## Current releases

### v0.8.0 - 2026-07-21

- Live-data repository and sync operations matured beyond the static demo baseline.
- Full-history catalog backfill can resume from durable database progress.
- Ranking pages support incremental loading instead of a fixed 20-row cap.
- Data quality dashboard exposes catalog coverage, MAL mapping gaps, source freshness, and backfill progress.
- MAL review queue supports evidence-ranked candidates and protected approval/rejection actions.

### v0.7.0 - 2026-07-01

- First reproducible portfolio demo release.
- Composite rankings, search, detail views, rating oscilloscope, browser-local Tier List, AI search, and private file import.
