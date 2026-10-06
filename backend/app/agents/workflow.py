"""Controlled research workflow: explicit nodes, static transition table, hard step cap.

Nodes are pure functions of ResearchState so they map one-to-one onto a LangGraph StateGraph
(langgraph is not installed in my sandbox, so this runner is dependency-free and tested).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable

from app.analysis.compare import compare_papers, to_markdown
from app.analysis.paper import PaperAnalysis, analyze_paper
from app.core.types import AnswerResult
from app.rag.citations import CITATION_RE
from app.rag.pipeline import RAGPipeline
from app.research.sources import ResearchSource
from app.verification.verifier import ClaimVerification, ClaimVerifier, summarize, verify_answer


@dataclass
class Task:
    kind: str
    query: str


@dataclass
class ResearchState:
    question: str
    scope: set[str] | None = None   # document ids the caller may read
    tasks: list[Task] = field(default_factory=list)
    external: list = field(default_factory=list)
    answers: list[AnswerResult] = field(default_factory=list)
    analyses: list[PaperAnalysis] = field(default_factory=list)
    comparison_md: str = ""
    verification: list[ClaimVerification] = field(default_factory=list)
    final: str = ""
    trace: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class ResearchWorkflow:
    ORDER = ["plan", "search", "retrieve", "analyze", "compare", "verify", "synthesize"]

    def __init__(self, pipeline: RAGPipeline, verifier: ClaimVerifier,
                 sources: list[ResearchSource] | None = None, max_steps: int = 12) -> None:
        self.p, self.v, self.sources, self.max_steps = pipeline, verifier, sources or [], max_steps
        self.nodes: dict[str, Callable[[ResearchState], None]] = {n: getattr(self, f"_{n}") for n in self.ORDER}

    def run(self, question: str, document_ids: set[str] | None = None) -> ResearchState:
        st = ResearchState(question, scope=document_ids)
        node: str | None = self.ORDER[0]
        steps = 0
        while node and steps < self.max_steps:
            steps += 1
            try:
                self.nodes[node](st)
                st.trace.append(node)
            except Exception as exc:  # node failure never crashes the run; no stack trace to users
                st.errors.append(f"{node}: {type(exc).__name__}")
                st.trace.append(f"{node}:failed")
            node = self._next(node, st)
        if node:
            st.errors.append("step limit reached")
        return st

    def _next(self, node: str, st: ResearchState) -> str | None:
        i = self.ORDER.index(node)
        nxt = self.ORDER[i + 1] if i + 1 < len(self.ORDER) else None
        if nxt == "compare" and len(st.analyses) < 2:
            nxt = "verify"  # deterministic skip: nothing to compare
        return nxt

    def _plan(self, st: ResearchState) -> None:
        q = st.question
        st.tasks = [Task("answer", q)]
        if re.search(r"\b(compare|versus|vs\.?|difference)\b", q, re.I):
            st.tasks.append(Task("compare", f"methods and results: {q}"))
        if re.search(r"\b(limitation|gap|future)\b", q, re.I):
            st.tasks.append(Task("gaps", f"limitations and future work: {q}"))

    def _search(self, st: ResearchState) -> None:
        for s in self.sources:
            try:
                st.external += s.search(st.question, 5)
            except RuntimeError as exc:
                st.errors.append(str(exc))

    def _retrieve(self, st: ResearchState) -> None:
        st.answers = [self.p.answer(t.query, st.scope) for t in st.tasks]

    def _analyze(self, st: ResearchState) -> None:
        ids = list(dict.fromkeys(
            a.citations[int(n) - 1].document_id for a in st.answers
            for n in CITATION_RE.findall(a.answer) if 1 <= int(n) <= len(a.citations)))
        st.analyses = [analyze_paper(self.p.retriever.chunks_for(i)) for i in ids]

    def _compare(self, st: ResearchState) -> None:
        st.comparison_md = to_markdown(st.analyses, compare_papers(st.analyses))

    def _verify(self, st: ResearchState) -> None:
        for a in st.answers:
            st.verification += verify_answer(a, self.v)

    def _synthesize(self, st: ResearchState) -> None:
        main = st.answers[0]
        parts = [f"## Source evidence (retrieved, cited)\n{main.answer}"]
        if st.comparison_md:
            parts.append(f"## Comparison (extracted from sources; gaps shown as 'Not reported')\n{st.comparison_md}")
        s = summarize(st.verification)
        if s["total"]:
            parts.append(f"## Verification\n{s['SUPPORTED']} supported, {s['PARTIALLY_SUPPORTED']} partial, "
                         f"{s['UNSUPPORTED']} unsupported, {s['CONTRADICTED']} contradicted, "
                         f"{s['INSUFFICIENT_EVIDENCE']} insufficient (mock lexical verifier).")
        parts.append("## Model inference\nNone generated: this build has no LLM synthesis step in mock mode.")
        st.final = "\n\n".join(parts)
