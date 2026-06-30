# AI retrieval evaluation

## Engine boundary

- Production target: `BAAI/bge-small-zh-v1.5`, 512 dimensions, loaded through FastEmbed's quantized ONNX runtime.
- Current deterministic baseline: 512-dimensional character n-grams plus structured rules.
- The API always returns `engine` and `model_name`; baseline metrics must not be presented as BGE metrics.

The BGE model card documents 24M parameters and a 512-dimensional Chinese embedding. FastEmbed documents quantized ONNX inference and model selection: [BGE documentation](https://bge-model.com/bge/bge_v1_v1.5.html), [FastEmbed documentation](https://qdrant.github.io/fastembed/).

## Evaluation set

`apps/api/tests/fixtures/semantic_queries.json` contains 50 Chinese queries across four deterministic demo titles. Cases cover title/alias lookup, year, country, co-production, media type, status, and tags.

Run:

```powershell
.venv\Scripts\python -m anime_oscilloscope.jobs.evaluate_semantic
```

Baseline run on 2026-06-30:

| Metric | Result |
|---|---:|
| Cases | 50 |
| Recall@1 | 0.94 |
| Recall@10 | 0.98 |
| Mean API-service latency | 0.47 ms |
| P95 API-service latency | 0.85 ms |

Latency excludes HTTP transport and model download because this is the deterministic in-process baseline.

## Failure analysis

One query—“想看一部韩国科幻电影”—expects the Korean space film but returns no candidate. The parser treats “科幻” as a hard catalog tag while the expected demo title carries “太空 / 剧情”. Failure type: `structured_filter_conflict_or_no_candidate`.

Next comparison: run the same 50 cases with the BGE backend, retain structured country/media filters, and test whether softening inferred tags improves Recall@10 without admitting region/type conflicts.
