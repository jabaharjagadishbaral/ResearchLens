# ResearchLens

### Evidence-Grounded Research Intelligence Platform

**See the evidence. Understand the research. Discover what’s next.**

ResearchLens is an evidence-grounded research assistant for **scientific literature retrieval, analysis, comparison, verification, and synthesis**.

It combines structure-aware document processing, hybrid retrieval, reranking, citation-grounded answering, claim verification, knowledge-graph extraction, controlled research workflows, literature-review generation, and evaluation into a unified research pipeline.

> 🚧 **Work in Progress:** The core research pipeline and service layer are implemented and tested offline. Several production integrations and frontend components are implemented but have not yet been executed in a real environment.

---

## ✨ Features

- 🔎 **Hybrid Retrieval** — BM25 + vector retrieval
- 🎯 **Reranking** — improves evidence selection
- 📚 **Evidence-Grounded Answers** — answers connected to retrieved sources
- 🛡️ **Prompt-Injection Quarantine** — isolates untrusted document instructions
- ⚠️ **Insufficient-Evidence Handling** — avoids unsupported answers
- 🔍 **Claim Verification** — evaluates claims against evidence
- 📊 **Paper Analysis** — structured analysis of research papers
- ⚖️ **Paper Comparison** — compares papers while preserving missing information
- 🕸️ **Knowledge Graph Extraction** — extracts research relationships
- 🔬 **Controlled Research Workflow** — bounded multi-step research execution
- 📝 **Literature Review Generation** — cited research synthesis
- 📈 **Evaluation Framework** — retrieval, grounding, citation, and verification metrics
- 🔐 **Security Layer** — authentication, authorization, rate limiting, and validation
- 📡 **SSE Infrastructure** — server-sent event architecture

---

# 🧠 ResearchLens Pipeline

ResearchLens follows an evidence-first research pipeline:

```text
                         User Question
                              │
                              ▼
                    ┌────────────────────┐
                    │ Document Retrieval │
                    └─────────┬──────────┘
                              │
                 ┌────────────┴────────────┐
                 ▼                         ▼
          ┌─────────────┐           ┌─────────────┐
          │    BM25     │           │    Vector   │
          │  Retrieval  │           │  Retrieval  │
          └──────┬──────┘           └──────┬──────┘
                 │                         │
                 └────────────┬────────────┘
                              ▼
                       ┌─────────────┐
                       │  Reranking  │
                       └──────┬──────┘
                              ▼
                     ┌─────────────────┐
                     │ Evidence Select │
                     └────────┬────────┘
                              ▼
                     ┌─────────────────┐
                     │ Grounded Answer │
                     └────────┬────────┘
                              ▼
                     ┌─────────────────┐
                     │ Claim Verification│
                     └────────┬────────┘
                              ▼
                     ┌─────────────────┐
                     │ Cited Response  │
                     └─────────────────┘
```

The same evidence layer also powers paper analysis, comparison, knowledge-graph extraction, and literature-review generation.

---

# 🔎 Hybrid Retrieval

ResearchLens combines **lexical and semantic retrieval**.

### BM25

Useful for:

- Exact technical terminology
- Keywords
- Model names
- Dataset names
- Specialized phrases

### Vector Retrieval

Useful for:

- Semantic similarity
- Paraphrased questions
- Related concepts
- Contextual matching

The retrieval results are combined before reranking.

```text
Query
  │
  ├──► BM25
  │
  └──► Vector Search
          │
          ▼
    Hybrid Candidates
          │
          ▼
       Reranker
          │
          ▼
     Evidence
```

---

# 📚 Evidence-Grounded Answers

ResearchLens is designed to make generated answers traceable to supporting evidence.

The answering pipeline:

```text
Question
   ↓
Retrieve
   ↓
Rank
   ↓
Select Evidence
   ↓
Generate
   ↓
Attach Citations
   ↓
Verify Claims
   ↓
Return Answer
```

The system also handles insufficient evidence explicitly.

When evidence is unavailable or inadequate, ResearchLens can return an **insufficient-evidence response** rather than inventing information.

Fabricated citation markers such as `[1]`, `[2]`, etc. are stripped when they are not backed by actual retrieved sources.

---

# 🛡️ Prompt-Injection Quarantine

Research documents are treated as **untrusted data**.

A scientific paper may contain text that resembles instructions to an AI system. ResearchLens separates document content from system-level instructions so retrieved content cannot simply redefine the behavior of the research assistant.

```text
Trusted
┌─────────────────────┐
│ System / Application│
│ Instructions        │
└──────────┬──────────┘
           │
           ▼
      AI Pipeline
           ▲
           │
Untrusted │
┌──────────┴──────────┐
│ Retrieved Documents │
│ / Evidence          │
└─────────────────────┘
```

---

# 🔍 Claim Verification

ResearchLens includes a claim-verification pipeline with **five verification labels**.

```text
Claim
  ↓
Retrieve Supporting Evidence
  ↓
Compare Claim ↔ Evidence
  ↓
Verification
  ↓
5 Verification Labels
```

The current implementation uses a **lexical verifier** as an offline stand-in.

> LLM-based verification is planned and is not currently implemented.

---

# 📊 Paper Analysis

ResearchLens can analyze research papers while distinguishing between reported information and unavailable information.

The system avoids filling gaps with unsupported assumptions.

For example:

```text
Dataset: Not reported
```

is preferred over an invented dataset.

This principle is carried into paper comparison and literature synthesis.

---

# ⚖️ Paper Comparison

ResearchLens supports structured paper comparison across available evidence.

Typical dimensions include:

```text
Paper
├── Problem
├── Method
├── Model
├── Dataset
├── Evaluation
├── Results
└── Limitations
```

When information is absent from a source, the comparison reports:

```text
Not reported
```

rather than guessing.

---

# 🕸️ Knowledge Graph

ResearchLens can extract relationships from research documents and construct a research knowledge graph.

Example:

```text
                  ┌──────────────┐
                  │    Paper     │
                  └──────┬───────┘
                         │
                    proposes
                         │
                         ▼
                  ┌──────────────┐
                  │    Method    │
                  └──────┬───────┘
                         │
                    evaluated on
                         │
                         ▼
                  ┌──────────────┐
                  │   Dataset    │
                  └──────┬───────┘
                         │
                       used for
                         │
                         ▼
                  ┌──────────────┐
                  │     Task     │
                  └──────────────┘
```

The graph can represent relationships among:

- Papers
- Methods
- Models
- Datasets
- Tasks
- Concepts
- Results

---

# 🔬 Controlled Research Workflow

ResearchLens includes a dependency-free research workflow engine.

The workflow system uses:

- Static transitions
- Explicit execution states
- Step limits
- Contained node failures

This provides controlled and predictable multi-step research execution.

> The current implementation does not depend on LangGraph.

---

# 📝 Literature Review Generation

ResearchLens can generate literature reviews from retrieved research evidence.

The pipeline produces:

- Evidence-grounded synthesis
- Citations
- References
- References containing only cited sources

```text
Research Documents
        ↓
     Retrieval
        ↓
     Reranking
        ↓
     Evidence
        ↓
    Synthesis
        ↓
     Citations
        ↓
 Literature Review
```

---

# 📈 Evaluation

ResearchLens includes an evaluation framework covering retrieval, ranking, grounding, citation quality, and verification.

## Retrieval Metrics

| Metric | Purpose |
|---|---|
| Recall@K | Relevant evidence retrieved |
| Precision@K | Relevance of retrieved evidence |
| MRR | Ranking quality |
| nDCG | Graded ranking quality |

## Answer & Grounding Metrics

| Metric | Purpose |
|---|---|
| Faithfulness | Evidence grounding |
| Citation Correctness | Whether citations support claims |
| Citation Completeness | Whether claims are sufficiently cited |
| Verification Accuracy | Claim-verification performance |

### Evaluation Dataset

The current development evaluation uses:

```text
evaluation/dev_set.json
```

> ⚠️ The current dataset is small and synthetic. Evaluation numbers are **development results, not benchmark results**.

---

# 🔐 Security

The service layer includes tested implementations for:

- Per-user authorization
- PBKDF2 authentication
- Signed authentication tokens
- Rate limiting
- Upload validation
- SSE frame ordering
- Cascade deletes
- Versioned migrations
- Atomic migration rollback

The OpenAI-compatible client is also tested using a fake transport.

---

# 💾 Persistence

The current persistence layer uses:

**SQLite**

with portable SQL migrations.

Database location can be configured with:

```env
DB_PATH=...
```

PostgreSQL support is planned but is not currently implemented.

---

# 🧪 Testing

Current offline test status:

```text
Backend tests:           56
Frontend-library tests:  5
────────────────────────────
Total:                  61
```

### Tested

#### Frontend

- API client
- SSE parser
- Citation linking
- Graph layout
- TypeScript checking

#### Backend

- Persistence
- Restart round-trip
- Versioned migrations
- Atomic rollback
- Cascade deletes
- Structure-aware chunking
- Hybrid retrieval
- Reranking
- Cited answers
- Injection quarantine
- Claim verification
- Evaluation metrics
- Paper analysis
- Paper comparison
- Knowledge-graph extraction
- Research workflow
- Literature review
- Authentication
- Authorization
- Rate limiting
- Upload validation
- SSE frame ordering
- OpenAI-compatible client

Run the tests:

```bash
make test
```

Run the evaluation:

```bash
make eval
```

---

# 🧰 Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI |
| Frontend | Next.js, React, TypeScript |
| Styling | Plain CSS |
| Database | SQLite |
| Retrieval | BM25 + Vector Retrieval |
| Ranking | Cross-encoder architecture |
| API Streaming | SSE |
| Testing | Pytest, TypeScript |
| Containerization | Docker |
| Vector Store | Qdrant integration |
| Graph Store | Neo4j integration |
| LLM Interface | OpenAI-compatible client |

> Some infrastructure integrations listed above are implemented in code but have not yet been executed in the current environment.

---

# 📂 Project Structure

```text
ResearchLens/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── db/
│   │   ├── documents/
│   │   ├── retrieval/
│   │   └── services/
│   │
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── app/
│   ├── components/
│   └── ...
│
├── evaluation/
│   └── dev_set.json
│
├── docs/
│   ├── architecture/
│   ├── RAG pipeline/
│   ├── agents/
│   ├── verification/
│   ├── document processing/
│   ├── evaluation/
│   ├── security/
│   └── deployment/
│
├── CHANGELOG.md
├── LICENSE
├── Makefile
├── docker-compose.yml
└── README.md
```

---

# ⚙️ Getting Started

## 1. Clone the repository

```bash
git clone https://github.com/jabaharjagadishbaral/ResearchLens.git
cd ResearchLens
```

## 2. Configure environment

```bash
cp .env.example .env
```

Set:

```env
AUTH_SECRET=your-secure-secret
```

## 3. Start the backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.api.main:app
```

## 4. Start the frontend

Open another terminal:

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Frontend:

```text
http://localhost:3000
```

> ⚠️ The frontend and several external integrations have been written but have not yet been browser/runtime-tested in the current environment. First-run integration fixes may therefore be required.

---

# 🧪 Mock Mode

ResearchLens includes offline/local stand-ins for development.

Responses may contain:

```text
mock_mode=True
```

This indicates that a mock/local provider was used.

Mock mode is intended for:

- Development
- Testing
- Pipeline validation
- Offline evaluation
- Reproducibility

It should not be interpreted as production-model performance.

---

# 🚧 Current Limitations

The following components are currently **not built**:

- `/research` workspace
- `/research/[id]` workspace
- Backend workspace model
- Bundled demo papers
- PostgreSQL repository
- Celery/Redis background jobs
- OCR engines
- Figure extraction
- Table extraction
- Vision-based document analysis
- PDF export
- DOCX export
- Langfuse
- LangGraph
- Semantic Scholar adapter
- OpenAlex adapter
- Crossref adapter
- PubMed adapter
- LLM-based verification
- True token-by-token LLM streaming

### Implemented but not yet executed

- Next.js application
- FastAPI application wiring
- Qdrant store
- SentenceTransformer providers
- CrossEncoder providers
- Neo4j graph store
- PyMuPDF PDF processing
- arXiv HTTP integration
- Backend Docker image
- Docker Compose
- CI workflow

---

# 🗺️ Roadmap

## Phase 1 — Core Research Pipeline

- [x] Structure-aware chunking
- [x] BM25 retrieval
- [x] Vector retrieval
- [x] Hybrid retrieval
- [x] Reranking
- [x] Citation-grounded answers
- [x] Injection quarantine
- [x] Insufficient-evidence handling
- [x] Claim verification
- [x] Paper analysis
- [x] Paper comparison
- [x] Knowledge-graph extraction
- [x] Controlled research workflow
- [x] Literature-review generation
- [x] Offline evaluation

## Phase 2 — Product Validation

- [ ] Run Next.js application
- [ ] Run FastAPI application
- [ ] Browser testing
- [ ] End-to-end integration testing
- [ ] Demo papers
- [ ] Research workspace
- [ ] UI/UX refinement

## Phase 3 — Production Infrastructure

- [ ] Production Qdrant integration
- [ ] SentenceTransformer embeddings
- [ ] Cross-encoder reranking
- [ ] Neo4j graph storage
- [ ] PostgreSQL repository
- [ ] Redis
- [ ] Celery background jobs

## Phase 4 — Multimodal Research

- [ ] OCR
- [ ] Figure extraction
- [ ] Table extraction
- [ ] Vision-language document analysis
- [ ] Multimodal retrieval
- [ ] Figure-aware evidence analysis

## Phase 5 — Research Discovery

- [ ] Semantic Scholar
- [ ] OpenAlex
- [ ] Crossref
- [ ] PubMed
- [ ] Research-gap detection
- [ ] Citation graph analysis
- [ ] Research trend discovery
- [ ] LLM-based verification

## Phase 6 — Production Platform

- [ ] PDF export
- [ ] DOCX export
- [ ] Observability
- [ ] Production deployment
- [ ] CI/CD hardening
- [ ] Large-scale benchmark
- [ ] Public evaluation dataset

---

# 🎯 Design Principles

### Evidence First

Prefer evidence-supported answers over confident unsupported answers.

### Citation Traceability

Claims should remain connected to the evidence supporting them.

### Missing Information Stays Missing

If a source does not report something:

```text
Not reported
```

is better than an invented value.

### Documents Are Untrusted Data

Retrieved documents should never automatically become system instructions.

### Evaluation Matters

Research systems should be measured using explicit metrics rather than judged only by response quality.

### Controlled Autonomy

Research workflows should be bounded, observable, and predictable.

---

# 🔭 Vision

ResearchLens aims to evolve from a conventional RAG application into a broader **research intelligence platform**.

```text
Discover
   ↓
Retrieve
   ↓
Understand
   ↓
Compare
   ↓
Verify
   ↓
Connect
   ↓
Synthesize
   ↓
Identify Research Gaps
   ↓
Discover What’s Next
```

The goal is not simply to build another AI chatbot.

The goal is to make AI-assisted research:

**Traceable.  
Verifiable.  
Reproducible.  
Evidence-driven.**

---

# 📚 Documentation

Detailed technical documentation is available in [`docs/`](./docs):

- Architecture
- RAG pipeline
- Research workflows
- Verification
- Document processing
- Evaluation
- Security
- Deployment

---

# 🤝 Contributing

Contributions, bug reports, feature requests, and improvements are welcome.

Please read [`CONTRIBUTING.md`](./CONTRIBUTING.md) before contributing.

---

# 🔐 Security

If you discover a security vulnerability, please follow the project's security policy rather than publicly disclosing the vulnerability through an issue.

See the repository's **Security Policy** for reporting instructions.

---

# 📝 Changelog

See [`CHANGELOG.md`](./CHANGELOG.md) for project changes and updates.

---

# 📜 License

ResearchLens is released under the **MIT License**.

See [`LICENSE`](./LICENSE) for the complete license text.

---

<div align="center">

## ResearchLens

**See the evidence. Understand the research. Discover what’s next.**

Built for evidence-grounded scientific research.

</div>
