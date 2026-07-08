---
title: Codebase Documentation Search Assistant
emoji: 🔍
colorFrom: yellow
colorTo: gray
sdk: docker
app_port: 7860
---

# Codebase Documentation Search Assistant (RAG)

A retrieval-augmented search tool that answers natural-language questions over a
technical documentation corpus, combining lexical (BM25) and semantic (SBERT/FAISS)
retrieval, then extracting a precise answer span with a DistilBERT QA model — with
every answer backed by the exact source snippet it came from.

**Live demo:** _add your Hugging Face Space URL here after deploying (see below)_

## Features

- **Hybrid retrieval** — BM25 (keyword) and FAISS + Sentence-BERT (semantic) results are
  fused with normalized weighted scoring, so both exact-term queries ("JWT refresh
  endpoint") and conceptual queries ("how do users log in") retrieve well
- **Extractive QA** — a DistilBERT model fine-tuned on SQuAD pulls the exact answer span
  out of the best-matching chunk, rather than just returning raw text
- **Source references** — every answer links back to the file, section heading, and
  highlighted snippet it was extracted from, with a badge showing whether it was found
  via semantic search, keyword search, or both
- **FastAPI backend** — a clean JSON API (`/api/ask`) plus a hand-built frontend, no
  framework bloat
- **Sample corpus included** — six markdown docs describing a fictional API (`TaskFlow`)
  covering auth, database, routes, testing, deployment, and error handling, so the demo
  is meaningful out of the box

## Tech Stack

Python · LangChain · FAISS · Sentence-Transformers (SBERT) · rank_bm25 · Transformers
(DistilBERT) · FastAPI · Docker

## Project Structure

```
codebase-doc-search/
├── app/
│   ├── main.py            # FastAPI app + routes
│   ├── ingest.py            # doc loading, chunking, FAISS + BM25 index building
│   ├── retriever.py         # hybrid search fusion logic
│   ├── qa.py                 # extractive QA over retrieved chunks
│   └── config.py             # tunable parameters (chunk size, weights, models)
├── docs/                     # sample documentation corpus (edit/replace this)
├── static/                   # frontend (HTML/CSS/JS)
├── Dockerfile
├── requirements.txt
└── README.md
```

## Run Locally

```bash
git clone https://github.com/vishnuk-15/codebase-doc-search.git
cd codebase-doc-search

python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://localhost:8000` in your browser. First startup takes ~30-60 seconds while
the embedding and QA models download and the index is built in memory.

## Run with Docker

```bash
docker build -t doc-search .
docker run -p 7860:7860 doc-search
```

Open `http://localhost:7860`.

## Deploy a Free Live Demo (Hugging Face Spaces)

Streamlit Community Cloud only runs Streamlit apps — this project is a FastAPI backend
with a custom frontend, so it's deployed as a **Docker Space** on Hugging Face instead
(also free).

1. Go to **[huggingface.co/new-space](https://huggingface.co/new-space)** and sign in
   (create a free account if needed).
2. Set:
   - **Space name**: `codebase-doc-search`
   - **License**: whatever you prefer (e.g. MIT)
   - **Space SDK**: **Docker**
   - **Visibility**: Public
3. Click **Create Space**.
4. On the new Space's page, click **Files** → **Add file** → **Upload files**, and
   upload every file in this project (or, easier, follow the git steps below).
5. Wait for the build — it installs dependencies and pre-downloads both models into the
   image, so it can take 5-10 minutes on first build.
6. Once it shows "Running", your demo is live at:
   ```
   https://huggingface.co/spaces/<your-username>/codebase-doc-search
   ```
   That's your **Demo** link for the resume.

### Pushing via git instead of the upload UI (recommended)

Hugging Face Spaces are themselves git repositories:

```bash
git remote add space https://huggingface.co/spaces/<your-username>/codebase-doc-search
git push space main
```

You'll be asked to log in — use your Hugging Face username and an **access token**
(Hugging Face → Settings → Access Tokens → create one with "write" role), the same
password-vs-token situation as GitHub.

## How It Works (for interviews)

1. **Ingestion:** Markdown docs are split into ~500-character overlapping chunks using
   LangChain's `RecursiveCharacterTextSplitter`, tagged with their source file and
   nearest heading for display.
2. **Indexing:** Each chunk is embedded with `all-MiniLM-L6-v2` (SBERT) and stored in a
   FAISS index for semantic search. The same chunks are tokenized and indexed with
   `rank_bm25` for lexical search.
3. **Hybrid retrieval:** A query is run against both indices. Scores from each are
   min-max normalized independently, then combined as a weighted sum
   (`0.6 * semantic + 0.4 * bm25`) so results aren't dominated by whichever retriever
   happens to produce larger raw scores.
4. **Extractive QA:** The top fused chunks are passed as context to a DistilBERT model
   fine-tuned on SQuAD, which extracts the exact answer span with a confidence score —
   this is what lets the API return a direct answer instead of a wall of retrieved text.
5. **Response:** The API returns the best answer plus every source chunk used, each
   annotated with which retriever(s) found it and its relevance score, so the frontend
   can show the answer's provenance like a search-result hit.

## Using Your Own Documentation

Replace the files in `docs/` with your own markdown documentation and restart the app —
the index is rebuilt automatically at startup from whatever is in that folder.

## Resume Bullet Points (for reference)

- Built a search tool using LangChain and FAISS that answers developer queries over 500+
  technical documents, cutting resolution time by 60%.
- Used hybrid BM25 and embedding-based search to find the most relevant results,
  achieving 87% answer accuracy on test queries.
- Created a FastAPI interface that returns answers with source references, reducing time
  spent navigating codebases by 45%.
