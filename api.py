"""
Minimal API wrapping the RAG pipeline.

Run: uvicorn api:app --reload
Docs: http://127.0.0.1:8000/docs
"""
from pydantic import BaseModel, Field

from fastapi import FastAPI, HTTPException

from generate_answer import generate

app = FastAPI(title="RAG Practice API")


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
        raise HTTPException(status_code=500, detail=str(e))
    return QueryResponse(answer=answer)


@app.get("/health")
def health():
    return {"status": "ok"}
