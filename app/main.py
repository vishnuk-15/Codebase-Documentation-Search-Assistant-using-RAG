"""
main.py
-------
FastAPI application exposing the RAG codebase-documentation search assistant.
"""

import time
import threading
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.ingest import SearchIndex
from app.retriever import hybrid_search
from app.qa import AnswerEngine
from app.config import DOCS_DIR

_state = {"index": None, "engine": None, "ready": False, "error": None}


def _load_models():
    try:
        print("[startup] building hybrid search index...", flush=True)
        index = SearchIndex().build()
        print(f"[startup] index built: {len(index.chunks)} chunks", flush=True)

        print("[startup] loading QA model...", flush=True)
        engine = AnswerEngine()
        print("[startup] QA model loaded", flush=True)

        _state["index"] = index
        _state["engine"] = engine
        _state["ready"] = True
        print("[startup] ready to serve requests", flush=True)
    except Exception as e:
        _state["error"] = str(e)
        print("[startup] FAILED:", e, flush=True)
        traceback.print_exc()


@asynccontextmanager
async def lifespan(app: FastAPI):
    thread = threading.Thread(target=_load_models, daemon=True)
    thread.start()
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
    if _state["error"]:
        return {"status": "error", "detail": _state["error"]}
    return {"status": "ok" if _state["ready"] else "starting"}


@app.get("/api/stats")
def stats():
    index: SearchIndex = _state["index"]
    if not index:
        return {"documents": len(list(DOCS_DIR.glob("*.md"))), "chunks": 0, "ready": False}
    return {
        "documents": len(list(DOCS_DIR.glob("*.md"))),
        "chunks": len(index.chunks),
        "ready": True,
    }


@app.post("/api/ask", response_model=AskResponse)
def ask(payload: AskRequest):
    if _state["error"]:
        raise HTTPException(status_code=500, detail=f"Model failed to load: {_state['error']}")
    if not _state["ready"]:
        raise HTTPException(status_code=503, detail="Models are still warming up, try again in a few seconds.")

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
