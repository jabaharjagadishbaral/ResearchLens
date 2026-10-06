"""Prompt-injection screening. Document text is DATA, never instructions."""
from __future__ import annotations

import re

_PATTERNS = [
    r"ignore (all |any )?(the )?(previous|prior|above) (instructions|prompts?)",
    r"disregard (all |any )?(the )?(previous|prior|above)",
    r"you are now\b",
    r"\bsystem prompt\b",
    r"reveal (your|the) (instructions|prompt)",
    r"do not (cite|mention) (any )?sources",
    r"new instructions\s*:",
]
_RE = re.compile("|".join(_PATTERNS), re.I)


def looks_like_injection(text: str) -> bool:
    return bool(_RE.search(text))


def escape_for_prompt(text: str) -> str:
    """Prevent evidence from closing our delimiter tags."""
    return text.replace("<", "&lt;").replace(">", "&gt;")
