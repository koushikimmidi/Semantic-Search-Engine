# Backend API image (CPU only).
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_EXTRA_INDEX_URL=https://download.pytorch.org/whl/cpu \
    HF_HOME=/app/.cache/huggingface \
    NLTK_DATA=/app/.cache/nltk_data

WORKDIR /app

# Dependencies first for better layer caching. The extra index makes
# pip pick the CPU build of torch (much smaller than the CUDA build).
COPY requirements.txt .
RUN pip install -r requirements.txt

# Download the NLTK tokenizer data at build time (works offline later).
RUN python -c "import nltk; [nltk.download(p, quiet=True) for p in ('punkt', 'punkt_tab')]"

COPY backend ./backend
COPY scripts ./scripts
COPY data/intent ./data/intent
COPY data/eval ./data/eval
COPY data/documents/education ./data/documents/education

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=300s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/', timeout=4)"

CMD ["uvicorn", "backend.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
