"""
Queries the FAISS index: embeds the query with text-embedding-3-small,
searches for top-k nearest chunks, and prints them.

Usage: python3 query_index.py "your question here" [top_k]
"""
import json
import os
import sys

import faiss
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_PATH = os.path.join(BASE_DIR, "faiss.index")
META_PATH = os.path.join(BASE_DIR, "chunks_with_meta.jsonl")

MODEL = "text-embedding-3-small"

client = OpenAI()


def load_meta():
    with open(META_PATH, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def embed_query(text: str) -> np.ndarray:
    response = client.embeddings.create(model=MODEL, input=[text])
    vector = np.array([response.data[0].embedding], dtype=np.float32)
    faiss.normalize_L2(vector)
    return vector


def search(query: str, top_k: int = 5, candidate_k: int = None):
    index = faiss.read_index(INDEX_PATH)
    meta = load_meta()

    query_vector = embed_query(query)
    scores, indices = index.search(query_vector, candidate_k or top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        chunk = meta[idx]
        results.append({"score": float(score), **chunk})
    return results


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
