"""Vector-store abstraction. Qdrant is the production backend; in-memory is for dev/tests."""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.core.types import Chunk


class VectorStore(ABC):
    @abstractmethod
    def upsert(self, chunks: list[Chunk], vectors: list[list[float]]) -> None: ...

    @abstractmethod
    def search(self, vector: list[float], k: int, document_ids: set[str] | None = None) -> list[tuple[Chunk, float]]: ...


class InMemoryVectorStore(VectorStore):
    def __init__(self) -> None:
        self._items: dict[str, tuple[Chunk, list[float]]] = {}

    def upsert(self, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        for c, v in zip(chunks, vectors, strict=True):
            self._items[c.chunk_id] = (c, v)

    def search(self, vector, k, document_ids=None):
        res = []
        for c, v in self._items.values():
            if document_ids is not None and c.document_id not in document_ids:
                continue
            res.append((c, sum(a * b for a, b in zip(vector, v))))
        res.sort(key=lambda x: -x[1])
        return res[:k]
