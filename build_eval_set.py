"""
Builds a synthetic retrieval eval set: samples chunks across the corpus,
asks gpt-4o-mini to write one question answerable from each chunk, and
records the chunk's id as ground truth.

Output: eval_set.jsonl - {"question": ..., "expected_id": "<chunk id>"}
"""
import json
import os
import random

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
META_PATH = os.path.join(BASE_DIR, "chunks_with_meta.jsonl")
EVAL_PATH = os.path.join(BASE_DIR, "eval_set.jsonl")

CHAT_MODEL = "gpt-4o-mini"
SAMPLES_PER_DOC_TYPE_TARGET = 40  # total questions, spread across sources
MIN_CHARS = 300  # skip tiny/boilerplate chunks

client = OpenAI()

QUESTION_PROMPT = (
    "Write exactly one specific, self-contained question that can only be "
    "answered using the information in the passage below. Do not reference "
    "'the passage' or 'the text' in the question. Return only the question, "
    "no preamble.\n\nPassage:\n{text}"
)


def load_chunks():
    with open(META_PATH, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def sample_chunks(chunks: list[dict], n: int) -> list[dict]:
    eligible = [c for c in chunks if len(c["text"]) >= MIN_CHARS]

    by_source = {}
    for c in eligible:
        by_source.setdefault(c["source"], []).append(c)

    random.seed(42)
    for bucket in by_source.values():
        random.shuffle(bucket)

    sources = list(by_source.keys())
    sampled = []
    i = 0
    while len(sampled) < n and any(by_source.values()):
        source = sources[i % len(sources)]
        if by_source[source]:
            sampled.append(by_source[source].pop())
        i += 1
        if i > n * 10:
            break
    return sampled


def generate_question(text: str) -> str:
    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[{"role": "user", "content": QUESTION_PROMPT.format(text=text[:2000])}],
        temperature=0.5,
    )
    return response.choices[0].message.content.strip()


def main():
    chunks = load_chunks()
    sampled = sample_chunks(chunks, SAMPLES_PER_DOC_TYPE_TARGET)
    print(f"generating questions for {len(sampled)} sampled chunks")

    with open(EVAL_PATH, "w", encoding="utf-8") as out:
        for i, chunk in enumerate(sampled, 1):
            question = generate_question(chunk["text"])
            record = {
                "question": question,
                "expected_id": chunk["id"],
                "expected_source": chunk["source"],
            }
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            print(f"[{i}/{len(sampled)}] {chunk['id']} -> {question}")

    print(f"\nwrote {len(sampled)} eval questions -> {EVAL_PATH}")


if __name__ == "__main__":
    main()
