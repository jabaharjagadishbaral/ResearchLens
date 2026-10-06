"""Structure-aware chunking: headings -> sections -> paragraphs, page numbers preserved."""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.text import split_sentences
from app.core.types import Chunk

KNOWN_SECTIONS = {
    "abstract", "introduction", "background", "related work", "methods", "method", "methodology",
    "materials and methods", "experiments", "experimental setup", "results", "discussion",
    "limitations", "conclusion", "conclusions", "future work", "references", "acknowledgments",
}
_NUMBERED = re.compile(r"^(\d+(\.\d+)*\.?|[IVX]+\.)\s+[A-Z][^\n]{1,80}$")


@dataclass
class PageText:
    page: int
    text: str


def heading_of(line: str) -> str | None:
    s = line.strip()
    if not s or len(s) > 90:
        return None
    bare = re.sub(r"^(\d+(\.\d+)*\.?|[IVX]+\.)\s+", "", s).rstrip(":").strip().lower()
    if bare in KNOWN_SECTIONS:
        return re.sub(r"^(\d+(\.\d+)*\.?|[IVX]+\.)\s+", "", s).rstrip(":").strip().title()
    if _NUMBERED.match(s) and not s.endswith("."):
        return re.sub(r"^(\d+(\.\d+)*\.?|[IVX]+\.)\s+", "", s).strip()
    return None


def _split_long(text: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    out, cur = [], ""
    for sent in split_sentences(text):
        if cur and len(cur) + len(sent) + 1 > max_chars:
            out.append(cur)
            cur = sent
        else:
            cur = f"{cur} {sent}".strip()
    if cur:
        out.append(cur)
    return out


def chunk_document(
    pages: list[PageText],
    document_id: str,
    title: str,
    authors: tuple[str, ...] = (),
    source: str = "",
    min_chars: int = 200,
    max_chars: int = 1400,
) -> list[Chunk]:
    """Walk pages in order; a heading starts a new section; paragraphs are blank-line delimited.

    Short paragraphs merge forward within the same section and page so a chunk never mixes
    pages (page numbers stay exact for citations). Oversized paragraphs split on sentences.
    """
    chunks: list[Chunk] = []
    section = "Front Matter"
    para_no = 0

    def emit(page: int, sec: str, text: str) -> None:
        nonlocal para_no
        for piece in _split_long(text.strip(), max_chars):
            if not piece:
                continue
            para_no += 1
            chunks.append(Chunk(
                chunk_id=f"{document_id}:p{page}:c{len(chunks)}",
                document_id=document_id, document_title=title, page=page, section=sec,
                paragraph=para_no, text=piece, authors=authors, source=source,
            ))

    for pg in pages:
        buf, buf_sec = "", section
        for block in re.split(r"\n\s*\n", pg.text):
            lines = [ln for ln in block.strip().splitlines() if ln.strip()]
            if not lines:
                continue
            h = heading_of(lines[0])
            if h:
                if buf:
                    emit(pg.page, buf_sec, buf)
                    buf = ""
                section = buf_sec = h
                lines = lines[1:]
                if not lines:
                    continue
            para = " ".join(ln.strip() for ln in lines)
            para = re.sub(r"-\s+(?=[a-z])", "", para)  # de-hyphenate line breaks
            buf = f"{buf} {para}".strip() if buf else para
            buf_sec = section
            if len(buf) >= min_chars:
                emit(pg.page, buf_sec, buf)
                buf = ""
        if buf:
            emit(pg.page, buf_sec, buf)
    return chunks
