"""Heuristic table + figure/table-reference helpers (text layout based; PDFs lose column layout,
so PyMuPDF find_tables() would be better there and is not wired in)."""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

from app.documents.chunking import PageText

_CAPTION = re.compile(r"^\s*(table)\s+(\d+)\s*[.:]\s*(.*)$", re.I)
_SPLIT = re.compile(r"\t+| {2,}")
_REF = re.compile(r"\b(figure|fig\.?|table)\s*(\d+)\b", re.I)


@dataclass
class Table:
    table_id: str
    page: int
    caption: str | None
    headers: list[str]
    rows: list[list[str]]


def parse_tables(pages: list[PageText]) -> list[Table]:
    out: list[Table] = []
    for pg in pages:
        lines = pg.text.splitlines()
        i, k = 0, 0
        while i < len(lines):
            if len(_SPLIT.split(lines[i].strip())) < 2 or not lines[i].strip():
                i += 1
                continue
            j = i
            while j < len(lines) and lines[j].strip() and len(_SPLIT.split(lines[j].strip())) >= 2:
                j += 1
            block = [_SPLIT.split(ln.strip()) for ln in lines[i:j]]
            n = Counter(len(r) for r in block).most_common(1)[0][0]
            rows = [r for r in block if len(r) == n]
            if len(rows) >= 2 and any(re.search(r"\d", c) for r in rows[1:] for c in r):
                cap = next((lines[x].strip() for x in range(i - 1, max(i - 3, -1), -1) if lines[x].strip()), "")
                m = _CAPTION.match(cap)
                k += 1
                out.append(Table(f"table_{m.group(2)}" if m else f"p{pg.page}_t{k}", pg.page,
                                 m.group(3).strip() if m else None, rows[0], rows[1:]))
            i = j
    return out


def referenced_object(question: str) -> tuple[str, int] | None:
    m = _REF.search(question)
    if not m:
        return None
    return ("Table" if m.group(1).lower() == "table" else "Figure"), int(m.group(2))


def mention_pattern(kind: str, n: int) -> re.Pattern[str]:
    word = r"table" if kind == "Table" else r"(?:figure|fig\.?)"
    return re.compile(rf"\b{word}\s*{n}\b", re.I)
