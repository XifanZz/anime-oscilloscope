# Phase 07 verification

## Release hardening

- GitHub Pages now receives an explicit production API URL.
- FastAPI semantic search has a 30-request/60-second per-process limit with standard response headers.
- API responses add content-type, frame, referrer, and permission security headers.
- Keyboard skip link, visible focus, and Escape-to-close dialog behavior were added.
- Playwright starts both services and covers four critical Chromium flows.
- Release version, MIT license, changelog, deployment guide, data dictionary, methodology, browser support, demo script, and Codex case study are included.

## Verification target

```text
API unit/integration: 60 passed
Web component/model:   17 passed
Chromium E2E:            4 passed
Semantic evaluation:    50 cases, Recall@1 0.94, Recall@10 0.98
TypeScript:              passed
Ruff:                    passed
Vite production build:  passed
```

## External publication status

At audit time the local repository had no Git remote and GitHub CLI was unavailable. Local release completion does not imply that the repository, Render service, Supabase database, or Pages site has been created. Follow `docs/deployment.md` with an authenticated GitHub connection.
