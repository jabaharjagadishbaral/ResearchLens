"""Environment-driven configuration. No secrets are hard-coded."""
from __future__ import annotations

import os
from dataclasses import dataclass


def _f(name: str, default: float) -> float:
    return float(os.getenv(name, default))


def _i(name: str, default: int) -> int:
    return int(os.getenv(name, default))


@dataclass(frozen=True)
class Settings:
    llm_provider: str = "local"          # "local" is the offline development provider
    embedding_provider: str = "local"
    reranker_provider: str = "local"
    hybrid_alpha: float = 0.6            # weight of semantic score; keyword gets 1 - alpha
    candidate_k: int = 30                # hybrid retrieval depth
    final_k: int = 8                     # evidence chunks passed to the LLM
    min_rerank_score: float = 0.15       # context-relevance floor; below -> insufficient evidence
    llm_base_url: str = ""
    llm_model: str = ""
    llm_api_key: str = ""
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    reranker_model: str = "BAAI/reranker-base"
    max_upload_bytes: int = 25 * 1024 * 1024
    rate_limit_per_minute: int = 30
    max_context_chars: int = 12000
    chunk_min_chars: int = 200
    chunk_max_chars: int = 1400

    @classmethod
    def from_env(cls) -> "Settings":
        d = cls()
        return cls(
            llm_provider=os.getenv("LLM_PROVIDER", d.llm_provider),
            embedding_provider=os.getenv("EMBEDDING_PROVIDER", d.embedding_provider),
            reranker_provider=os.getenv("RERANKER_PROVIDER", d.reranker_provider),
            hybrid_alpha=_f("HYBRID_ALPHA", d.hybrid_alpha),
            candidate_k=_i("CANDIDATE_K", d.candidate_k),
            final_k=_i("FINAL_K", d.final_k),
            min_rerank_score=_f("MIN_RERANK_SCORE", d.min_rerank_score),
            llm_base_url=os.getenv("LLM_BASE_URL", d.llm_base_url),
            llm_model=os.getenv("LLM_MODEL", d.llm_model),
            llm_api_key=os.getenv("LLM_API_KEY", d.llm_api_key),
            embedding_model=os.getenv("EMBEDDING_MODEL", d.embedding_model),
            reranker_model=os.getenv("RERANKER_MODEL", d.reranker_model),
            max_upload_bytes=_i("MAX_UPLOAD_BYTES", d.max_upload_bytes),
            rate_limit_per_minute=_i("RATE_LIMIT_PER_MINUTE", d.rate_limit_per_minute),
            max_context_chars=_i("MAX_CONTEXT_CHARS", d.max_context_chars),
            chunk_min_chars=_i("CHUNK_MIN_CHARS", d.chunk_min_chars),
            chunk_max_chars=_i("CHUNK_MAX_CHARS", d.chunk_max_chars),
        )

    @property
    def mock_mode(self) -> bool:
        """True when any stage uses an offline development provider."""
        return "local" in (self.llm_provider, self.embedding_provider, self.reranker_provider)
