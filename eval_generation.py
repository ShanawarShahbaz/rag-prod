"""
Answer-quality eval (LLM-as-judge) for the full RAG pipeline: for each
question in eval_set.jsonl, runs retrieval+rerank+generation, then scores
the result on three axes using gpt-4o-mini as judge:

  Faithfulness      - fraction of claims in the answer that are actually
                       supported by the retrieved context (catches hallucination)
  Answer Relevancy  - does the answer actually address the question, fully
                       and directly
  Context Precision - fraction of retrieved chunks that are relevant to the
                       question (signal on retrieval noise, independent of
                       whether the *correct* chunk was found)

Usage: python3 eval_generation.py [n_questions] [top_k] [candidate_k]
"""
import json
import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

from generate_answer import build_context, generate
from rerank import search_with_rerank

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EVAL_PATH = os.path.join(BASE_DIR, "eval_set.jsonl")
RESULTS_PATH = os.path.join(BASE_DIR, "generation_eval_results.jsonl")

JUDGE_MODEL = "gpt-4o-mini"
TOP_K = 5
CANDIDATE_K = 20

client = OpenAI()

FAITHFULNESS_PROMPT = """You are evaluating whether an AI-generated answer is faithful to (fully supported by) the provided context.

Context:
{context}

Answer:
{answer}

Break the answer down into its individual factual claims. For each claim, determine if it is directly supported by the context. Then output JSON:
{{"total_claims": <int>, "supported_claims": <int>, "score": <supported_claims / total_claims as a float between 0 and 1>, "reasoning": "<brief explanation of any unsupported or hallucinated claims>"}}
Return only valid JSON."""

ANSWER_RELEVANCY_PROMPT = """Question: {question}

Answer: {answer}

Rate how relevant and complete this answer is with respect to the question, on a scale from 0.0 (irrelevant or a non-answer) to 1.0 (directly and completely answers the question). Penalize answers that are evasive, off-topic, or only partially address the question.
Output JSON: {{"score": <float between 0 and 1>, "reasoning": "<brief explanation>"}}
Return only valid JSON."""

CONTEXT_PRECISION_PROMPT = """Question: {question}

Below are context chunks retrieved for this question, numbered.

{numbered_chunks}

For each chunk, determine if it is relevant/useful for answering the question.
Output JSON: {{"relevance": [<bool for chunk 1>, <bool for chunk 2>, ...]}}
Return only valid JSON, with exactly {n} booleans in the array."""


def judge(prompt: str) -> dict:
    response = client.chat.completions.create(
        model=JUDGE_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0,
    )
    return json.loads(response.choices[0].message.content)


def score_faithfulness(context: str, answer: str) -> dict:
    return judge(FAITHFULNESS_PROMPT.format(context=context, answer=answer))


def score_answer_relevancy(question: str, answer: str) -> dict:
    return judge(ANSWER_RELEVANCY_PROMPT.format(question=question, answer=answer))


def score_context_precision(question: str, chunks: list[dict]) -> dict:
    numbered = "\n\n".join(f"[{i}] {c['text']}" for i, c in enumerate(chunks, 1))
    result = judge(CONTEXT_PRECISION_PROMPT.format(question=question, numbered_chunks=numbered, n=len(chunks)))
    relevance = result.get("relevance", [])
    score = sum(1 for r in relevance if r) / len(relevance) if relevance else 0.0
    return {"score": score, "relevance": relevance}


def load_eval_set(n: int = None):
    with open(EVAL_PATH, "r", encoding="utf-8") as f:
        items = [json.loads(line) for line in f]
    return items[:n] if n else items


def evaluate(n_questions: int = None, top_k: int = TOP_K, candidate_k: int = CANDIDATE_K):
    eval_items = load_eval_set(n_questions)

    faithfulness_scores = []
    relevancy_scores = []
    precision_scores = []
    results_log = []

    for i, item in enumerate(eval_items, 1):
        question = item["question"]

        chunks = search_with_rerank(question, top_k, candidate_k)
        context = build_context(chunks)
        full_answer = generate(question, top_k, candidate_k, chunks=chunks)
        answer = full_answer.split("\n\nSources:")[0]

        faith = score_faithfulness(context, answer)
        relevancy = score_answer_relevancy(question, answer)
        precision = score_context_precision(question, chunks)

        faithfulness_scores.append(faith["score"])
        relevancy_scores.append(relevancy["score"])
        precision_scores.append(precision["score"])

        results_log.append({
            "question": question,
            "answer": answer,
            "faithfulness": faith,
            "answer_relevancy": relevancy,
            "context_precision": precision,
        })

        print(f"[{i}/{len(eval_items)}] faith={faith['score']:.2f} relevancy={relevancy['score']:.2f} "
              f"precision={precision['score']:.2f} | {question[:60]}")

    with open(RESULTS_PATH, "w", encoding="utf-8") as out:
        for r in results_log:
            out.write(json.dumps(r, ensure_ascii=False) + "\n")

    n = len(eval_items)
    print(f"\n--- Generation Quality Eval (n={n}, top_k={top_k}, candidate_k={candidate_k}) ---")
    print(f"Faithfulness:      {sum(faithfulness_scores) / n:.2%}")
    print(f"Answer Relevancy:  {sum(relevancy_scores) / n:.2%}")
    print(f"Context Precision: {sum(precision_scores) / n:.2%}")
    print(f"\nfull results logged in: {RESULTS_PATH}")


if __name__ == "__main__":
    n_questions = int(sys.argv[1]) if len(sys.argv) > 1 else None
    top_k = int(sys.argv[2]) if len(sys.argv) > 2 else TOP_K
    candidate_k = int(sys.argv[3]) if len(sys.argv) > 3 else CANDIDATE_K
    evaluate(n_questions, top_k, candidate_k)
