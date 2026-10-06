CREATE TABLE doc_tables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    table_id TEXT NOT NULL,
    page INTEGER NOT NULL,
    caption TEXT,
    headers TEXT NOT NULL,
    rows TEXT NOT NULL
);
CREATE INDEX idx_doc_tables_document ON doc_tables(document_id);
