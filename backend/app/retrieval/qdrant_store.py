"""Qdrant VectorStore adapter. UNTESTED (qdrant-client not installable here); written against qdrant-client>=1.10."""
from __future__ import annotations

import uuid
from dataclasses import asdict

from app.core.types import Chunk
from app.retrieval.vector_store import VectorStore


class QdrantVectorStore(VectorStore):  # pragma: no cover
    def __init__(self, url: str, api_key: str | None, dim: int, collection: str = "chunks") -> None:
        from qdrant_client import QdrantClient, models
        self._m, self.col = models, collection
        self.client = QdrantClient(url=url, api_key=api_key or None, timeout=10)
        if not self.client.collection_exists(collection):
            self.client.create_collection(collection, vectors_config=models.VectorParams(
                size=dim, distance=models.Distance.COSINE))
            self.client.create_payload_index(collection, "document_id", models.PayloadSchemaType.KEYWORD)

    def upsert(self, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        pts = [self._m.PointStruct(id=str(uuid.uuid5(uuid.NAMESPACE_URL, c.chunk_id)), vector=v,
                                   payload={**asdict(c), "authors": list(c.authors)})
               for c, v in zip(chunks, vectors, strict=True)]
        self.client.upsert(self.col, points=pts)

    def search(self, vector, k, document_ids=None):
        flt = None if document_ids is None else self._m.Filter(must=[self._m.FieldCondition(
            key="document_id", match=self._m.MatchAny(any=sorted(document_ids)))])
        res = self.client.query_points(self.col, query=vector, limit=k, query_filter=flt, with_payload=True).points
        return [(Chunk(**{**p.payload, "authors": tuple(p.payload.get("authors", ()))}), p.score) for p in res]
