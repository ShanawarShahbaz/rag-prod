"""
Embeds chunks.jsonl using OpenAI's text-embedding-3-small and writes
embeddings.npy (float32 array, rows aligned to chunks.jsonl line order)
plus chunks_with_meta.jsonl (id/source/doc_type/text, same row order)
for the vector store step to consume.
"""
import json
import os
import time

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHUNKS_PATH = os.path.join(BASE_DIR, "chunks.jsonl")
EMBEDDINGS_PATH = os.path.join(BASE_DIR, "embeddings.npy")
META_PATH = os.path.join(BASE_DIR, "chunks_with_meta.jsonl")

MODEL = "text-embedding-3-small"
BATCH_SIZE = 50
SECONDS_BETWEEN_BATCHES = 5

client = OpenAI()


def load_chunks():
    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def embed_batch(texts: list[str]) -> list[list[float]]:
    response = client.embeddings.create(model=MODEL, input=texts)
    return [item.embedding for item in response.data]


def load_existing_progress():
    if not (os.path.exists(META_PATH) and os.path.exists(EMBEDDINGS_PATH)):
        return [], []
    with open(META_PATH, "r", encoding="utf-8") as f:
        meta_lines = f.readlines()
    embeddings = np.load(EMBEDDINGS_PATH)
    n = min(len(meta_lines), len(embeddings))
    return meta_lines[:n], list(embeddings[:n])


def main():
    chunks = load_chunks()
    print(f"loaded {len(chunks)} chunks")

    existing_meta_lines, all_embeddings = load_existing_progress()
    done = len(existing_meta_lines)
    if done:
        print(f"resuming after {done} already-embedded chunks")

    with open(META_PATH, "w", encoding="utf-8") as meta_out:
        meta_out.writelines(existing_meta_lines)
        for start in range(done, len(chunks), BATCH_SIZE):
            batch = chunks[start:start + BATCH_SIZE]
            texts = [c["text"] for c in batch]

            for attempt in range(5):
                try:
                    vectors = embed_batch(texts)
                    break
                except Exception as e:
                    wait = 2 ** attempt
                    print(f"error on batch {start}: {e} - retrying in {wait}s")
                    time.sleep(wait)
            else:
                raise RuntimeError(f"failed to embed batch starting at {start}")

            all_embeddings.extend(vectors)
            for c in batch:
                meta_out.write(json.dumps({
                    "id": c["id"],
                    "source": c["source"],
                    "doc_type": c["doc_type"],
                    "chunk_index": c["chunk_index"],
                    "text": c["text"],
                }, ensure_ascii=False) + "\n")
            meta_out.flush()
            np.save(EMBEDDINGS_PATH, np.array(all_embeddings, dtype=np.float32))

            print(f"embedded {start + len(batch)}/{len(chunks)}")
            time.sleep(SECONDS_BETWEEN_BATCHES)

    embeddings_array = np.array(all_embeddings, dtype=np.float32)
    print(f"\nsaved embeddings: {embeddings_array.shape} -> {EMBEDDINGS_PATH}")
    print(f"saved metadata -> {META_PATH}")


if __name__ == "__main__":
    main()
