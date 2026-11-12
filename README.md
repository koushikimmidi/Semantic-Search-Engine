# Semantic Intent Search Engine

An AI support assistant for an education platform. It answers student questions from a
document knowledge base (RAG), detects intent, scores its own confidence, and can process a
Gmail support inbox automatically — routing anything it is unsure about to a human review queue.

## How a question flows

```
query ─► Query pipeline (normalize, stop words, corpus spelling, education synonyms)
      ─► BM25 (keyword) ──────┐
      ─► FAISS (cosine dense) ┴► Reciprocal Rank Fusion
      ─► Cross-encoder rerank on the ORIGINAL question (top 10)
      ─► Gemma via Ollama: streamed answer with [n] citations (up to 4 sources)
      ─► Hybrid intent (rules + embedding classifier) + Confidence engine
      ─► AUTO_REPLY or HUMAN_REVIEW
```

## Features

- Sentence-aware chunking with section headings and real PDF page numbers
- Persistent embedding cache: only new or edited chunks are re-encoded
- Hybrid retrieval: BM25 + Sentence-Transformers/FAISS + RRF, reranked by `ms-marco-MiniLM-L-6-v2`
- Grounded, streamed answers with clickable inline citations (`gemma4` through Ollama)
- Hybrid intent detection: precise rules + few-shot embedding classifier
- Confidence engine with an intent-evidence safety gate, thresholds tuned on a labelled set
- API key authentication with viewer / agent / admin roles
- Knowledge base manager: upload / view / delete PDF, DOCX, TXT, MD (index rebuilds automatically)
- Email automation: Gmail IMAP fetch, Message-ID de-duplication, optional mark-as-read,
  threaded replies, newsletter/no-reply filtering, scheduler, run history, dashboard
- Persistent human review queue; agents edit the suggested answer and reply in-thread
- React + Vite frontend with search history, dark mode, and an automation dashboard

## Setup

Requirements: Python 3.13, Node 20+, [Ollama](https://ollama.com) with the model pulled.

```bash
ollama pull gemma4
python -m venv venv
venv\Scripts\pip install -r requirements.txt
cd semantic-search-frontend && npm install
```

Copy `.env.example` to `.env` and fill in your values (use a Gmail **App Password**).
`AUTOMATION_SEND_EMAILS=false` keeps the system in safe mode: answers are generated but never sent.

## Run

```bash
venv\Scripts\python -m uvicorn backend.api.app:app --port 8000
```

```bash
cd semantic-search-frontend && npm run dev
```

Open http://localhost:5173. API docs: http://localhost:8000/docs.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/auth/me` | Current role (viewer / agent / admin) |
| POST | `/search` | Answer a question (answer, sources, intent, confidence, routing) |
| POST | `/search/stream` | Same, streamed as NDJSON events (`sources`, `token`…, `done`) |
| GET / DELETE | `/documents` | List / delete knowledge-base files |
| POST | `/documents/upload` | Upload files (multipart) |
| GET | `/documents/content` | Read a file's extracted text |
| POST | `/automation/process` | Run one email through the pipeline |
| POST | `/automation/run` | Check the Gmail inbox now |
| POST | `/automation/scheduler/start` · `/stop` | Control the background scheduler |
| GET | `/automation/dashboard` · `/history` | Statistics and run history |
| GET | `/automation/escalations` | Human review queue (`?status=PENDING`) |
| POST | `/automation/escalations/{id}/resolve` | Mark a review item resolved |
| POST | `/automation/escalations/{id}/reply` | Send an agent reply (threaded) and resolve |

Roles: no key = **viewer** (search, browse documents); **agent** = automation and review
queue; **admin** = also upload/delete documents and the scheduler. Send the key as
`X-API-Key` (the UI has a 🔑 field in the sidebar). With no keys configured, auth is off.

## Docker

```bash
cp .env.example .env
docker compose up --build
```

Starts Ollama (and pulls the model, about 10 GB for gemma4), the API on :8000 and the UI on
http://localhost:8080.

## Tests and evaluation

```bash
venv\Scripts\pip install -r requirements-dev.txt
venv\Scripts\python -m pytest
```

```bash
set RUN_INTEGRATION=1 && venv\Scripts\python -m pytest tests/test_integration.py
```

```bash
venv\Scripts\python -m scripts.evaluate_intent
```

```bash
venv\Scripts\python -m scripts.evaluate_pipeline --full
```

Unit tests use fakes for the models and the LLM (fast, run in CI). The evaluation scripts use
`data/eval/eval_set.json` (45 labelled questions). Latest full run: auto-reply precision 100%,
coverage 47%, intent accuracy 95.6%. GitHub Actions (`.github/workflows/ci.yml`) runs the tests,
frontend lint/build and the Docker image builds.

## Project layout

```
backend/
  api/            FastAPI app
  engine/         SearchEngine (orchestrates retrieval)
  retrieval/      BM25          embeddings/  encoder + FAISS
  hybrid/         RRF fusion    reranker/    cross-encoder
  query/          query preprocessing pipeline
  rag/  llm/      RAG pipeline + Ollama client
  intent/  confidence/   intent detection and confidence scoring
  automation/     email fetch/send, runner, scheduler, history, escalations
  api/auth.py     API key roles
data/documents/education/   the knowledge base
data/intent/                labelled examples for the intent classifier
data/eval/                  labelled evaluation set
tests/                      pytest suite
semantic-search-frontend/   React UI
```
