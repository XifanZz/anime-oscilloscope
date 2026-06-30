# Phase 06 verification

## Delivered contract

- `POST /anime/semantic-search` with Chinese intent parsing, vector ranking, reasons, confidence, engine disclosure, and latency.
- Swappable 512-dimensional provider: deterministic CI fallback and optional quantized BGE/FastEmbed production engine.
- A 50-query evaluation dataset, Recall@1/10, mean/P95 latency, and recorded failure type.
- `GET /anime/index` for one-way download of public matching data.
- Browser-local CSV/JSON parsing, deduplication, exact/fuzzy candidate evidence, and explicit confirmation.
- Credential-field rejection for password, Cookie, `SESSDATA`, and tokens.
- Confirmed imports feed the active local Tier library without an account or server write.

## Automated checks

```text
API:       57 tests passed
Web:       17 tests passed
Ruff:       passed
TypeScript: passed
Vite build: passed
```

The BGE model download is optional and is not performed in CI. Demo results visibly report `hash-512-demo`; they are never labelled as BGE output.

The Bilibili open-platform documentation was reviewed on 2026-06-30. It documents account authorization, public user information, content management, and authorized data capabilities, but no public viewing-history scope was identified. OAuth viewing-history import is therefore not claimed or implemented; the local file workflow remains the compliant fallback.
