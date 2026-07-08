FROM python:3.11-slim

WORKDIR /code

# System deps needed for building faiss/torch related wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# Pre-download models at build time so the first request isn't slow and so
# the app doesn't need network access at runtime beyond the initial pull.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')" && \
    python -c "from transformers import pipeline; pipeline('question-answering', model='distilbert-base-cased-distilled-squad')"

# Hugging Face Spaces (Docker SDK) expects the app to listen on port 7860
EXPOSE 7860

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
