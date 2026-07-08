"""
config.py
---------
Central configuration for the RAG pipeline.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = BASE_DIR / "docs"
INDEX_DIR = BASE_DIR / ".index"

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
QA_MODEL_NAME = "distilbert-base-cased-distilled-squad"

CHUNK_SIZE = 500          # characters per chunk
CHUNK_OVERLAP = 80        # overlap between consecutive chunks

TOP_K_RETRIEVE = 8        # candidates pulled from each retriever before fusion
TOP_K_RESULTS = 4         # final number of sources shown to the user

# Hybrid fusion weights (must sum to 1.0)
SEMANTIC_WEIGHT = 0.6
BM25_WEIGHT = 0.4
