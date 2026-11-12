# Semantic Intent Search Engine

An AI support assistant for an education platform. It answers student questions from a
document knowledge base (RAG), detects intent, scores its own confidence, and can process a
Gmail support inbox automatically — routing anything it is unsure about to a human review queue.

## How a question flows

```
query ─► Query pipeline (normalize, stop words, spelling, expansion)
      ─► BM25 (keyword) ─┐
      ─► FAISS (dense)  ─┴► Reciprocal Rank Fusion ─► Cross-encoder rerank (top 10)
      ─► Gemma via Ollama (answer from top 3 chunks only)
      ─► Intent detector + Confidence engine ─► AUTO_REPLY or HUMAN_REVIEW
```

## Features

- Hybrid retrieval: BM25 + Sentence-Transformers/FAISS + RRF, reranked by `ms-marco-MiniLM-L-6-v2`
- Grounded answers from a local LLM (`gemma4` through Ollama)
- Rule-based intent detection (refund, password reset, payment, certificate, …)
- Confidence engine with an intent-evidence safety gate
- Knowledge base manager: upload / view / delete PDF, DOCX, TXT, MD (index rebuilds automatically)
- Email automation: Gmail IMAP fetch, de-duplication, scheduler, run history, dashboard
- Persistent human review queue for low-confidence emails
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
| POST | `/search` | Answer a question (answer, sources, intent, confidence, routing) |
| GET / DELETE | `/documents` | List / delete knowledge-base files |
| POST | `/documents/upload` | Upload files (multipart) |
| GET | `/documents/content` | Read a file's extracted text |
| POST | `/automation/process` | Run one email through the pipeline |
| POST | `/automation/run` | Check the Gmail inbox now |
| POST | `/automation/scheduler/start` · `/stop` | Control the background scheduler |
| GET | `/automation/dashboard` · `/history` | Statistics and run history |
| GET | `/automation/escalations` | Human review queue (`?status=PENDING`) |
| POST | `/automation/escalations/{id}/resolve` | Mark a review item resolved |

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
data/documents/education/   the knowledge base
semantic-search-frontend/   React UI
```
