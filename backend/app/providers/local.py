"""Offline development providers (MOCK MODE).

Deterministic and dependency-free so the pipeline and tests run without network access.
They are NOT production quality. Production uses sentence-transformers / BGE / a real LLM
behind the same interfaces (see providers/base.py).
"""
from __future__ import annotations

import math
import zlib

from app.core.text import split_sentences, tokenize
from app.providers.base import EmbeddingProvider, GenerationRequest, LLMProvider, RerankerProvider


class HashingEmbeddingProvider(EmbeddingProvider):
    name = "local-hashing"
    is_mock = True

    def __init__(self, dim: int = 512) -> None:
        self.dim = dim

    def _vec(self, text: str) -> list[float]:
        toks = tokenize(text)
        feats = toks + [f"{a}_{b}" for a, b in zip(toks, toks[1:])]
        v = [0.0] * self.dim
        for f in feats:
            h = zlib.crc32(f.encode())
            v[h % self.dim] += 1.0 if (h >> 16) & 1 else -1.0
        norm = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / norm for x in v]

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vec(t) for t in texts]


class LexicalReranker(RerankerProvider):
    """IDF-weighted query-term coverage over the candidate set, plus a bigram bonus."""

    name = "local-lexical"
    is_mock = True

    def score(self, query: str, passages: list[str]) -> list[float]:
        q = list(dict.fromkeys(tokenize(query)))
        if not q or not passages:
            return [0.0] * len(passages)
        ptoks = [tokenize(p) for p in passages]
        n = len(passages)
        idf = {t: math.log(1 + (n + 1) / (1 + sum(t in set(p) for p in ptoks))) for t in q}
        total = sum(idf.values())
        qbi = set(zip(q, q[1:]))
        out = []
        for toks in ptoks:
            s = set(toks)
            cov = sum(idf[t] for t in q if t in s) / total
            bi = set(zip(toks, toks[1:]))
            bonus = 0.15 * (len(qbi & bi) / len(qbi)) if qbi else 0.0
            out.append(min(1.0, cov * 0.85 + bonus))
        return out


class ExtractiveLLM(LLMProvider):
    """Mock generator: quotes the best-matching sentence from each evidence block with its [n].

    It can only restate evidence, so it cannot invent claims. It exists to exercise the
    retrieval -> citation -> verification path offline.
    """

    name = "local-extractive"
    is_mock = True

    def __init__(self, max_sentences: int = 4) -> None:
        self.max_sentences = max_sentences

    def generate(self, request: GenerationRequest) -> str:
        q = set(tokenize(request.question))
        picks: list[tuple[float, int, str]] = []
        for ev in request.evidence:
            best = (0.0, "")
            for sent in split_sentences(ev.text):
                st = set(tokenize(sent))
                overlap = len(q & st) / (len(q) or 1)
                if overlap > best[0]:
                    best = (overlap, sent)
            if best[0] > 0:
                picks.append((best[0], ev.id, best[1]))
        picks.sort(key=lambda x: -x[0])
        if picks:  # drop weak matches: keep sentences scoring >= half of the best one
            picks = [x for x in picks if x[0] >= 0.5 * picks[0][0]]
        lines = [f"{s.rstrip('.')} [{i}]." for _, i, s in picks[: self.max_sentences]]
        return " ".join(lines)
