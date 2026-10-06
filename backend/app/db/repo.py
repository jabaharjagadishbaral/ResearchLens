"""Relational persistence (stdlib sqlite3) with versioned SQL migrations.

Schema/SQL is kept portable so a Postgres repository (SQLAlchemy) can mirror this interface.
Rows are plain tables (no JSON blobs for relational data); only author lists / OCR page lists are JSON text.
"""
from __future__ import annotations

import json
import sqlite3
import threading
import time
from pathlib import Path

from app.core.types import Chunk

MIGRATIONS = Path(__file__).parent / "migrations"


def migrate(conn: sqlite3.Connection) -> list[str]:
    """Apply unapplied migrations in order, each in its own transaction. Returns applied versions."""
    conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at REAL)")
    done = {r[0] for r in conn.execute("SELECT version FROM schema_migrations")}
    applied = []
    for f in sorted(MIGRATIONS.glob("*.sql")):
        if f.stem in done:
            continue
        conn.execute("BEGIN")
        try:
            for stmt in f.read_text().split(";"):
                if stmt.strip():
                    conn.execute(stmt)
            conn.execute("INSERT INTO schema_migrations VALUES (?, ?)", (f.stem, time.time()))
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
        applied.append(f.stem)
    return applied


class SQLiteRepository:
    def __init__(self, path: str = ":memory:") -> None:
        self._lock = threading.RLock()
        self.conn = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        self.conn.execute("PRAGMA foreign_keys = ON")
        migrate(self.conn)

    def _tx(self):
        repo = self

        class Tx:
            def __enter__(self_):
                repo._lock.acquire(); repo.conn.execute("BEGIN"); return repo.conn

            def __exit__(self_, et, *_):
                try:
                    repo.conn.execute("ROLLBACK" if et else "COMMIT")
                finally:
                    repo._lock.release()
        return Tx()

    # users
    def add_user(self, uid: str, email: str, password_hash: str) -> None:
        try:
            with self._tx() as c:
                c.execute("INSERT INTO users VALUES (?,?,?,?)", (uid, email, password_hash, time.time()))
        except sqlite3.IntegrityError:
            raise ValueError("email already registered") from None

    def get_user(self, email: str) -> tuple[str, str] | None:
        with self._lock:
            return self.conn.execute("SELECT id, password_hash FROM users WHERE email=?", (email,)).fetchone()

    # documents + chunks
    def add_document(self, doc: dict, chunks: list[Chunk], tables: list | None = None) -> None:
        with self._tx() as c:
            c.execute("INSERT INTO documents VALUES (?,?,?,?,?,?,?,?)",
                      (doc["id"], doc["owner"], doc["title"], doc["filename"], doc["pages"],
                       json.dumps(doc["ocr_pages"]), doc["status"], time.time()))
            c.executemany("INSERT INTO chunks VALUES (?,?,?,?,?,?,?,?,?)", [
                (k.chunk_id, k.document_id, k.document_title, k.page, k.section, k.paragraph, k.text,
                 json.dumps(list(k.authors)), k.source) for k in chunks])
            c.executemany("INSERT INTO doc_tables (document_id, table_id, page, caption, headers, rows) VALUES (?,?,?,?,?,?)",
                          [(doc["id"], t.table_id, t.page, t.caption, json.dumps(t.headers), json.dumps(t.rows))
                           for t in tables or []])

    def documents(self) -> list[dict]:
        with self._lock:
            rows = self.conn.execute(
                "SELECT d.id, d.owner_id, d.title, d.filename, d.pages, d.ocr_pages, d.status, "
                "(SELECT COUNT(*) FROM chunks c WHERE c.document_id = d.id) FROM documents d ORDER BY d.created_at").fetchall()
        return [{"id": r[0], "owner": r[1], "title": r[2], "filename": r[3], "pages": r[4],
                 "ocr_pages": json.loads(r[5]), "status": r[6], "chunks": r[7]} for r in rows]

    def tables(self, document_id: str) -> list[dict]:
        with self._lock:
            rows = self.conn.execute("SELECT table_id, page, caption, headers, rows FROM doc_tables "
                                     "WHERE document_id=? ORDER BY id", (document_id,)).fetchall()
        return [{"table_id": r[0], "page": r[1], "caption": r[2], "headers": json.loads(r[3]), "rows": json.loads(r[4])} for r in rows]

    def chunks(self) -> list[Chunk]:
        with self._lock:
            rows = self.conn.execute(
                "SELECT chunk_id, document_id, document_title, page, section, paragraph, text, authors, source "
                "FROM chunks ORDER BY rowid").fetchall()
        return [Chunk(r[0], r[1], r[2], r[3], r[4], r[5], r[6], tuple(json.loads(r[7])), r[8]) for r in rows]

    # activity
    def log_query(self, user: str, question: str, status: str, mock: bool,
                  verifs: list[tuple[str, str, float, str | None, int | None]]) -> None:
        with self._tx() as c:
            qid = c.execute("INSERT INTO queries (user_id, question, status, mock_mode, created_at) VALUES (?,?,?,?,?)",
                            (user, question, status, int(mock), time.time())).lastrowid
            c.executemany("INSERT INTO verifications (query_id, user_id, kind, claim, status, score, chunk_id, page) "
                          "VALUES (?,?,?,?,?,?,?,?)", [(qid, user, "answer", *v) for v in verifs])

    def log_claims(self, user: str, verifs: list[tuple[str, str, float, str | None, int | None]]) -> None:
        with self._tx() as c:
            c.executemany("INSERT INTO verifications (query_id, user_id, kind, claim, status, score, chunk_id, page) "
                          "VALUES (NULL,?,?,?,?,?,?,?)", [(user, "claim", *v) for v in verifs])

    def stats(self, user: str) -> dict:
        with self._lock:
            q = self.conn.execute("SELECT COUNT(*) FROM queries WHERE user_id=?", (user,)).fetchone()[0]
            by = dict(self.conn.execute(
                "SELECT status, COUNT(*) FROM verifications WHERE user_id=? GROUP BY status", (user,)).fetchall())
            cl = self.conn.execute("SELECT COUNT(*) FROM verifications WHERE user_id=? AND kind='claim'",
                                   (user,)).fetchone()[0]
        return {"queries": q, "verification": by, "claims_verified": cl}

    def close(self) -> None:
        self.conn.close()
