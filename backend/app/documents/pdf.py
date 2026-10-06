"""PDF page extraction with per-page OCR detection.

Requires PyMuPDF (`pip install pymupdf`). OCR itself (PaddleOCR / Tesseract) is a separate
step: pages flagged `needs_ocr` should be routed to an OCR provider before chunking.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.documents.chunking import PageText

MIN_TEXT_CHARS_PER_PAGE = 50


def needs_ocr(text: str, has_images: bool) -> bool:
    return len(text.strip()) < MIN_TEXT_CHARS_PER_PAGE and has_images


@dataclass
class ExtractedPage:
    page: PageText
    needs_ocr: bool


def extract_pages(path: str) -> list[ExtractedPage]:
    try:
        import fitz  # PyMuPDF
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise RuntimeError("PyMuPDF is required for PDF extraction: pip install pymupdf") from exc
    out: list[ExtractedPage] = []
    with fitz.open(path) as doc:
        for i, page in enumerate(doc, start=1):
            text = page.get_text("text")
            out.append(ExtractedPage(PageText(i, text), needs_ocr(text, bool(page.get_images()))))
    return out
