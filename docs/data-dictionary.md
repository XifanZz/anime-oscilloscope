# Data dictionary

The SQL source of truth is `database/migrations`. IDs are internal UUIDs unless noted.

## Core catalog

| Entity | Purpose | Important fields |
|---|---|---|
| `anime` | Canonical title catalog | Bangumi ID, names, aliases, dates, status, media type, regions, exclusion flags |
| `external_mapping` | Cross-source identity | source, external ID, confidence, review status, evidence |
| `mapping_candidate` | Versioned human-review queue | primary/candidate IDs, confidence, disposition, evidence |
| `episode` | Bangumi episode timeline | episode number, localized titles, air date |

`anime.is_excluded` retains audit evidence instead of silently deleting records. External mappings are unique per source and title.

## Ratings and history

| Entity | Grain | Retention |
|---|---|---|
| `current_rating` | One latest row per anime and source | Replaced only by a successful sample |
| `rating_snapshot` | One anime/source/sample timestamp | Permanent |
| `sync_run` | One connector job execution | Permanent operational history |
| `source_connector` | One source capability/status row | Latest status and success time |

Scores use a 0–10 scale. `rating_count` is non-negative. A missing source has no row; it is not represented as score zero.

## AI and cached source data

| Entity | Purpose |
|---|---|
| `anime_embedding` | 512-dimensional catalog embedding, model name, and content hash |
| `source_payload_cache` | Raw response cache for schema-drift investigation and retry isolation |

Embedding rows are replaced when the normalized content hash or model changes. Private viewing records and Tier libraries are deliberately absent from the database.

## Browser-local state

`anime-oscilloscope:tier-libraries:v1` stores a versioned document containing an active library ID and ordered arrays for `pool`, `s`, `a`, `b`, `c`, and `d`. Invalid structures fall back to a new empty library.
