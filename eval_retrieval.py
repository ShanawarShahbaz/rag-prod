"""
Evaluates retrieval quality against eval_set.jsonl using query_index.search().

Metrics:
  Hit@1   - fraction where the expected chunk is the top result
  Recall@k - fraction where the expected chunk appears in the top-k results
  MRR     - mean reciprocal rank of the expected chunk (0 if absent from top-k)

Usage: python3 eval_retrieval.py [top_k] [--rerank] [candidate_k]
"""
import json
import os
import sys

from query_index import search

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EVAL_PATH = os.path.join(BASE_DIR, "eval_set.jsonl")
RESULTS_PATH = os.path.join(BASE_DIR, "eval_results.jsonl")


def load_eval_set():
    with open(EVAL_PATH, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def evaluate(top_k: int = 5, use_rerank: bool = False, candidate_k: int = 20):
    eval_items = load_eval_set()

    if use_rerank:
        from rerank import search_with_rerank

    hits_at_1 = 0
    hits_at_k = 0
    reciprocal_ranks = []
    results_log = []

    for i, item in enumerate(eval_items, 1):
        question = item["question"]
        expected_id = item["expected_id"]

        if use_rerank:
            results = search_with_rerank(question, top_k, candidate_k)
        else:
            results = search(question, top_k)
        retrieved_ids = [r["id"] for r in results]

        rank = retrieved_ids.index(expected_id) + 1 if expected_id in retrieved_ids else None

        if rank == 1:
            hits_at_1 += 1
        if rank is not None:
            hits_at_k += 1
            reciprocal_ranks.append(1 / rank)
        else:
            reciprocal_ranks.append(0)

        results_log.append({
            "question": question,
            "expected_id": expected_id,
            "retrieved_ids": retrieved_ids,
            "rank": rank,
        })
        status = f"rank {rank}" if rank else "MISS"
        print(f"[{i}/{len(eval_items)}] {status:8s} | {question[:70]}")

    n = len(eval_items)
    hit_at_1 = hits_at_1 / n
    recall_at_k = hits_at_k / n
    mrr = sum(reciprocal_ranks) / n

    with open(RESULTS_PATH, "w", encoding="utf-8") as out:
        for r in results_log:
            out.write(json.dumps(r, ensure_ascii=False) + "\n")

    mode = "rerank" if use_rerank else "vector-only"
    print(f"\n--- Retrieval Eval ({mode}, top_k={top_k}, n={n}) ---")
    print(f"Hit@1:      {hit_at_1:.2%}")
    print(f"Recall@{top_k}:   {recall_at_k:.2%}")
    print(f"MRR:        {mrr:.4f}")
    print(f"\nmisses logged in: {RESULTS_PATH}")


if __name__ == "__main__":
    args = sys.argv[1:]
    use_rerank = "--rerank" in args
    args = [a for a in args if a != "--rerank"]

    top_k = int(args[0]) if len(args) > 0 else 5
    candidate_k = int(args[1]) if len(args) > 1 else 20

    evaluate(top_k, use_rerank, candidate_k)
