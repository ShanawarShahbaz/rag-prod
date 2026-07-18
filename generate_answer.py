"""
Full RAG: retrieves top-k chunks for a query via query_index.search(),
then generates an answer with gpt-4o-mini grounded in those chunks,
with inline source citations.

generate_async() uses AsyncOpenAI so the API can serve concurrent requests
without a thread blocked on each network call -- generate() (sync) is kept
for CLI use.

Usage: python3 generate_answer.py "your question here" [top_k]
"""
import os
import sys
import time

from dotenv import load_dotenv
from openai import AsyncOpenAI, OpenAI

from rerank import search_with_rerank, search_with_rerank_async
from telemetry import generation_latency, tokens_counter, tracer

load_dotenv()

CHAT_MODEL = "gpt-4o-mini"

client = OpenAI()
async_client = AsyncOpenAI()

SYSTEM_PROMPT = (
    "You are a helpful assistant that answers questions using only the "
    "provided context. Each context chunk is labeled with a source number. "
    "Cite sources inline like [1], [2] after the claims they support. "
    "If the context doesn't contain the answer, say so explicitly instead "
    "of guessing."
)


def build_context(chunks: list[dict]) -> str:
    parts = []
    for i, chunk in enumerate(chunks, 1):
        parts.append(f"[{i}] Source: {chunk['source']}\n{chunk['text']}")
    return "\n\n".join(parts)


def _messages(context: str, query: str) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"},
    ]


def _format_answer(response, chunks: list[dict]) -> str:
    answer = response.choices[0].message.content
    sources_list = "\n".join(
        f"[{i}] {c['source']} (chunk {c['chunk_index']})" for i, c in enumerate(chunks, 1)
    )
    return f"{answer}\n\nSources:\n{sources_list}"


def _record_usage(response, gen_span):
    usage = response.usage
    tokens_counter.add(usage.prompt_tokens, {"type": "prompt"})
    tokens_counter.add(usage.completion_tokens, {"type": "completion"})
    gen_span.set_attribute("prompt_tokens", usage.prompt_tokens)
    gen_span.set_attribute("completion_tokens", usage.completion_tokens)


def generate(query: str, top_k: int = 3, candidate_k: int = 20, chunks: list[dict] = None) -> str:
    with tracer.start_as_current_span("rag_query") as query_span:
        query_span.set_attribute("question", query)
        query_span.set_attribute("top_k", top_k)

        if chunks is None:
            chunks = search_with_rerank(query, top_k, candidate_k)
        context = build_context(chunks)

        with tracer.start_as_current_span("generation") as gen_span:
            gen_span.set_attribute("model", CHAT_MODEL)
            t0 = time.perf_counter()
            response = client.chat.completions.create(
                model=CHAT_MODEL, messages=_messages(context, query), temperature=0.2,
            )
            generation_latency.record(time.perf_counter() - t0)
            _record_usage(response, gen_span)

    return _format_answer(response, chunks)


async def generate_async(query: str, top_k: int = 3, candidate_k: int = 20, chunks: list[dict] = None) -> str:
    with tracer.start_as_current_span("rag_query") as query_span:
        query_span.set_attribute("question", query)
        query_span.set_attribute("top_k", top_k)

        if chunks is None:
            chunks = await search_with_rerank_async(query, top_k, candidate_k)
        context = build_context(chunks)

        with tracer.start_as_current_span("generation") as gen_span:
            gen_span.set_attribute("model", CHAT_MODEL)
            t0 = time.perf_counter()
            response = await async_client.chat.completions.create(
                model=CHAT_MODEL, messages=_messages(context, query), temperature=0.2,
            )
            generation_latency.record(time.perf_counter() - t0)
            _record_usage(response, gen_span)

    return _format_answer(response, chunks)


def main():
    if len(sys.argv) < 2:
        print('Usage: python3 generate_answer.py "your question here" [top_k]')
        sys.exit(1)

    query = sys.argv[1]
    top_k = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    print(generate(query, top_k))


if __name__ == "__main__":
    main()
