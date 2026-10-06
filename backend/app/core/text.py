from __future__ import annotations

import re

STOPWORDS = frozenset(
    "a an the of in on for to and or is are was were be been by with as at from that this these those "
    "it its into than then which what who how why when where do does did can could should would may "
    "might we our their they them using use used based via about over under between".split()
)
_TOKEN = re.compile(r"[a-z0-9]+")


def _stem(t: str) -> str:
    if len(t) > 4 and t.endswith("ies"):
        return t[:-3] + "y"
    if len(t) > 3 and t.endswith("s") and not t.endswith("ss"):
        return t[:-1]
    return t


def tokenize(text: str, keep_stopwords: bool = False) -> list[str]:
    toks = _TOKEN.findall(text.lower())
    if not keep_stopwords:
        toks = [t for t in toks if t not in STOPWORDS]
    return [_stem(t) for t in toks]


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]
