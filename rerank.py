"""
Two-stage retrieval: FAISS pulls a wide candidate set (candidate_k), then a
local cross-encoder (cross-encoder/ms-marco-MiniLM-L-6-v2) reranks candidates
by how well each chunk actually answers the query, cutting down to top_k.

Usage: python3 rerank.py "your question here" [top_k] [candidate_k]
"""
import sys

from sentence_transformers import CrossEncoder

from query_index import search

RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

_model = None


def get_model() -> CrossEncoder:
    global _model
    if _model is None:
        _model = CrossEncoder(RERANKER_MODEL)
    return _model


def search_with_rerank(query: str, top_k: int = 5, candidate_k: int = 20):
    candidates = search(query, top_k=top_k, candidate_k=candidate_k)
    if not candidates:
        return []

    pairs = [(query, c["text"]) for c in candidates]
    rerank_scores = get_model().predict(pairs)

    for c, score in zip(candidates, rerank_scores):
        c["rerank_score"] = float(score)

    candidates.sort(key=lambda c: c["rerank_score"], reverse=True)
    return candidates[:top_k]


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
