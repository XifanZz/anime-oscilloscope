# Phase 11 verification - ranking scoring patch

Date: 2026-07-21

## Scope

- Change ranking quarter labels from seasonal names to cour start months: `1 月`, `4 月`, `7 月`, and `10 月`.
- Keep missing-MAL entries based on Bangumi, while confidence-guarding tiny early single-source vote samples toward `5.0`.
- Record the release cadence rule for future GitHub-visible versions.

## Expected checks

```powershell
ruff check apps/api
.venv\Scripts\python -m pytest apps\api\tests
npm.cmd run typecheck
npm.cmd test -- --run
npm.cmd run build
```

## Acceptance notes

- A Bangumi-only item with `8.8` from `4` votes calculates as `5.152`, so it no longer outranks stable titles solely from an early tiny sample.
- A Bangumi-only item with at least `100` Bangumi votes remains exactly the Bangumi score.
- Quarter filters continue sending `quarter=1..4`; only the user-facing labels changed.
