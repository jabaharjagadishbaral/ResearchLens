CREATE TABLE users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at REAL NOT NULL
);
CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    owner_id TEXT NOT NULL,
    title TEXT NOT NULL,
    filename TEXT NOT NULL,
    pages INTEGER NOT NULL,
    ocr_pages TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL,
    created_at REAL NOT NULL
);
CREATE INDEX idx_documents_owner ON documents(owner_id);
CREATE TABLE chunks (
    chunk_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    document_title TEXT NOT NULL,
    page INTEGER NOT NULL,
    section TEXT NOT NULL,
    paragraph INTEGER NOT NULL,
    text TEXT NOT NULL,
    authors TEXT NOT NULL DEFAULT '[]',
    source TEXT NOT NULL DEFAULT ''
);
CREATE INDEX idx_chunks_document ON chunks(document_id);
CREATE TABLE queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    question TEXT NOT NULL,
    status TEXT NOT NULL,
    mock_mode INTEGER NOT NULL,
    created_at REAL NOT NULL
);
CREATE INDEX idx_queries_user ON queries(user_id);
CREATE TABLE verifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_id INTEGER REFERENCES queries(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    claim TEXT NOT NULL,
    status TEXT NOT NULL,
    score REAL NOT NULL,
    chunk_id TEXT,
    page INTEGER
);
CREATE INDEX idx_verifications_user ON verifications(user_id);
