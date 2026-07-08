"""
main.py
-------
FastAPI application exposing the RAG codebase-documentation search assistant.

Endpoints:
  GET  /health        — liveness check
  GET  /api/stats      — corpus stats (doc count, chunk count)
  POST /api/ask         — ask a question, get an answer + source references
  GET  /                — serves the static frontend
"""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.ingest import SearchIndex
from app.retriever import hybrid_search
from app.qa import AnswerEngine
from app.config import DOCS_DIR

_state = {"index": None, "engine": None, "ready": False}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Build the hybrid index and load the QA model once at startup, not per-request.
    index = SearchIndex().build()
    engine = AnswerEngine()
    _state["index"] = index
    _state["engine"] = engine
    _state["ready"] = True
    yield
    _state.clear()


app = FastAPI(title="Codebase Documentation Search Assistant", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)


class SourceRef(BaseModel):
    file: str
    heading: str
    snippet: str
    matched_via: str
    relevance: float
    span_answer: str
    span_score: float


class AskResponse(BaseModel):
    answer: str
    confidence: float
    sources: list[SourceRef]
    latency_ms: int


@app.get("/health")
def health():
    return {"status": "ok" if _state["ready"] else "starting"}


@app.get("/api/stats")
def stats():
    index: SearchIndex = _state["index"]
    if not index:
        return {"documents": 0, "chunks": 0}
    return {
        "documents": len(list(DOCS_DIR.glob("*.md"))),
        "chunks": len(index.chunks),
    }


@app.post("/api/ask", response_model=AskResponse)
def ask(payload: AskRequest):
    start = time.time()
    index: SearchIndex = _state["index"]
    engine: AnswerEngine = _state["engine"]

    retrieved = hybrid_search(index, payload.question)
    result = engine.answer(payload.question, retrieved)
    latency_ms = int((time.time() - start) * 1000)

    return AskResponse(
        answer=result["answer"],
        confidence=result["confidence"],
        sources=[SourceRef(**s) for s in result["sources"]],
        latency_ms=latency_ms,
    )


app.mount("/assets", StaticFiles(directory="static"), name="assets")


@app.get("/")
def serve_index():
    return FileResponse("static/index.html")
