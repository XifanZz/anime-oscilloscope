# Release history and GitHub versioning

Anime Oscilloscope uses Git tags, GitHub Releases, and `CHANGELOG.md` together so each portfolio milestone has a visible version number and update summary on GitHub.

## Policy

- Product milestones use `vMAJOR.MINOR.PATCH` tags, for example `v0.8.0`.
- Each release updates package versions, API `__version__`, the README release badge, and `CHANGELOG.md`.
- After the release commit reaches `main`, create an annotated Git tag and a GitHub Release using the same changelog notes.
- I decide the release level by scope: substantial user-visible feature sets become minor versions such as `v0.9.0`; focused fixes, copy changes, and scoring adjustments become patch versions such as `v0.8.1`.
- Older pre-policy commits are kept in Git history, but formal release notes start at `v0.8.0`.

## Current releases

### v0.8.2 - 2026-07-21

- Anime detail panels now show the Bangumi cover poster when available.
- Empty ranking results explain that a selected year/quarter may not have been synchronized yet.
- Live-data sync can be manually dispatched for a chosen year and quarter, allowing targeted seasonal backfills.

### v0.8.1 - 2026-07-21

- Ranking quarter labels now use anime cour start months: `1 月`, `4 月`, `7 月`, and `10 月`.
- Single-source Bangumi entries still use Bangumi as the authority when MAL is missing, but tiny early vote samples are confidence-guarded toward a neutral score.
- Release cadence is documented so future GitHub Releases consistently show version number, date, and update notes.

### v0.8.0 - 2026-07-21

- Live-data repository and sync operations matured beyond the static demo baseline.
- Full-history catalog backfill can resume from durable database progress.
- Ranking pages support incremental loading instead of a fixed 20-row cap.
- Data quality dashboard exposes catalog coverage, MAL mapping gaps, source freshness, and backfill progress.
- MAL review queue supports evidence-ranked candidates and protected approval/rejection actions.

### v0.7.0 - 2026-07-01

- First reproducible portfolio demo release.
- Composite rankings, search, detail views, rating oscilloscope, browser-local Tier List, AI search, and private file import.
