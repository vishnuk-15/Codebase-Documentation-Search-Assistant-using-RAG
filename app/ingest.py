"""
ingest.py
---------
Loads the markdown documentation corpus, splits it into overlapping chunks,
and builds two indices over those chunks:
  1. A FAISS vector index (semantic search) via LangChain's FAISS wrapper,
     using sentence-transformer embeddings.
  2. A BM25 index (lexical/keyword search) via rank_bm25.

Both indices are built in-memory at process startup. For a corpus of this
size (a documentation set) this takes a few seconds; for much larger
corpora the FAISS index would be persisted to disk with `.save_local()`.
"""

import re
from dataclasses import dataclass
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rank_bm25 import BM25Okapi

from app.config import DOCS_DIR, EMBEDDING_MODEL_NAME, CHUNK_SIZE, CHUNK_OVERLAP


@dataclass
class Chunk:
    text: str
    source: str        # filename
    heading: str        # nearest markdown heading, for display
    chunk_id: int


def _load_documents() -> list[tuple[str, str]]:
    """Returns list of (filename, raw_text) for every markdown file in DOCS_DIR."""
    docs = []
    for path in sorted(DOCS_DIR.glob("*.md")):
        docs.append((path.name, path.read_text(encoding="utf-8")))
    return docs


def _nearest_heading(text: str, position: int) -> str:
    """Finds the closest markdown heading (# ...) at or before `position`."""
    headings = list(re.finditer(r"^#+\s+(.*)$", text[:position], flags=re.MULTILINE))
    return headings[-1].group(1).strip() if headings else "Overview"


def build_chunks() -> list[Chunk]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "],
    )

    chunks: list[Chunk] = []
    chunk_id = 0
    for filename, text in _load_documents():
        splits = splitter.split_text(text)
        cursor = 0
        for split in splits:
            pos = text.find(split[:40], cursor)
            pos = pos if pos != -1 else cursor
            heading = _nearest_heading(text, pos)
            chunks.append(Chunk(text=split.strip(), source=filename, heading=heading, chunk_id=chunk_id))
            chunk_id += 1
            cursor = pos

    return chunks


class SearchIndex:
    """Holds the built FAISS and BM25 indices plus the chunk metadata."""

    def __init__(self):
        self.chunks: list[Chunk] = []
        self.vectorstore: FAISS | None = None
        self.bm25: BM25Okapi | None = None
        self._bm25_corpus_tokens: list[list[str]] = []

    def build(self):
        self.chunks = build_chunks()
        texts = [c.text for c in self.chunks]

        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
        metadatas = [{"source": c.source, "heading": c.heading, "chunk_id": c.chunk_id} for c in self.chunks]
        self.vectorstore = FAISS.from_texts(texts, embeddings, metadatas=metadatas)

        self._bm25_corpus_tokens = [self._tokenize(t) for t in texts]
        self.bm25 = BM25Okapi(self._bm25_corpus_tokens)

        return self

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return re.findall(r"[a-zA-Z0-9_]+", text.lower())
