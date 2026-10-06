from __future__ import annotations

import math
from collections import Counter

from app.core.text import tokenize


class BM25Index:
    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1, self.b = k1, b
        self._tf: list[Counter[str]] = []
        self._len: list[int] = []
        self._df: Counter[str] = Counter()
        self._avg = 0.0

    def fit(self, texts: list[str]) -> None:
        toks = [tokenize(t) for t in texts]
        self._tf = [Counter(t) for t in toks]
        self._len = [len(t) for t in toks]
        self._df = Counter(term for tf in self._tf for term in tf)
        self._avg = (sum(self._len) / len(self._len)) if self._len else 0.0

    def search(self, query: str, k: int, allowed: set[int] | None = None) -> list[tuple[int, float]]:
        n = len(self._tf)
        q = tokenize(query)
        scores: list[tuple[int, float]] = []
        for i, tf in enumerate(self._tf):
            if allowed is not None and i not in allowed:
                continue
            s = 0.0
            for term in q:
                f = tf.get(term, 0)
                if not f:
                    continue
                idf = math.log(1 + (n - self._df[term] + 0.5) / (self._df[term] + 0.5))
                denom = f + self.k1 * (1 - self.b + self.b * self._len[i] / (self._avg or 1))
                s += idf * f * (self.k1 + 1) / denom
            if s > 0:
                scores.append((i, s))
        scores.sort(key=lambda x: -x[1])
        return scores[:k]
