# Phase 2B verification

Date: 2026-06-30

## Delivered

- official MAL v2 client authentication contract using `X-MAL-CLIENT-ID`;
- seasonal discovery, title search, detail, rating population, status, media type, and episode-count normalization;
- explicit source capability declarations—MAL cannot provide episode timelines;
- deterministic Bangumi-to-MAL candidate scoring and review gates;
- PostgreSQL candidate queue migration with structured evidence;
- read-only match command with a safe missing-secret error;
- fixture-only tests for MAL and cross-source matching.

## Automated checks

```text
npm.cmd run typecheck                         passed
npm.cmd test                                 2 passed
npm.cmd run build                            passed
python -m ruff check apps/api                passed
python -m pytest apps/api/tests              34 passed
```

## Secret and network verification

- No MAL client ID exists in the repository.
- Without `APP_MAL_CLIENT_ID`, the read-only match command exits before any MAL request and explains local `.env` setup.
- MAL request shape, fields, pagination, and client header are verified through a committed mock transport.
- A live MAL smoke test is intentionally deferred until the maintainer configures their own client ID locally.

## Matching acceptance examples

- Exact alias, date, media type, and episode count: automatic, confidence 1.0.
- Similar title but TV/movie and episode conflict: review.
- Different numbered seasons: never automatic.
- Unrelated title: reject.
