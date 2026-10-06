"""Research source adapters + SSRF-safe fetching. Only arXiv is implemented; others are TODO."""
from __future__ import annotations

import ipaddress
import socket
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

ATOM = "{http://www.w3.org/2005/Atom}"


class UnsafeURL(ValueError):
    pass


def validate_url(url: str, allowed_hosts: set[str]) -> str:
    p = urllib.parse.urlparse(url)
    if p.scheme != "https" or not p.hostname:
        raise UnsafeURL("only https URLs are allowed")
    if p.hostname not in allowed_hosts:
        raise UnsafeURL(f"host not allowed: {p.hostname}")
    for info in socket.getaddrinfo(p.hostname, p.port or 443):
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise UnsafeURL("host resolves to a non-public address")
    return url


@dataclass
class PaperRecord:
    source: str
    title: str
    authors: list[str] = field(default_factory=list)
    abstract: str = ""
    url: str = ""
    published: str = ""


class ResearchSource(ABC):
    name = "base"

    @abstractmethod
    def search(self, query: str, limit: int = 10) -> list[PaperRecord]: ...


def parse_arxiv_atom(xml_text: str) -> list[PaperRecord]:
    root = ET.fromstring(xml_text)  # arXiv is a trusted host; use defusedxml for arbitrary XML
    out = []
    for e in root.findall(f"{ATOM}entry"):
        g = lambda t: (e.findtext(f"{ATOM}{t}") or "").strip()  # noqa: E731
        out.append(PaperRecord("arxiv", " ".join(g("title").split()),
                               [a.findtext(f"{ATOM}name") or "" for a in e.findall(f"{ATOM}author")],
                               " ".join(g("summary").split()), g("id"), g("published")[:10]))
    return out


class ArxivSource(ResearchSource):
    name = "arxiv"
    HOSTS = {"export.arxiv.org"}
    MIN_INTERVAL = 3.0  # arXiv API terms: at most one request per 3 seconds

    def __init__(self, timeout: float = 10.0, retries: int = 2) -> None:
        self.timeout, self.retries, self._last = timeout, retries, 0.0

    def search(self, query: str, limit: int = 10) -> list[PaperRecord]:  # pragma: no cover - network
        q = urllib.parse.urlencode({"search_query": f"all:{query}", "max_results": limit})
        url = validate_url(f"https://export.arxiv.org/api/query?{q}", self.HOSTS)
        for attempt in range(self.retries + 1):
            time.sleep(max(0.0, self.MIN_INTERVAL - (time.time() - self._last)))
            self._last = time.time()
            try:
                with urllib.request.urlopen(url, timeout=self.timeout) as r:
                    return parse_arxiv_atom(r.read(2_000_000).decode("utf-8", "replace"))
            except OSError:
                if attempt == self.retries:
                    raise RuntimeError("The research source is temporarily unavailable. "
                                       "You can retry or search your indexed documents.") from None
        return []
