"""Claim verification. LexicalVerifier is the offline MOCK; an LLM/NLI verifier implements ClaimVerifier."""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.core.text import split_sentences, tokenize
from app.core.types import AnswerResult, ScoredChunk
from app.rag.citations import CITATION_RE

SUPPORTED, PARTIAL, UNSUPPORTED = "SUPPORTED", "PARTIALLY_SUPPORTED", "UNSUPPORTED"
CONTRADICTED, INSUFFICIENT = "CONTRADICTED", "INSUFFICIENT_EVIDENCE"
LABELS = (SUPPORTED, PARTIAL, UNSUPPORTED, CONTRADICTED, INSUFFICIENT)

_NEG = re.compile(r"\b(not|no|never|cannot|without|fails?|failed|unable)\b|n't", re.I)
_NUM = re.compile(r"(?<![\w.-])\d+(?:\.\d+)?(?![\w-])")  # standalone numbers only (not DenseNet-121)


@dataclass
class ClaimVerification:
    claim: str
    status: str
    score: float
    chunk_id: str | None = None
    document_title: str | None = None
    page: int | None = None
    evidence_sentence: str | None = None
    cited: bool = True


class ClaimVerifier(ABC):
    is_mock = False

    @abstractmethod
    def verify(self, claim: str, evidence: list[ScoredChunk]) -> ClaimVerification: ...


def _windows(text: str) -> list[str]:
    s = split_sentences(text)
    return s + [f"{a} {b}" for a, b in zip(s, s[1:])]


class LexicalVerifier(ClaimVerifier):
    is_mock = True

    def verify(self, claim: str, evidence: list[ScoredChunk]) -> ClaimVerification:
        clean = CITATION_RE.sub("", claim).strip()
        ctoks = set(tokenize(clean))
        best, best_cov, best_ev = None, 0.0, None
        for ev in evidence:
            for w in _windows(ev.chunk.text):
                cov = len(ctoks & set(tokenize(w))) / (len(ctoks) or 1)
                if cov > best_cov:
                    best, best_cov, best_ev = w, cov, ev
        if best is None or best_ev is None:
            return ClaimVerification(clean, INSUFFICIENT, 0.0)
        status = SUPPORTED if best_cov >= 0.75 else PARTIAL if best_cov >= 0.4 else \
            UNSUPPORTED if best_cov >= 0.15 else INSUFFICIENT
        cn, en = set(_NUM.findall(clean)), set(_NUM.findall(best))
        if cn and best_cov >= 0.5:
            if not (cn & en) and en:
                status = CONTRADICTED
            elif cn - en and status == SUPPORTED:
                status = PARTIAL
        if best_cov >= 0.6 and bool(_NEG.search(clean)) != bool(_NEG.search(best)):
            status = CONTRADICTED
        if status == INSUFFICIENT:
            return ClaimVerification(clean, status, round(best_cov, 3))
        c = best_ev.chunk
        return ClaimVerification(clean, status, round(best_cov, 3), c.chunk_id, c.document_title, c.page, best)


def verify_answer(result: AnswerResult, verifier: ClaimVerifier) -> list[ClaimVerification]:
    """Verify each answer sentence against the evidence it cites (or all evidence if uncited)."""
    if result.status != "answered":
        return []
    out = []
    for sent in split_sentences(result.answer):
        ids = [int(n) for n in CITATION_RE.findall(sent) if 1 <= int(n) <= len(result.evidence_chunks)]
        pool = [result.evidence_chunks[i - 1] for i in ids] or result.evidence_chunks
        v = verifier.verify(sent, pool)
        v.cited = bool(ids)
        out.append(v)
    return out


def summarize(vs: list[ClaimVerification]) -> dict[str, float | int | None]:
    n = len(vs)
    d: dict[str, float | int | None] = {l: sum(v.status == l for v in vs) for l in LABELS}
    d["total"] = n
    d["supported_rate"] = (sum(v.status in (SUPPORTED, PARTIAL) for v in vs) / n) if n else None
    return d
