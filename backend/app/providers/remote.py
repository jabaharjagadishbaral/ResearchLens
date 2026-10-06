"""Production providers. UNTESTED against real services in my sandbox (no network / packages).
The OpenAI-compatible client's request building and error mapping are unit-tested with a fake transport."""
from __future__ import annotations

import json
import math
import time
import urllib.error
import urllib.request

from app.core.config import Settings
from app.core.security import ServiceError
from app.providers.base import EmbeddingProvider, GenerationRequest, LLMProvider, RerankerProvider
from app.providers.local import ExtractiveLLM, HashingEmbeddingProvider, LexicalReranker


class OpenAICompatibleLLM(LLMProvider):
    """Works with OpenAI, Ollama (/v1), vLLM and other OpenAI-compatible servers."""
    name = "openai-compatible"

    def __init__(self, base_url: str, model: str, api_key: str = "", timeout: float = 60.0, retries: int = 2) -> None:
        if not base_url or not model:
            raise ValueError("LLM_BASE_URL and LLM_MODEL are required for this provider")
        self.url, self.model, self.key = base_url.rstrip("/") + "/chat/completions", model, api_key
        self.timeout, self.retries = timeout, retries

    def build_payload(self, r: GenerationRequest) -> dict:
        return {"model": self.model, "temperature": r.temperature, "max_tokens": r.max_tokens,
                "messages": [{"role": "system", "content": r.system}, {"role": "user", "content": r.user}]}

    def _post(self, payload: dict) -> dict:  # overridable transport
        req = urllib.request.Request(self.url, json.dumps(payload).encode(), {
            "Content-Type": "application/json", **({"Authorization": f"Bearer {self.key}"} if self.key else {})})
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read())

    def generate(self, request: GenerationRequest) -> str:
        payload = self.build_payload(request)
        for attempt in range(self.retries + 1):
            try:
                return self._post(payload)["choices"][0]["message"]["content"]
            except (urllib.error.URLError, TimeoutError, KeyError, IndexError, json.JSONDecodeError):
                if attempt == self.retries:
                    raise ServiceError("llm_unavailable", "The model provider did not respond. Please retry.") from None
                time.sleep(0.5 * 2 ** attempt)
        raise AssertionError("unreachable")


class SentenceTransformerEmbedding(EmbeddingProvider):  # pragma: no cover - needs sentence-transformers
    name = "sentence-transformers"

    def __init__(self, model: str) -> None:
        from sentence_transformers import SentenceTransformer
        self._m = SentenceTransformer(model)
        self.dim = self._m.get_sentence_embedding_dimension()

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self._m.encode(texts, normalize_embeddings=True).tolist()


class CrossEncoderReranker(RerankerProvider):  # pragma: no cover - needs sentence-transformers
    name = "cross-encoder"

    def __init__(self, model: str) -> None:
        from sentence_transformers import CrossEncoder
        self._m = CrossEncoder(model)

    def score(self, query: str, passages: list[str]) -> list[float]:
        return [1 / (1 + math.exp(-float(s))) for s in self._m.predict([(query, p) for p in passages])]


def build_providers(s: Settings) -> tuple[EmbeddingProvider, RerankerProvider, LLMProvider]:
    def pick(kind: str, value: str, options: dict):
        if value not in options:
            raise ValueError(f"unknown {kind} provider: {value!r} (choose from {sorted(options)})")
        return options[value]()
    emb = pick("embedding", s.embedding_provider, {
        "local": HashingEmbeddingProvider, "sentence-transformers": lambda: SentenceTransformerEmbedding(s.embedding_model)})
    rer = pick("reranker", s.reranker_provider, {
        "local": LexicalReranker, "cross-encoder": lambda: CrossEncoderReranker(s.reranker_model)})
    llm = pick("llm", s.llm_provider, {
        "local": ExtractiveLLM, "openai": lambda: OpenAICompatibleLLM(s.llm_base_url, s.llm_model, s.llm_api_key),
        "ollama": lambda: OpenAICompatibleLLM(s.llm_base_url or "http://localhost:11434/v1", s.llm_model)})
    return emb, rer, llm
