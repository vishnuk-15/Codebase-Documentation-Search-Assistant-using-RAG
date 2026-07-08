"""
qa.py
-----
Extractive question-answering over the top retrieved chunks. Uses a
DistilBERT model fine-tuned on SQuAD to pull the precise answer span out of
the best-matching context, rather than just returning raw chunks — this is
what lets the API return a direct answer plus the source references it came
from.
"""

from transformers import pipeline

from app.config import QA_MODEL_NAME
from app.retriever import RetrievedChunk


class AnswerEngine:
    def __init__(self):
        self.pipeline = pipeline("question-answering", model=QA_MODEL_NAME, tokenizer=QA_MODEL_NAME)

    def answer(self, question: str, retrieved: list[RetrievedChunk]) -> dict:
        if not retrieved:
            return {
                "answer": "No relevant documentation was found for this question.",
                "confidence": 0.0,
                "sources": [],
            }

        best_answer = None
        best_score = -1.0
        sources = []

        for r in retrieved:
            result = self.pipeline(question=question, context=r.chunk.text)
            sources.append({
                "file": r.chunk.source,
                "heading": r.chunk.heading,
                "snippet": r.chunk.text,
                "matched_via": r.matched_via,
                "relevance": r.fused_score,
                "span_answer": result["answer"],
                "span_score": round(float(result["score"]), 3),
            })
            if result["score"] > best_score:
                best_score = result["score"]
                best_answer = result["answer"]

        sources.sort(key=lambda s: s["relevance"], reverse=True)

        return {
            "answer": best_answer,
            "confidence": round(float(best_score), 3),
            "sources": sources,
        }
