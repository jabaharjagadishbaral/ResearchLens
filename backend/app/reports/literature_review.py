"""Literature-review generator. Every factual sentence is cited; references list only cited sources."""
from __future__ import annotations

import re

from app.analysis.paper import analyze_paper
from app.rag.citations import CITATION_RE
from app.rag.pipeline import RAGPipeline

SECTIONS = [
    ("Background", "background explainability medical imaging"),
    ("Research Methods and Major Approaches", "method approach explain predictions"),
    ("Comparative Analysis", "results accuracy dataset performance"),
    ("Limitations", "limitations not validated"),
]


def generate_review(pipe: RAGPipeline, title: str, question: str, document_ids: set[str] | None = None) -> str:
    refs: dict[str, int] = {}
    info: dict[str, tuple[str, int, str, tuple[str, ...]]] = {}
    out = [f"# {title}", f"**Research question:** {question}", "",
           "_Generated in mock mode: sentences are extracted from indexed sources, not LLM-written._", ""]
    docs: list[str] = []

    def section(name: str, query: str) -> None:
        res = pipe.answer(f"{query} {question}", document_ids)
        out.append(f"## {name}")
        if res.status != "answered":
            out.extend(["I could not find sufficient evidence in the indexed sources to support this claim.", ""])
            return

        def remap(m: re.Match[str]) -> str:
            c = res.citations[int(m.group(1)) - 1]
            n = refs.setdefault(c.chunk_id, len(refs) + 1)
            info[c.chunk_id] = (c.document_title, c.page, c.section, c.authors)
            if c.document_id not in docs:
                docs.append(c.document_id)
            return f"[{n}]"
        out.extend([CITATION_RE.sub(remap, res.answer), ""])

    for name, q in SECTIONS:
        section(name, q)
    out.append("## Research Gaps")
    out.append("**Evidence-backed observations (limitations reported by the sources):**")
    found = False
    for d in docs:
        a = analyze_paper(pipe.retriever.chunks_for(d))
        for f in a.limitations[:2]:
            found = True
            n = refs.setdefault(f.chunk_id, len(refs) + 1)
            ch = next(c for c in pipe.retriever.chunks_for(d) if c.chunk_id == f.chunk_id)
            info[f.chunk_id] = (ch.document_title, ch.page, ch.section, ch.authors)
            out.append(f"- {f.value} [{n}]")
    if not found:
        out.append("- Not reported in the available sources.")
    out.append("\n**Potential research directions (stated by the authors; not verified findings):**")
    fw = [(f, d) for d in docs for f in analyze_paper(pipe.retriever.chunks_for(d)).future_work]
    for f, d in fw:
        n = refs.setdefault(f.chunk_id, len(refs) + 1)
        ch = next(c for c in pipe.retriever.chunks_for(d) if c.chunk_id == f.chunk_id)
        info[f.chunk_id] = (ch.document_title, ch.page, ch.section, ch.authors)
        out.append(f"- {f.value} [{n}]")
    if not fw:
        out.append("- Not reported in the available sources.")
    out += ["", "## References"]
    for cid, n in sorted(refs.items(), key=lambda kv: kv[1]):
        t, pg, sec, au = info[cid]
        out.append(f"[{n}] {', '.join(au) + '. ' if au else ''}{t}. Page {pg}, section: {sec}.")
    return "\n".join(out) + "\n"
