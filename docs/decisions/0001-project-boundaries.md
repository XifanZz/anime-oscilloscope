# ADR 0001: Project and data boundaries

## Status

Accepted for Phase 1.

## Decision

- Build Anime Oscilloscope in a new repository and leave `XifanZz.github.io` unchanged.
- Use Bangumi and MyAnimeList as the first live sources.
- Keep Douban and Filmarks disabled pending written authorization.
- Keep personal Tier List and viewing-history data in the browser.
- Exclude NSFW entries and the complete *My Hero Academia* animation franchise at ingestion time.

## Consequences

- The GitHub Pages base path is `/anime-oscilloscope/` rather than `/`.
- Source connectors must be independently enabled and observable.
- The site must publish methodology and data-source limitations.
- Bilibili import has a formal-authorization-first gate and a local-file fallback.
