# Phase 2A verification

Date: 2026-06-30

## Delivered

- normalized `SourceConnector` boundary;
- Bangumi seasonal discovery, subject, and episode reads;
- explicit User-Agent and bounded retry behavior;
- media-type, alias, rating, region, and episode normalization;
- eligible/excluded/review decisions for target region, NSFW, missing region, and excluded franchise;
- PostgreSQL raw payload cache migration;
- fixture-only CI tests and a separate read-only live discovery command.

## Automated checks

```text
npm.cmd run typecheck                         passed
npm.cmd test                                 2 passed
npm.cmd run build                            passed
python -m ruff check apps/api                passed
python -m pytest apps/api/tests              19 passed
```

## Live read smoke test

Command:

```powershell
.venv\Scripts\python -m anime_oscilloscope.jobs.discover_bangumi `
  --year 2026 --quarter 3 --limit 3
```

Observed contract:

- API-reported matching titles: 124;
- returned sample: 3;
- all three normalized as `tv` and `JP` from explicit Bangumi public tags;
- all three received `eligible / target_region`;
- `writes_performed` was `false`.

The live call is evidence only. CI remains deterministic and does not contact Bangumi.
