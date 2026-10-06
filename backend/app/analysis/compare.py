from __future__ import annotations

from app.analysis.paper import NOT_REPORTED, Fact, PaperAnalysis


def _cell(facts: list[Fact] | Fact | None, join: str = "; ") -> str:
    if not facts:
        return NOT_REPORTED
    fs = [facts] if isinstance(facts, Fact) else facts
    return join.join(f"{f.value} (p. {f.page})" for f in fs)


def compare_papers(papers: list[PaperAnalysis]) -> dict[str, list[str]]:
    """Returns {row label: [cell per paper]}. Missing data is always 'Not reported'."""
    rows: dict[str, list[str]] = {
        "Model": [_cell(p.models) for p in papers],
        "Dataset": [_cell(p.datasets) for p in papers],
        "Year": [p.year or NOT_REPORTED for p in papers],
    }
    for m in sorted({m for p in papers for m in p.metrics}):
        rows[m] = [_cell(p.metrics.get(m)) for p in papers]
    rows["Limitations"] = [_cell(p.limitations[:2], " | ") for p in papers]
    return rows


def to_markdown(papers: list[PaperAnalysis], rows: dict[str, list[str]]) -> str:
    head = "| Category | " + " | ".join(p.title for p in papers) + " |"
    sep = "|---|" + "---|" * len(papers)
    body = [f"| {k} | " + " | ".join(v.replace("|", "/") if k != "Limitations" else v.replace("|", "/")
                                    for v in vals) + " |" for k, vals in rows.items()]
    return "\n".join([head, sep, *body])
