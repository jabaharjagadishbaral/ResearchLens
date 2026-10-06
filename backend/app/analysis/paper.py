"""Rule-based paper analysis (heuristic MOCK extractor). Every fact keeps page + chunk evidence.
An LLM extractor can replace it behind the same PaperAnalysis shape."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.core.text import split_sentences
from app.core.types import Chunk

NOT_REPORTED = "Not reported"
_MODEL = re.compile(r"\b(ResNet-?\d*|DenseNet-?\d*|VGG-?\d*|ViT|U-Net|EfficientNet-?\w*|Inception\w*|BERT|CLIP|Swin\w*)\b")
_DATASET = re.compile(r"\b(?:on|using|from)\s+(?:the\s+)?([A-Z][A-Za-z0-9-]+)\s+(?:dataset|benchmark)\b")
_METRIC = re.compile(r"\b(accuracy|F1|AUROC|AUC|Dice|precision|recall|sensitivity|specificity)\b"
                     r"(?:\s+score)?(?:\s+of|\s+was|\s*=|:)?\s*(\d+(?:\.\d+)?)\s*(%?)", re.I)


@dataclass
class Fact:
    value: str
    page: int
    chunk_id: str


@dataclass
class PaperAnalysis:
    document_id: str
    title: str
    authors: tuple[str, ...]
    year: str | None = None
    models: list[Fact] = field(default_factory=list)
    datasets: list[Fact] = field(default_factory=list)
    metrics: dict[str, Fact] = field(default_factory=dict)
    limitations: list[Fact] = field(default_factory=list)
    future_work: list[Fact] = field(default_factory=list)


def _add_unique(lst: list[Fact], f: Fact) -> None:
    if all(x.value.lower() != f.value.lower() for x in lst):
        lst.append(f)


def analyze_paper(chunks: list[Chunk], year: str | None = None) -> PaperAnalysis:
    if not chunks:
        raise ValueError("no chunks")
    a = PaperAnalysis(chunks[0].document_id, chunks[0].document_title, chunks[0].authors, year)
    for c in chunks:
        for m in _MODEL.finditer(c.text):
            _add_unique(a.models, Fact(m.group(1), c.page, c.chunk_id))
        for m in _DATASET.finditer(c.text):
            _add_unique(a.datasets, Fact(m.group(1), c.page, c.chunk_id))
        for m in _METRIC.finditer(c.text):
            name = m.group(1).upper() if m.group(1).lower() in ("auroc", "auc", "f1") else m.group(1).title()
            a.metrics.setdefault(name, Fact(m.group(2) + m.group(3), c.page, c.chunk_id))
        for s in split_sentences(c.text):
            low = s.lower()
            if c.section.lower() == "limitations" or "limitation" in low or "not validated" in low:
                _add_unique(a.limitations, Fact(s, c.page, c.chunk_id))
            if "future work" in low or c.section.lower() == "future work":
                _add_unique(a.future_work, Fact(s, c.page, c.chunk_id))
    return a
