from __future__ import annotations

from app.core.types import Chunk, ScoredChunk
from app.providers.base import EmbeddingProvider, RerankerProvider
from app.retrieval.bm25 import BM25Index
from app.retrieval.vector_store import VectorStore


def _minmax(d: dict[str, float]) -> dict[str, float]:
    if not d:
        return {}
    lo, hi = min(d.values()), max(d.values())
    if hi == lo:
        return {k: (1.0 if hi > 0 else 0.0) for k in d}
    return {k: (v - lo) / (hi - lo) for k, v in d.items()}


class HybridRetriever:
    """score = alpha * semantic + (1 - alpha) * keyword, each min-max normalised."""

    def __init__(self, embedder: EmbeddingProvider, store: VectorStore, alpha: float = 0.6) -> None:
        self.embedder, self.store, self.alpha = embedder, store, alpha
        self._chunks: list[Chunk] = []
        self._bm25 = BM25Index()

    def index(self, chunks: list[Chunk]) -> None:
        self._chunks.extend(chunks)
        self.store.upsert(chunks, self.embedder.embed([c.text for c in chunks]))
        self._bm25.fit([c.text for c in self._chunks])

    def all_chunks(self, document_ids: set[str] | None = None) -> list[Chunk]:
        return [c for c in self._chunks if document_ids is None or c.document_id in document_ids]

    def get_chunk(self, chunk_id: str) -> Chunk | None:
        return next((c for c in self._chunks if c.chunk_id == chunk_id), None)

    def chunks_for(self, document_id: str) -> list[Chunk]:
        return [c for c in self._chunks if c.document_id == document_id]

    def retrieve(self, query: str, k: int = 30, document_ids: set[str] | None = None) -> list[ScoredChunk]:
        sem_hits = self.store.search(self.embedder.embed([query])[0], k, document_ids)
        allowed = None if document_ids is None else {
            i for i, c in enumerate(self._chunks) if c.document_id in document_ids}
        kw_hits = [(self._chunks[i], s) for i, s in self._bm25.search(query, k, allowed)]
        sem = _minmax({c.chunk_id: s for c, s in sem_hits})
        kw = _minmax({c.chunk_id: s for c, s in kw_hits})
        by_id = {c.chunk_id: c for c, _ in sem_hits + kw_hits}
        out = []
        for cid, c in by_id.items():
            s, w = sem.get(cid, 0.0), kw.get(cid, 0.0)
            out.append(ScoredChunk(c, self.alpha * s + (1 - self.alpha) * w,
                                   {"semantic": s, "keyword": w}))
        out.sort(key=lambda x: -x.score)
        return out[:k]


def rerank(reranker: RerankerProvider, query: str, candidates: list[ScoredChunk], top_k: int) -> list[ScoredChunk]:
    scores = reranker.score(query, [c.chunk.text for c in candidates])
    ranked = [ScoredChunk(c.chunk, s, {**c.components, "hybrid": c.score, "rerank": s})
              for c, s in zip(candidates, scores, strict=True)]
    ranked.sort(key=lambda x: -x.score)
    return ranked[:top_k]
