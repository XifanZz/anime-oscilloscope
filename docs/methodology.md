# Scoring and sampling methodology

## Composite rating

```text
Σ(score × platform coefficient × log(1 + rating count))
────────────────────────────────────────────────────────
Σ(platform coefficient × log(1 + rating count))
```

Coefficients: Bangumi `1.5`; MAL, Douban, and Filmarks `1.0`. Filmarks will be converted from five to ten points if written permission is obtained.

The logarithm reduces platform-size dominance without discarding rating population. The unrestricted ranking allows single-source titles and reports completeness. Default threshold mode requires Bangumi `> 1,000` and MAL `> 20,000`; users can override both.

## Missing and stale data

- Missing observations are omitted from the denominator, never converted to zero.
- A failed connector attempt cannot delete the last successful current value or snapshot.
- API history exposes source status, last success, last attempt, and a stale explanation.

## Historical sampling

Only titles premiering from the tracking launch date enter the pipeline.

| Lifecycle | Cadence |
|---|---|
| Airing | Daily |
| First 90 days after completion | Weekly |
| 90 days to three years | Every 30 days |
| More than three years | Every 365 days |

Snapshots are retained permanently. Episode markers come from Bangumi because MAL does not expose the required timeline capability.

## Cross-source mapping

Candidate confidence weights title aliases `65%`, air date `20%`, media type `10%`, and episode count `5%`. Automatic approval requires confidence at least `0.88`, title similarity at least `0.92`, and no season/Part/movie/OVA conflict. Ambiguous cases remain in the review queue.

## Semantic retrieval

Rules extract year, region, media type, status, and known tags. Structured constraints filter candidates; a 512-dimensional provider ranks survivors. Responses disclose provider, reasons, confidence, and latency. See [AI evaluation](ai-evaluation.md).
