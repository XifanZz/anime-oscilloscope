# Codex collaboration case study

## Human ownership

The product owner defined the name, source priorities, Bangumi coefficient, vote thresholds, inclusion/exclusion policy, sampling cadence, local-only privacy boundary, staged approval process, and the decision to preserve the original `XifanZz.github.io` project unchanged.

## AI-assisted execution

Codex translated those decisions into typed connector contracts, migrations, ranking/history APIs, the React design system, local Tier state, explainable retrieval, file parsing, tests, deployment configuration, and documentation. Work was split into phase commits so generated output could be reviewed or stopped without losing a runnable checkpoint.

## Review and correction evidence

AI output was not accepted blindly:

- Fixture tests caught cross-source and scoring assumptions before live credentials were available.
- Browser review found an asynchronous file-import/catalog-index race; the upload control now waits for the public index.
- Chromium E2E exposed incorrect monorepo server roots and a test that erased its own localStorage on reload.
- The 50-query evaluation retained a real structured-filter failure instead of reporting perfect synthetic metrics.
- Demo data, fallback embeddings, unavailable OAuth scope, and missing live credentials are explicitly disclosed.

## Phase history

| Commit | Human-reviewable outcome |
|---|---|
| `ee9ad9b` | Foundation and visual contract |
| `2c5d7fe` | Bangumi discovery connector |
| `bd5408b` | MAL matching pipeline |
| `c88f048` | API-driven ranking catalog |
| `1f82a4d` | Historical rating oscilloscope |
| `db6ff10` | Local-first Tier libraries |
| `db52518` | Explainable AI search and local imports |

## Resume framing

“Designed and implemented a multi-source anime analytics platform with React/TypeScript, FastAPI, PostgreSQL/pgvector schemas, explainable 512-D retrieval, privacy-preserving local imports, 60 API tests, 17 web tests, and Chromium E2E. Used Codex as an engineering copilot while retaining human control over product policy, data compliance, review gates, and acceptance metrics.”
