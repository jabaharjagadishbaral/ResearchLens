"""Provider interfaces. Swap implementations through configuration."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class EvidenceBlock:
    id: int
    text: str
    title: str = ""
    page: int = 0
    section: str = ""


@dataclass
class GenerationRequest:
    system: str
    user: str
    question: str
    evidence: list[EvidenceBlock] = field(default_factory=list)
    max_tokens: int = 800
    temperature: float = 0.0


class LLMProvider(ABC):
    name: str = "base"
    is_mock: bool = False

    @abstractmethod
    def generate(self, request: GenerationRequest) -> str: ...


class EmbeddingProvider(ABC):
    name: str = "base"
    is_mock: bool = False
    dim: int

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class RerankerProvider(ABC):
    name: str = "base"
    is_mock: bool = False

    @abstractmethod
    def score(self, query: str, passages: list[str]) -> list[float]:
        """Return a relevance score in [0, 1] per passage."""


class VisionProvider(ABC):
    name: str = "base"
    is_mock: bool = False

    @abstractmethod
    def describe(self, image_bytes: bytes, context: str = "") -> str: ...
