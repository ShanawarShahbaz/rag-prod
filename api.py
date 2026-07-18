"""
Minimal API wrapping the RAG pipeline.

Run: uvicorn api:app --reload
Docs: http://127.0.0.1:8000/docs
"""
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel, Field

from fastapi import FastAPI, HTTPException, Response

from generate_answer import generate
from telemetry import instrument_fastapi, request_counter

app = FastAPI(title="RAG Practice API")
instrument_fastapi(app)


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = Field(3, ge=1, le=20)
    candidate_k: int = Field(20, ge=1, le=100)


class QueryResponse(BaseModel):
    answer: str


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    try:
        answer = generate(request.question, request.top_k, request.candidate_k)
    except Exception as e:
        request_counter.add(1, {"status": "error"})
        raise HTTPException(status_code=500, detail=str(e))
    request_counter.add(1, {"status": "success"})
    return QueryResponse(answer=answer)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics_endpoint():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
