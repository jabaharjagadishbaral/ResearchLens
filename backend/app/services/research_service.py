"""Framework-agnostic application service: every API endpoint is a method here (and is unit-tested)."""
from __future__ import annotations

import json
import tempfile
import uuid
from dataclasses import asdict
from typing import Iterator

from app.agents.workflow import ResearchWorkflow
from app.analysis.compare import compare_papers, to_markdown
from app.analysis.paper import analyze_paper
from app.core.config import Settings
from app.core.security import RateLimiter, ServiceError, validate_upload
from app.documents.chunking import PageText, chunk_document
from app.db.repo import SQLiteRepository
from app.documents.pdf import extract_pages
from app.documents.tables import parse_tables
from app.knowledge_graph.graph import build_graph
from app.providers.base import EmbeddingProvider, LLMProvider, RerankerProvider
from app.rag.pipeline import RAGPipeline
from app.reports.literature_review import generate_review
from app.retrieval.hybrid import HybridRetriever, rerank
from app.retrieval.vector_store import InMemoryVectorStore, VectorStore
from app.research.sources import ResearchSource
from app.verification.verifier import ClaimVerifier, summarize

MAX_QUESTION = 2000


class ResearchService:
    def __init__(self, settings: Settings, embedder: EmbeddingProvider, reranker: RerankerProvider,
                 llm: LLMProvider, verifier: ClaimVerifier, store: VectorStore | None = None,
                 repo: SQLiteRepository | None = None) -> None:
        self.s = settings
        self.retriever = HybridRetriever(embedder, store or InMemoryVectorStore(), settings.hybrid_alpha)
        self.pipe = RAGPipeline(self.retriever, reranker, llm, settings)
        self.verifier = verifier
        self.sources: list[ResearchSource] = []     # external research adapters (configured by the app)
        self.limiter = RateLimiter(settings.rate_limit_per_minute)
        self.repo = repo or SQLiteRepository(":memory:")
        self._docs: dict[str, dict] = {d["id"]: d for d in self.repo.documents()}
        stored = self.repo.chunks()
        if stored:                      # rebuild vector + keyword indexes from persisted chunks
            self.retriever.index(stored)

    # ---- helpers -------------------------------------------------------------------------
    def _owned(self, user: str) -> set[str]:
        return {i for i, d in self._docs.items() if d["owner"] == user}

    def _doc(self, user: str, doc_id: str) -> dict:
        d = self._docs.get(doc_id)
        if not d or d["owner"] != user:       # same error for missing and foreign: no existence leak
            raise ServiceError("not_found", "Document not found.")
        return d

    @staticmethod
    def _question(q: str) -> str:
        q = (q or "").strip()
        if not q or len(q) > MAX_QUESTION:
            raise ServiceError("invalid_input", f"Provide a question of 1-{MAX_QUESTION} characters.")
        return q

    # ---- documents -----------------------------------------------------------------------
    def upload(self, user: str, filename: str, data: bytes, title: str | None = None) -> dict:
        self.limiter.check(f"{user}:upload")
        ext, safe = validate_upload(filename, data, self.s.max_upload_bytes)
        ocr_pages: list[int] = []
        if ext == "pdf":
            try:
                with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
                    f.write(data); f.flush()
                    extracted = extract_pages(f.name)
            except RuntimeError:
                raise ServiceError("unavailable", "PDF extraction is not available on this server.") from None
            except Exception:
                raise ServiceError("invalid_upload", "The PDF could not be read.") from None
            pages = [e.page for e in extracted]
            ocr_pages = [e.page.page for e in extracted if e.needs_ocr]
        else:
            pages = [PageText(i, t) for i, t in enumerate(data.decode("utf-8").split("\f"), 1)]
        if not any(p.text.strip() for p in pages):
            raise ServiceError("ocr_required", "No extractable text found. Scanned PDFs need an OCR engine, "
                                               "which is not configured.")
        first = next((ln.strip() for p in pages for ln in p.text.splitlines() if ln.strip()), safe)
        doc_id = uuid.uuid4().hex[:12]
        chunks = chunk_document(pages, doc_id, (title or first)[:160], source=safe,
                                min_chars=self.s.chunk_min_chars, max_chars=self.s.chunk_max_chars)
        if not chunks:
            raise ServiceError("invalid_upload", "No readable content found in the file.")
        doc = {"id": doc_id, "owner": user, "title": chunks[0].document_title, "filename": safe,
               "pages": len(pages), "chunks": len(chunks), "ocr_pages": ocr_pages, "status": "indexed"}
        self.repo.add_document(doc, chunks, parse_tables(pages))      # persist first: a DB failure leaves nothing half-indexed
        self.retriever.index(chunks)
        self._docs[doc_id] = doc
        return self.public_doc(self._docs[doc_id])

    @staticmethod
    def public_doc(d: dict) -> dict:
        return {k: v for k, v in d.items() if k != "owner"}

    def list_documents(self, user: str) -> list[dict]:
        return [self.public_doc(self._docs[i]) for i in sorted(self._owned(user))]

    def get_document(self, user: str, doc_id: str) -> dict:
        return self.public_doc(self._doc(user, doc_id))

    def tables(self, user: str, doc_id: str) -> list[dict]:
        self._doc(user, doc_id)
        return self.repo.tables(doc_id)

    def evidence(self, user: str, chunk_id: str) -> dict:
        c = self.retriever.get_chunk(chunk_id)
        if c is None:
            raise ServiceError("not_found", "Evidence not found.")
        self._doc(user, c.document_id)
        return {"chunk_id": c.chunk_id, "document_id": c.document_id, "document_title": c.document_title,
                "authors": list(c.authors), "page": c.page, "section": c.section, "text": c.text,
                "source": c.source}

    # ---- research ------------------------------------------------------------------------
    def query(self, user: str, question: str) -> dict:
        self.limiter.check(f"{user}:query")
        q = self._question(question)
        st = ResearchWorkflow(self.pipe, self.verifier).run(q, self._owned(user))
        main = st.answers[0]
        self.repo.log_query(user, q, main.status, main.mock_mode,
                            [(v.claim, v.status, v.score, v.chunk_id, v.page) for v in st.verification])
        return {"question": q, "status": main.status, "answer": main.answer,
                "citations": [asdict(c) for c in main.citations], "invalid_citations": main.invalid_citations,
                "uncited_sentences": main.uncited_sentences, "injection_flagged": main.injection_flagged,
                "confidence": main.confidence, "verification": [asdict(v) for v in st.verification],
                "verification_summary": summarize(st.verification), "comparison_markdown": st.comparison_md,
                "report": st.final, "trace": st.trace, "errors": st.errors, "mock_mode": main.mock_mode}

    def chat_stream(self, user: str, question: str) -> Iterator[str]:
        """SSE frames. Streams the completed, validated answer word by word (real token streaming
        needs a provider-level stream method, not implemented)."""
        def frame(event: str, data: object) -> str:
            return f"event: {event}\ndata: {json.dumps(data)}\n\n"
        try:
            r = self.query(user, question)
        except ServiceError as e:
            yield frame("error", {"code": e.code, "message": e.message}); return
        yield frame("evidence", r["citations"])
        for w in r["answer"].split(" "):
            yield frame("token", w + " ")
        yield frame("verification", r["verification"])
        yield frame("done", {"status": r["status"], "mock_mode": r["mock_mode"]})

    def compare(self, user: str, doc_ids: list[str]) -> dict:
        if len(doc_ids) < 2:
            raise ServiceError("invalid_input", "Select at least two documents to compare.")
        for i in doc_ids:
            self._doc(user, i)
        papers = [analyze_paper(self.retriever.chunks_for(i)) for i in doc_ids]
        rows = compare_papers(papers)
        return {"papers": [p.title for p in papers], "rows": rows, "markdown": to_markdown(papers, rows)}

    def verify_claims(self, user: str, claims: list[str]) -> list[dict]:
        self.limiter.check(f"{user}:verify")
        if not claims or len(claims) > 50:
            raise ServiceError("invalid_input", "Provide 1-50 claims.")
        scope, out = self._owned(user), []
        for c in claims:
            c = self._question(c)
            cands = self.retriever.retrieve(c, self.s.candidate_k, scope)
            ev = rerank(self.pipe.reranker, c, cands, self.s.final_k) if cands else []
            v = self.verifier.verify(c, ev)
            out.append(asdict(v))
        self.repo.log_claims(user, [(v["claim"], v["status"], v["score"], v["chunk_id"], v["page"]) for v in out])
        return out

    def graph(self, user: str) -> dict:
        papers = [analyze_paper(self.retriever.chunks_for(i)) for i in sorted(self._owned(user))]
        nodes, edges = build_graph(papers)
        return {"nodes": [{"kind": n.kind, "name": n.name} for n in sorted(nodes, key=lambda n: (n.kind, n.name))],
                "edges": [{"source": e.src.name, "relation": e.rel, "target": e.dst.name, "page": e.page}
                          for e in sorted(edges, key=lambda e: (e.src.name, e.rel, e.dst.name))]}

    def literature_review(self, user: str, title: str, question: str) -> dict:
        self.limiter.check(f"{user}:report")
        md = generate_review(self.pipe, title.strip()[:200] or "Literature Review", self._question(question),
                             self._owned(user))
        return {"markdown": md}

    def dashboard(self, user: str) -> dict:
        owned, st = self._owned(user), self.repo.stats(user)
        return {"documents": len(owned), "chunks": sum(self._docs[i]["chunks"] for i in owned),
                "queries": st["queries"], "claims_verified": st["claims_verified"],
                "verification_counts": st["verification"], "mock_mode": self.s.mock_mode}

    def analyze_document(self, user: str, doc_id: str) -> dict:
        d = self._doc(user, doc_id)
        a = asdict(analyze_paper(self.retriever.chunks_for(doc_id)))
        a["metrics"] = {k: v for k, v in a["metrics"].items()}
        a["not_extracted"] = ["problem", "method", "results", "key_contributions", "task"]  # not in this build
        a["filename"] = d["filename"]
        return a

    def search_external(self, user: str, query: str, limit: int = 10) -> dict:
        self.limiter.check(f"{user}:search")
        q = self._question(query)
        if not self.sources:
            raise ServiceError("unavailable", "No external research sources are configured.")
        records, errors = [], []
        for src in self.sources:
            try:
                records += [asdict(r) for r in src.search(q, max(1, min(limit, 25)))]
            except RuntimeError as exc:
                errors.append(str(exc))
        if not records and errors:
            raise ServiceError("source_unavailable", errors[0])
        return {"results": records, "errors": errors}

    @staticmethod
    def evaluation_report(path: str) -> dict:
        import os
        if not os.path.exists(path):
            return {"evaluated": False}
        with open(path) as f:
            return {"evaluated": True, **json.load(f)}
