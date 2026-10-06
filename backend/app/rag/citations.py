from __future__ import annotations

import re

from app.core.text import split_sentences

CITATION_RE = re.compile(r"\[(\d+)\]")
_WITH_SPACE = re.compile(r"(\s*)\[(\d+)\]")


def validate_citations(answer: str, evidence_count: int) -> tuple[str, list[int], list[str]]:
    """Strip citations that do not map to real evidence; list sentences lacking any citation.

    Returns (cleaned_answer, invalid_ids, uncited_sentences).
    """
    invalid: list[int] = []

    def fix(m: re.Match[str]) -> str:
        n = int(m.group(2))
        if 1 <= n <= evidence_count:
            return m.group(0)
        invalid.append(n)
        return ""

    cleaned = re.sub(r"\s+", " ", _WITH_SPACE.sub(fix, answer)).strip()
    uncited = [s for s in split_sentences(cleaned) if not CITATION_RE.search(s)]
    return cleaned, invalid, uncited
