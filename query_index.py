"""
Queries the FAISS index: embeds the query with text-embedding-3-small,
searches for top-k nearest chunks, and prints them.

The FAISS index and chunk metadata are loaded once at import time, not on
every call to search() -- reloading them from disk per-request was a real
bottleneck under concurrent load.

Usage: python3 query_index.py "your question here" [top_k]
"""
import json
import os
import sys

import faiss
import numpy as np
from dotenv import load_dotenv
from openai import AsyncOpenAI, OpenAI

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_PATH = os.path.join(BASE_DIR, "faiss.index")
META_PATH = os.path.join(BASE_DIR, "chunks_with_meta.jsonl")

MODEL = "text-embedding-3-small"

client = OpenAI()
async_client = AsyncOpenAI()

_index = faiss.read_index(INDEX_PATH)
with open(META_PATH, "r", encoding="utf-8") as f:
    _meta = [json.loads(line) for line in f]


def embed_query(text: str) -> np.ndarray:
    response = client.embeddings.create(model=MODEL, input=[text])
    vector = np.array([response.data[0].embedding], dtype=np.float32)
    faiss.normalize_L2(vector)
    return vector


async def embed_query_async(text: str) -> np.ndarray:
    response = await async_client.embeddings.create(model=MODEL, input=[text])
    vector = np.array([response.data[0].embedding], dtype=np.float32)
    faiss.normalize_L2(vector)
    return vector


def _search_vectors(query_vector: np.ndarray, top_k: int, candidate_k: int = None):
    scores, indices = _index.search(query_vector, candidate_k or top_k)
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        chunk = _meta[idx]
        results.append({"score": float(score), **chunk})
    return results


def search(query: str, top_k: int = 5, candidate_k: int = None):
    query_vector = embed_query(query)
    return _search_vectors(query_vector, top_k, candidate_k)


async def search_async(query: str, top_k: int = 5, candidate_k: int = None):
    query_vector = await embed_query_async(query)
    return _search_vectors(query_vector, top_k, candidate_k)


def main():
    if len(sys.argv) < 2:
        print('Usage: python3 query_index.py "your question here" [top_k]')
        sys.exit(1)

    query = sys.argv[1]
    top_k = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    results = search(query, top_k)
    for i, r in enumerate(results, 1):
        print(f"\n--- #{i} | score={r['score']:.4f} | {r['source']} (chunk {r['chunk_index']}) ---")
        print(r["text"][:400].strip())


if __name__ == "__main__":
    main()
