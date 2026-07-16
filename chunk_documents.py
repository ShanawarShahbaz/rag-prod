"""
Chunks the sample corpus (Data/pdf, Data/text, Data/markdown) using
RecursiveCharacterTextSplitter with token-based length (tiktoken),
splitting on semantic separators (\n\n -> \n -> sentence -> word).

Output: chunks.jsonl, one JSON object per chunk:
  {"id", "source", "doc_type", "chunk_index", "text", "n_tokens"}
"""
import json
import os

import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "Data")
OUTPUT_PATH = os.path.join(BASE_DIR, "chunks.jsonl")

CHUNK_SIZE_TOKENS = 500
CHUNK_OVERLAP_TOKENS = 75

ENCODING = tiktoken.get_encoding("cl100k_base")


def token_length(text: str) -> int:
    return len(ENCODING.encode(text))


splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    encoding_name="cl100k_base",
    chunk_size=CHUNK_SIZE_TOKENS,
    chunk_overlap=CHUNK_OVERLAP_TOKENS,
    separators=["\n\n", "\n", ". ", " ", ""],
)


def load_pdf(path: str) -> str:
    reader = PdfReader(path)
    return "\n\n".join(page.extract_text() or "" for page in reader.pages)


def load_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def iter_source_files():
    for filename in sorted(os.listdir(os.path.join(DATA_DIR, "pdf"))):
        if filename.endswith(".pdf"):
            yield os.path.join(DATA_DIR, "pdf", filename), "pdf"
    for filename in sorted(os.listdir(os.path.join(DATA_DIR, "text"))):
        if filename.endswith(".txt"):
            yield os.path.join(DATA_DIR, "text", filename), "text"
    for root, _, files in os.walk(os.path.join(DATA_DIR, "markdown")):
        for filename in sorted(files):
            if filename.endswith(".md"):
                yield os.path.join(root, filename), "markdown"


def main():
    chunk_count = 0
    with open(OUTPUT_PATH, "w", encoding="utf-8") as out:
        for path, doc_type in iter_source_files():
            text = load_pdf(path) if doc_type == "pdf" else load_text(path)
            if not text.strip():
                print(f"skip (empty): {path}")
                continue

            chunks = splitter.split_text(text)
            source = os.path.relpath(path, DATA_DIR)

            for i, chunk in enumerate(chunks):
                record = {
                    "id": f"{source}::{i}",
                    "source": source,
                    "doc_type": doc_type,
                    "chunk_index": i,
                    "text": chunk,
                    "n_tokens": token_length(chunk),
                }
                out.write(json.dumps(record, ensure_ascii=False) + "\n")
                chunk_count += 1

            print(f"{source}: {len(chunks)} chunks")

    print(f"\ntotal chunks: {chunk_count}")
    print(f"written to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
