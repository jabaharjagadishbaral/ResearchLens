# Document processing

- **Upload validation** (`core/security.py`): extension allow-list (pdf, txt), size limit, `%PDF-` magic bytes, UTF-8/NUL check, sanitised filename.
- **PDF**: PyMuPDF text per page; pages with <50 characters and images are flagged `needs_ocr`. **No OCR engine is wired**; a document with no extractable text is rejected with `ocr_required`.
- **Chunking** (`documents/chunking.py`): heading detection (known section names + numbered headings), blank-line paragraphs, short paragraphs merge forward inside a section *and page*, long ones split on sentences. Chunks never cross pages, so page citations are exact.
- **Tables** (`documents/tables.py`): text-layout heuristic (columns split on tabs or 2+ spaces, needs a numeric data cell); captions `Table N: ...` give `table_N` ids. PDF text loses column layout, so PDF tables are often missed.
- **Not implemented:** figure image extraction, vision analysis, title/author/reference parsing (title = first line; authors are never invented).
