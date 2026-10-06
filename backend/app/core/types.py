from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    document_id: str
    document_title: str
    page: int
    section: str
    paragraph: int
    text: str
    authors: tuple[str, ...] = ()
    source: str = ""


@dataclass
class ScoredChunk:
    chunk: Chunk
    score: float
    components: dict[str, float] = field(default_factory=dict)


@dataclass
class Citation:
    id: int
    chunk_id: str
    document_id: str
    document_title: str
    authors: tuple[str, ...]
    page: int
    section: str
    quote: str
    relevance: float


@dataclass
class AnswerResult:
    question: str
    answer: str
    citations: list[Citation]
    invalid_citations: list[int]
    uncited_sentences: list[str]
    injection_flagged: list[str]
    confidence: float
    status: str                      # "answered" | "insufficient_evidence"
    mock_mode: bool
    evidence_chunks: list = field(default_factory=list)   # ScoredChunk list backing [n]
