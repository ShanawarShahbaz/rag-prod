# RAG Practice Pipeline

An end-to-end Retrieval-Augmented Generation pipeline built for learning: ingest
documents, chunk them, embed and index them, retrieve, rerank, and generate
grounded answers with citations — plus an eval harness to measure retrieval
quality at each stage.

## Pipeline stages

```
Data/ (pdf, text, markdown)
      │  chunk_documents.py
      ▼
chunks.jsonl
      │  embed_chunks.py  (OpenAI text-embedding-3-small)
      ▼
embeddings.npy + chunks_with_meta.jsonl
      │  build_faiss_index.py
      ▼
faiss.index
      │  query_index.py (vector search) → rerank.py (cross-encoder)
      ▼
generate_answer.py  (gpt-4o-mini, cited answer)
```

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install langchain-text-splitters tiktoken pypdf python-dotenv openai numpy faiss-cpu sentence-transformers
```

Create a `.env` file in the project root:

```
OPENAI_API_KEY=sk-...
```

## Files

| File | Purpose |
|---|---|
| `download_samples.py` | Downloads a starter corpus into `Data/`: arXiv PDFs, Project Gutenberg text, and a markdown docs repo |
| `chunk_documents.py` | Splits all docs in `Data/` into chunks using `RecursiveCharacterTextSplitter` (token-based, 500 tokens/75 overlap, splits on `\n\n` → `\n` → sentence → word). Writes `chunks.jsonl` |
| `embed_chunks.py` | Embeds every chunk with `text-embedding-3-small`. Batches requests, retries with backoff, resumable if interrupted. Writes `embeddings.npy` + `chunks_with_meta.jsonl` |
| `build_faiss_index.py` | Builds a `faiss.index` (`IndexFlatIP` on L2-normalized vectors = cosine similarity) from `embeddings.npy` |
| `query_index.py` | Embeds a query and does a plain FAISS vector search. `search(query, top_k, candidate_k)` — used directly, or as stage 1 of reranking |
| `rerank.py` | Two-stage retrieval: FAISS pulls `candidate_k` candidates (default 20), then a local cross-encoder (`cross-encoder/ms-marco-MiniLM-L-6-v2`) rescores and returns the top `top_k` |
| `generate_answer.py` | Full RAG: reranked retrieval (`top_k=3` default) → `gpt-4o-mini` generates an answer grounded in the retrieved chunks, with inline `[1]`, `[2]` citations mapped to sources |
| `build_eval_set.py` | Generates a synthetic retrieval eval set: samples chunks across all sources, asks `gpt-4o-mini` to write one question per chunk, records the chunk id as ground truth. Writes `eval_set.jsonl` |
| `eval_retrieval.py` | Runs every eval question through retrieval and scores Hit@1, Recall@k, and MRR. Supports `--rerank` to compare vector-only vs. reranked retrieval. Logs per-question ranks to `eval_results.jsonl` |
| `eval_generation.py` | LLM-as-judge eval of full RAG output: scores each answer on Faithfulness, Answer Relevancy, and Context Precision using `gpt-4o-mini` as judge. Logs per-question scores + reasoning to `generation_eval_results.jsonl` |
| `api.py` | FastAPI wrapper exposing the pipeline as a `POST /query` endpoint (question → generated answer + sources), plus `GET /health` and `GET /metrics` |
| `telemetry.py` | OpenTelemetry setup: trace export to Jaeger (OTLP), custom Prometheus metrics (stage latency, retrieval confidence, token usage, request counts) |
| `docker-compose.monitoring.yml` + `prometheus.yml` | Local Jaeger + Prometheus stack for viewing traces/metrics |

### Generated data files (not source, regenerate as needed)

- `chunks.jsonl` — chunked text + metadata, no embeddings
- `chunks_with_meta.jsonl` — same chunks, row-aligned with `embeddings.npy`
- `embeddings.npy` — (N, 1536) float32 embedding matrix
- `faiss.index` — FAISS vector index built from `embeddings.npy`
- `eval_set.jsonl` — synthetic eval questions + expected chunk ids
- `eval_results.jsonl` — last retrieval eval run's per-question ranks
- `generation_eval_results.jsonl` — last generation eval run's per-question faithfulness/relevancy/precision scores

## Usage

Run the pipeline once, in order:

```bash
python3 download_samples.py
python3 chunk_documents.py
python3 embed_chunks.py
python3 build_faiss_index.py
```

Then query it:

```bash
# plain vector search
python3 query_index.py "How does self-attention work in transformers?" 5

# reranked search
python3 rerank.py "How does self-attention work in transformers?" 5 20

# full RAG answer with citations (top_k=3 default)
python3 generate_answer.py "How does self-attention work in transformers?"
```

Evaluate retrieval quality:

```bash
python3 build_eval_set.py           # regenerate eval_set.jsonl (only needed once, or after re-chunking)
python3 eval_retrieval.py 5                 # vector-only baseline
python3 eval_retrieval.py 5 --rerank 20     # with cross-encoder reranking
```

Evaluate generation quality (LLM-as-judge):

```bash
python3 eval_generation.py                  # all 40 questions, top_k=3 default
python3 eval_generation.py 40 5             # override top_k, e.g. to compare against 5
```

## Eval results

### Retrieval (40 synthetic questions, top_k=5)

| Metric | Vector-only | + Cross-encoder rerank |
|---|---|---|
| Hit@1 | 50.0% | 67.5% |
| Recall@5 | 82.5% | 87.5% |
| MRR | 0.615 | 0.754 |

Reranking gives the largest lift on Hit@1 — the cross-encoder scores
query+chunk jointly, which is much better at picking the single best chunk
than embedding similarity alone. Most remaining misses are chunk-boundary
near-misses (the answer sentence sits just outside the retrieved chunk),
suggesting overlap tuning as the next lever, followed by chunk size tuning.

### Generation quality (LLM-as-judge, 40 questions, reranked retrieval)

| Metric | top_k=5 | top_k=3 (current default) |
|---|---|---|
| Faithfulness | 90.4% | **95.4%** |
| Answer Relevancy | 93.0% | 91.5% |
| Context Precision | 47.0% | **55.8%** |

`top_k=3` is the default because it improves faithfulness and context
precision with negligible relevancy cost — fewer, more-focused chunks means
less irrelevant material for the model to potentially misuse. The one
regression seen when dropping from 5→3 was a case where the correct chunk
fell outside the smaller context window; the model correctly said "the
context doesn't contain this" rather than hallucinating, which is the right
failure mode. If you need to prioritize recall over precision (e.g. broader,
open-ended questions), pass a larger `top_k` explicitly.

## API

A minimal FastAPI wrapper (`api.py`) exposes the full RAG pipeline over HTTP.

```bash
pip install fastapi "uvicorn[standard]"
uvicorn api:app --reload
```

Interactive docs: `http://127.0.0.1:8000/docs`

```bash
curl -X POST http://127.0.0.1:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "How does self-attention work in transformers?", "top_k": 3, "candidate_k": 20}'
```

Response:

```json
{ "answer": "... generated answer with [1][2] citations ...\n\nSources:\n[1] ..." }
```

`GET /health` returns `{"status": "ok"}` for liveness checks.

## Monitoring

The pipeline is instrumented with **OpenTelemetry**: traces show the
per-request waterfall (retrieval → rerank → generation), and custom metrics
(latency per stage, retrieval confidence, token usage, request counts) are
exposed in Prometheus format on the API.

- `telemetry.py` — sets up the OTel `TracerProvider` (exports spans via OTLP
  to Jaeger) and `MeterProvider` (exposes metrics via `PrometheusMetricReader`),
  plus `instrument_fastapi()` for automatic HTTP-level spans
- `rerank.py` — wraps vector search and cross-encoder rerank in spans, records
  `rag_retrieval_latency_seconds`, `rag_rerank_latency_seconds`, and
  `rag_retrieval_top_score` (a retrieval-confidence proxy)
- `generate_answer.py` — wraps the OpenAI call in a `generation` span, records
  `rag_generation_latency_seconds` and `rag_tokens_total` (prompt/completion)
- `api.py` — auto-instruments all HTTP routes, tracks `rag_requests_total`
  by status, exposes `GET /metrics` for Prometheus to scrape

### Run the local stack

```bash
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp-proto-http \
  opentelemetry-instrumentation-fastapi opentelemetry-exporter-prometheus prometheus-client

docker compose -f docker-compose.monitoring.yml up -d   # Jaeger + Prometheus
uvicorn api:app --reload
```

- Jaeger UI (traces): http://localhost:16686 — select service `rag-pipeline`
- Prometheus UI (metrics): http://localhost:9090 — e.g. query
  `histogram_quantile(0.95, rag_generation_latency_seconds_bucket)` for p95
  generation latency, or `rate(rag_tokens_total[5m])` for token usage rate
- Raw metrics: `curl http://127.0.0.1:8000/metrics`

Prometheus scrapes the API via `host.docker.internal:8000` (see
`prometheus.yml`) — no Dockerfile needed for the API itself, it just needs to
be running locally on port 8000.

Stop the stack: `docker compose -f docker-compose.monitoring.yml down`

## Design notes / things to know

- **Chunking**: recursive character splitting with token-aware length
  (tiktoken `cl100k_base`), not fixed-width — respects paragraph/sentence
  boundaries before falling back to word splits.
- **Embeddings**: OpenAI has per-minute token rate limits on lower usage
  tiers; `embed_chunks.py` batches at 50 chunks/request with a 5s pause
  between batches and is resumable (re-running picks up where it left off
  by comparing `chunks_with_meta.jsonl` length against `chunks.jsonl`).
- **Similarity metric**: embeddings are L2-normalized before indexing, so
  FAISS inner product == cosine similarity.
- **Reranker** runs locally (no API cost, no extra key) via
  `sentence-transformers`. First run downloads the model (~80MB) and caches
  it.
- **Eval set is synthetic**, not hand-labeled — a small fraction of
  "misses" are actually eval-labeling artifacts (e.g. a question generated
  from a bibliography chunk whose real answer lives in a different paper),
  not genuine retrieval failures. Spot-check `eval_results.jsonl` misses
  before trusting the numbers at face value.
- **Generation eval (`eval_generation.py`) is also LLM-as-judge**, so it
  inherits judge noise/pedantry — e.g. it may mark a correct claim as
  "unsupported" over a literal wording mismatch with the context. Spot-check
  low scores in `generation_eval_results.jsonl` before treating them as real
  faithfulness failures.
