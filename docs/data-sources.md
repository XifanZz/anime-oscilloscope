# Data sources

## Connector policy

All sources implement the `SourceConnector` contract and return normalized domain models. Connectors do not write to PostgreSQL directly. This keeps retries, API changes, normalization, eligibility, and persistence independently testable.

CI uses committed response fixtures and never calls a live third-party API.

## Bangumi

- API base: `https://api.bgm.tv`
- Contract checked against API version `2026-06-25`.
- Discovery: `POST /v0/search/subjects` with animation type, half-open air-date range, and `nsfw: false`.
- Detail: `GET /v0/subjects/{subject_id}`.
- Episodes: paginated `GET /v0/episodes?subject_id=...`.
- The required identifying User-Agent contains the maintainer name and public project URL.
- An access token is optional for current public reads and is loaded only from `APP_BANGUMI_TOKEN`.

The search endpoint is documented as experimental. Raw payload caching and fixture tests prevent silent schema drift from contaminating normalized records.

## Eligibility decisions

Every discovered title receives one of three decisions:

- `eligible`: at least one participating region is CN, JP, or KR;
- `excluded`: NSFW, configured excluded franchise, or only outside regions;
- `review`: region metadata is missing and must not be silently discarded.

Cross-border productions remain eligible whenever a target-region participant is present.

## Disabled sources

Douban and Filmarks connectors remain disabled until written authorization permits reuse. Disabled connectors make no network requests.
