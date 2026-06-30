import argparse
import json
from pathlib import Path
from statistics import mean

from anime_oscilloscope.demo_catalog import DEMO_CATALOG
from anime_oscilloscope.semantic import (
    HashEmbeddingProvider,
    SemanticSearchRequest,
    SemanticSearchService,
)


def evaluate(dataset: Path) -> dict[str, object]:
    cases = json.loads(dataset.read_text(encoding="utf-8"))
    service = SemanticSearchService(DEMO_CATALOG, HashEmbeddingProvider())
    recall_at_1 = 0
    recall_at_10 = 0
    latencies = []
    failures = []
    for case in cases:
        response = service.search(SemanticSearchRequest(query=case["query"], limit=10))
        ids = [match.anime.id for match in response.results]
        recall_at_1 += int(bool(ids) and ids[0] == case["expected_id"])
        recall_at_10 += int(case["expected_id"] in ids)
        if case["expected_id"] not in ids:
            failures.append(
                {
                    "query": case["query"],
                    "expected_id": case["expected_id"],
                    "returned_ids": ids,
                    "failure_type": "structured_filter_conflict_or_no_candidate",
                }
            )
        latencies.append(response.elapsed_ms)
    ordered = sorted(latencies)
    p95_index = max(0, min(len(ordered) - 1, round(0.95 * len(ordered)) - 1))
    return {
        "cases": len(cases),
        "recall_at_1": round(recall_at_1 / len(cases), 3),
        "recall_at_10": round(recall_at_10 / len(cases), 3),
        "mean_latency_ms": round(mean(latencies), 3),
        "p95_latency_ms": ordered[p95_index],
        "failures": failures,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate deterministic semantic retrieval")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("apps/api/tests/fixtures/semantic_queries.json"),
    )
    arguments = parser.parse_args()
    print(json.dumps(evaluate(arguments.dataset), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
