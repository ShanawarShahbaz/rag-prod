"""
Two-stage retrieval: FAISS pulls a wide candidate set (candidate_k), then a
local cross-encoder (cross-encoder/ms-marco-MiniLM-L-6-v2) reranks candidates
by how well each chunk actually answers the query, cutting down to top_k.

search_with_rerank_async() runs the CPU-bound cross-encoder inference in a
thread executor so it doesn't block the event loop -- important under
concurrent load, since the sync version otherwise ties up a full request's
worth of wall-clock time on one thread.

Usage: python3 rerank.py "your question here" [top_k] [candidate_k]
"""
import asyncio
import sys
import time

from sentence_transformers import CrossEncoder

from query_index import search, search_async
from telemetry import rerank_latency, retrieval_latency, retrieval_top_score, tracer

RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

_model = None


def get_model() -> CrossEncoder:
    global _model
    if _model is None:
        _model = CrossEncoder(RERANKER_MODEL)
    return _model


def _rerank(query: str, candidates: list[dict], top_k: int, span) -> list[dict]:
    pairs = [(query, c["text"]) for c in candidates]
    t0 = time.perf_counter()
    rerank_scores = get_model().predict(pairs)
    rerank_latency.record(time.perf_counter() - t0)

    for c, score in zip(candidates, rerank_scores):
        c["rerank_score"] = float(score)

    candidates.sort(key=lambda c: c["rerank_score"], reverse=True)
    results = candidates[:top_k]
    if results:
        top_score = results[0]["rerank_score"]
        retrieval_top_score.record(top_score)
        span.set_attribute("top_score", top_score)
    return results


def search_with_rerank(query: str, top_k: int = 5, candidate_k: int = 20):
    with tracer.start_as_current_span("retrieval") as span:
        span.set_attribute("candidate_k", candidate_k)
        t0 = time.perf_counter()
        candidates = search(query, top_k=top_k, candidate_k=candidate_k)
        retrieval_latency.record(time.perf_counter() - t0)
        span.set_attribute("candidates_found", len(candidates))

    if not candidates:
        return []

    with tracer.start_as_current_span("rerank") as span:
        span.set_attribute("top_k", top_k)
        return _rerank(query, candidates, top_k, span)


async def search_with_rerank_async(query: str, top_k: int = 5, candidate_k: int = 20):
    with tracer.start_as_current_span("retrieval") as span:
        span.set_attribute("candidate_k", candidate_k)
        t0 = time.perf_counter()
        candidates = await search_async(query, top_k=top_k, candidate_k=candidate_k)
        retrieval_latency.record(time.perf_counter() - t0)
        span.set_attribute("candidates_found", len(candidates))

    if not candidates:
        return []

    with tracer.start_as_current_span("rerank") as span:
        span.set_attribute("top_k", top_k)
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _rerank, query, candidates, top_k, span)


def main():
    if len(sys.argv) < 2:
        print('Usage: python3 rerank.py "your question here" [top_k] [candidate_k]')
        sys.exit(1)

    query = sys.argv[1]
    top_k = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    candidate_k = int(sys.argv[3]) if len(sys.argv) > 3 else 20

    results = search_with_rerank(query, top_k, candidate_k)
    for i, r in enumerate(results, 1):
        print(f"\n--- #{i} | rerank={r['rerank_score']:.4f} | vector={r['score']:.4f} | {r['source']} (chunk {r['chunk_index']}) ---")
        print(r["text"][:400].strip())


if __name__ == "__main__":
    main()
