# ResearchMind AI — evidence-grounded research assistant (work in progress)

Pipeline implemented and tested offline (`make test`, `make eval`): structure-aware chunking with
page/section metadata -> BM25 + vector hybrid retrieval -> reranking -> cited answers (fabricated
`[n]` stripped, injection quarantine, explicit insufficient-evidence reply) -> claim verification
(5 labels) -> paper analysis/comparison ("Not reported" for gaps) -> knowledge-graph extraction ->
controlled research workflow (static transitions, step cap, contained node failures) ->
literature-review generator (cited, references list only cited sources) -> evaluation metrics
(Recall@K, Precision@K, MRR, nDCG, faithfulness, citation correctness/completeness, verification accuracy).

## Honest status
**Tested (56 backend + 5 frontend-library tests, `make test`):** frontend API client, SSE parser, citation linking and graph layout (type-checked with tsc), persistence (restart round-trip, versioned migrations with atomic rollback, cascade deletes), chunking, hybrid retrieval, reranking, cited answers, injection
quarantine, claim verification, evaluation metrics, paper analysis/comparison, graph extraction, workflow,
literature review, and the whole service layer (`app/services`): per-user authorization, PBKDF2 auth + signed
tokens, rate limiting, upload validation, SSE frame ordering, and an OpenAI-compatible client against a fake transport.

**Written but never executed: the Next.js app (`frontend/app`, `components`: login, dashboard, papers, paper analysis, chat with SSE + evidence panel, compare, graph, reports, evaluation, settings; plain CSS, not Tailwind/shadcn; no `npm install` or browser run yet), (no packages/network/Docker in my sandbox):** `app/api/main.py` (FastAPI wiring),
`retrieval/qdrant_store.py`, SentenceTransformer/CrossEncoder providers, `Neo4jGraphStore`, `documents/pdf.py`
(PyMuPDF), arXiv HTTP fetch, `backend/Dockerfile`, `docker-compose.yml`, CI workflow. Expect first-run fixes.

**Mock mode:** `local` providers and the lexical verifier are offline stand-ins (`mock_mode=True` in responses).
Eval numbers come from a tiny synthetic dev set (`evaluation/dev_set.json`) and are not a benchmark.

**Not built:** `/research` and `/research/[id]` workspace pages (no workspace model in the backend), bundled demo papers, Postgres repository (persistence is SQLite via `app/db/repo.py` with portable SQL migrations; set `DB_PATH`),
Celery/Redis jobs (uploads index synchronously), OCR engines, figure/table extraction and vision analysis,
PDF/DOCX export, Langfuse, LangGraph (workflow is dependency-free), Semantic Scholar/OpenAlex/Crossref/PubMed
adapters, real token streaming (SSE streams the finished answer), LLM-based verification.

## Run
```
cp .env.example .env            # set AUTH_SECRET
cd backend && pip install -r requirements.txt && uvicorn app.api.main:app
```

## Frontend
```
cd frontend && cp .env.example .env.local && npm install && npm run dev   # http://localhost:3000
```

Docs: see `docs/` (architecture, RAG pipeline, agents, verification, document processing, evaluation, security, deployment).
