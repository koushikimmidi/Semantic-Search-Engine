# Changelog

All notable changes to this project.

## 2.2.0 — Brand colour

- Deep-teal brand colour across the interface: solid brand sidebar, primary buttons,
  links, focus rings, selected items and single-series charts (all text meets WCAG AA contrast)
- Sign-in page with a brand panel summarising what the product does
- Light top bar for a crisp split against the sidebar; matching dark theme

## 2.1.0 — Interface redesign

- New interface design: IBM Plex type, warm neutral palette, line icons, light and dark themes
- Ask page shows the answer and its sources side by side, with numbered citations
- Review queue laid out like a help-desk inbox (message list + reply panel)
- Pages have their own URLs (`#queue`, `#users`, …) so refresh keeps your place
- Project tidied for public release: development experiments moved to `scripts/experiments/`,
  history moved to `docs/history/`, generated caches no longer tracked

## 2.0.0 — Accounts, portals and analytics

- User accounts with two portals: **Admin console** and **Employee workspace**
- First-run admin setup protected by `ADMIN_API_KEY`; hashed passwords, signed sessions,
  lockout after repeated failures
- Users page (create, disable, reset password, change role) and a full audit log
- Analytics: email outcomes, questions, topics, confidence, review-queue health,
  knowledge gaps and team activity
- System page: component health and runtime settings (auto-replies, mark-as-read, schedule, re-index)
- UI talks to the API through `/api` (Vite proxy in development, nginx in Docker)

## 1.2.0 — Retrieval, intent and automation upgrades

- Sentence-aware chunking with section headings and real PDF page numbers
- Persistent embedding cache; FAISS switched to cosine similarity
- Education-specific query expansion; reranking on the user's original question
- Few-shot embedding intent classifier combined with keyword rules (95.6% accuracy on the eval set)
- Streaming answers with inline citations
- Threaded email replies, Message-ID de-duplication, newsletter / no-reply filtering
- API keys with viewer / agent / admin roles
- pytest suite, GitHub Actions CI, Docker Compose stack

## 1.1.0 — Email automation and web interface

- Gmail inbox automation with scheduler, run history and human review queue
- Confidence engine and intent detection deciding auto-reply vs. human review
- React interface: ask questions, manage the knowledge base, automation dashboard
- Security fixes for document paths and uploads

## 1.0.0 — Search engine

- BM25 and dense (FAISS + Sentence-Transformers) retrieval
- Reciprocal Rank Fusion and cross-encoder reranking
- Query preprocessing pipeline, logging, profiling, JSON configuration
- Local LLM answers through Ollama (RAG)
