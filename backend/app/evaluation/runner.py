"""Runs the dev-set evaluation and returns REAL measured numbers (None => 'Not evaluated')."""
from __future__ import annotations

import json
from pathlib import Path

from app.core.config import Settings
from app.core.text import tokenize
from app.core.types import Chunk, ScoredChunk
from app.documents.chunking import PageText, chunk_document
from app.evaluation import metrics as M
from app.providers.local import ExtractiveLLM, HashingEmbeddingProvider, LexicalReranker
from app.rag.citations import CITATION_RE
from app.rag.pipeline import RAGPipeline
from app.retrieval.hybrid import HybridRetriever, rerank
from app.retrieval.vector_store import InMemoryVectorStore
from app.verification.verifier import (CONTRADICTED, INSUFFICIENT, SUPPORTED, UNSUPPORTED, LexicalVerifier,
                                       verify_answer)

NON_SUPPORT = {UNSUPPORTED, CONTRADICTED, INSUFFICIENT}


def build_pipeline(data: dict, settings: Settings) -> tuple[RAGPipeline, HybridRetriever]:
    r = HybridRetriever(HashingEmbeddingProvider(), InMemoryVectorStore(), settings.hybrid_alpha)
    for d in data["documents"]:
        pages = [PageText(p["page"], p["text"]) for p in d["pages"]]
        r.index(chunk_document(pages, d["id"], d["title"], tuple(d.get("authors", ())),
                               min_chars=settings.chunk_min_chars, max_chars=settings.chunk_max_chars))
    return RAGPipeline(r, LexicalReranker(), ExtractiveLLM(), settings), r


def run_evaluation(dataset_path: str | Path, settings: Settings | None = None, k: int = 5) -> dict:
    s = settings or Settings(chunk_min_chars=60)
    data = json.loads(Path(dataset_path).read_text())
    pipe, retriever = build_pipeline(data, s)
    verifier = LexicalVerifier()
    rec, prec, rr, nd, ctx_rel, ctx_rec, pts, cit_ok, cit_comp, faith = ([] for _ in range(10))
    abstain = []
    for q in data["questions"]:
        gold = set(q["expected_sources"])
        res = pipe.answer(q["question"])
        if not gold:
            abstain.append(1.0 if res.status == "insufficient_evidence" else 0.0)
            continue
        cands = retriever.retrieve(q["question"], s.candidate_k)
        ranked_docs: list[str] = []
        for c in rerank(pipe.reranker, q["question"], cands, len(cands)):
            if c.chunk.document_id not in ranked_docs:
                ranked_docs.append(c.chunk.document_id)
        rec.append(M.recall_at_k(ranked_docs, gold, k)); prec.append(M.precision_at_k(ranked_docs, gold, k))
        rr.append(M.mrr(ranked_docs, gold)); nd.append(M.ndcg_at_k(ranked_docs, gold, k))
        used = [e.chunk.document_id for e in res.evidence_chunks]
        ctx_rel.append(sum(u in gold for u in used) / len(used) if used else 0.0)
        ctx_rec.append(len(gold & set(used)) / len(gold))
        text = res.answer.lower()
        for group in q["expected_answer_points"]:
            pts.append(1.0 if all(any(t in text for t in alts.split("|")) for alts in group) else 0.0)
        vs = verify_answer(res, verifier)
        if vs:
            faith.append(sum(v.status == SUPPORTED or v.status == "PARTIALLY_SUPPORTED" for v in vs) / len(vs))
            cit_comp.append(sum(v.cited for v in vs) / len(vs))
            cited = [v for v in vs if v.cited]
            if cited:
                cit_ok.append(sum(v.chunk_id is not None and v.chunk_id.split(":")[0] in gold for v in cited)
                              / len(cited))
    vtrue = vpred = unsup_hit = unsup_total = 0
    for c in data.get("claims", []):
        ev = ScoredChunk(Chunk("e:p1:c0", "e", "eval", 1, "x", 1, c["evidence_text"]), 1.0)
        pred = verifier.verify(c["claim"], [ev]).status
        vtrue += pred == c["label"]; vpred += 1
        if c["label"] in NON_SUPPORT:
            unsup_total += 1; unsup_hit += pred in NON_SUPPORT
    return {
        "dataset": str(dataset_path), "n_questions": len(data["questions"]), "k": k,
        "mock_mode": True, "note": "Synthetic dev set + offline mock providers; not a research benchmark.",
        "retrieval": {f"recall@{k}": M.mean(rec), f"precision@{k}": M.mean(prec),
                      "mrr": M.mean(rr), f"ndcg@{k}": M.mean(nd)},
        "rag": {"context_relevance": M.mean(ctx_rel), "context_recall": M.mean(ctx_rec),
                "faithfulness": M.mean(faith), "answer_point_coverage": M.mean(pts),
                "abstention_accuracy": M.mean(abstain)},
        "citations": {"correctness": M.mean(cit_ok), "completeness": M.mean(cit_comp)},
        "verification": {"label_accuracy": (vtrue / vpred) if vpred else None,
                         "unsupported_detection_recall": (unsup_hit / unsup_total) if unsup_total else None,
                         "n_claims": vpred},
    }
