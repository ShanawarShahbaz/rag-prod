"""
Builds a FAISS index from embeddings.npy (cosine similarity via normalized
inner product) and saves it alongside chunks_with_meta.jsonl for retrieval.
"""
import os

import faiss
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EMBEDDINGS_PATH = os.path.join(BASE_DIR, "embeddings.npy")
INDEX_PATH = os.path.join(BASE_DIR, "faiss.index")


def main():
    embeddings = np.load(EMBEDDINGS_PATH)
    faiss.normalize_L2(embeddings)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  # inner product on normalized vectors = cosine similarity
    index.add(embeddings)

    faiss.write_index(index, INDEX_PATH)
    print(f"indexed {index.ntotal} vectors (dim={dim}) -> {INDEX_PATH}")


if __name__ == "__main__":
    main()
