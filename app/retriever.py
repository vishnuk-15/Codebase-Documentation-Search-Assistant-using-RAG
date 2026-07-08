"""
retriever.py
------------
Hybrid retrieval: combines BM25 (lexical) and FAISS/SBERT (semantic) search
results using min-max normalized weighted score fusion, so queries that are
either keyword-heavy ("JWT refresh endpoint") or purely conceptual ("how do
users get logged in") both retrieve well.
"""

from dataclasses import dataclass

from app.config import TOP_K_RETRIEVE, TOP_K_RESULTS, SEMANTIC_WEIGHT, BM25_WEIGHT
from app.ingest import SearchIndex, Chunk


@dataclass
class RetrievedChunk:
    chunk: Chunk
    semantic_score: float
    bm25_score: float
    fused_score: float
    matched_via: str    # "semantic", "keyword", or "both"


def _min_max_normalize(scores: list[float]) -> list[float]:
    if not scores:
        return scores
    lo, hi = min(scores), max(scores)
    if hi - lo < 1e-9:
        return [0.5 for _ in scores]
    return [(s - lo) / (hi - lo) for s in scores]


def hybrid_search(index: SearchIndex, query: str) -> list[RetrievedChunk]:
    # --- semantic leg ---
    semantic_hits = index.vectorstore.similarity_search_with_score(query, k=TOP_K_RETRIEVE)
    # FAISS returns L2 distance (lower = better); convert to a similarity-style score
    semantic_by_id: dict[int, float] = {}
    for doc, distance in semantic_hits:
        cid = doc.metadata["chunk_id"]
        semantic_by_id[cid] = -distance  # negate so higher = better, for consistent fusion

    # --- keyword leg ---
    tokens = SearchIndex._tokenize(query)
    bm25_scores = index.bm25.get_scores(tokens)
    ranked_bm25 = sorted(enumerate(bm25_scores), key=lambda x: x[1], reverse=True)[:TOP_K_RETRIEVE]
    bm25_by_id: dict[int, float] = {cid: score for cid, score in ranked_bm25}

    candidate_ids = set(semantic_by_id) | set(bm25_by_id)

    raw_semantic = [semantic_by_id.get(cid, min(semantic_by_id.values(), default=0.0)) for cid in candidate_ids]
    raw_bm25 = [bm25_by_id.get(cid, 0.0) for cid in candidate_ids]

    norm_semantic = dict(zip(candidate_ids, _min_max_normalize(raw_semantic)))
    norm_bm25 = dict(zip(candidate_ids, _min_max_normalize(raw_bm25)))

    results: list[RetrievedChunk] = []
    for cid in candidate_ids:
        s = norm_semantic[cid]
        b = norm_bm25[cid]
        fused = SEMANTIC_WEIGHT * s + BM25_WEIGHT * b

        in_semantic = cid in semantic_by_id
        in_bm25 = cid in bm25_by_id and bm25_by_id[cid] > 0
        matched_via = "both" if (in_semantic and in_bm25) else ("semantic" if in_semantic else "keyword")

        results.append(RetrievedChunk(
            chunk=index.chunks[cid],
            semantic_score=round(s, 3),
            bm25_score=round(b, 3),
            fused_score=round(fused, 3),
            matched_via=matched_via,
        ))

    results.sort(key=lambda r: r.fused_score, reverse=True)
    return results[:TOP_K_RESULTS]
