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
Web component/model:   18 passed
Chromium E2E:            4 passed
Semantic evaluation:    50 cases, Recall@1 0.94, Recall@10 0.98
TypeScript:              passed
Ruff:                    passed
Vite production build:  passed
```

## External publication status

The public repository and GitHub Pages site are published. Pages uses an explicit, clearly labelled static demo fallback while the Render service and Supabase live repository remain unprovisioned. Follow `docs/deployment.md` to activate live backend data.
