import os
import sqlite3
import tempfile
import unittest

from app.core.config import Settings
from app.core.security import ServiceError
from app.db.repo import SQLiteRepository, migrate
from app.providers.local import ExtractiveLLM, HashingEmbeddingProvider, LexicalReranker
from app.services.auth import AuthService
from app.services.research_service import ResearchService
from app.verification.verifier import LexicalVerifier

PAPER = ("Grad-CAM for Chest Radiographs\n\n3 Methodology\n\nGrad-CAM weights feature maps by pooled gradients "
         "to localize regions that drive a CNN prediction on chest X-ray images.\n\n4 Results\n\n"
         "DenseNet-121 achieved accuracy of 92.4% on the ChestXray14 dataset.").encode()


def make(path):
    repo = SQLiteRepository(path)
    return repo, ResearchService(Settings(chunk_min_chars=60), HashingEmbeddingProvider(), LexicalReranker(),
                                 ExtractiveLLM(), LexicalVerifier(), repo=repo)


class PersistenceTests(unittest.TestCase):
    def test_state_survives_restart(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "t.db")
            repo, s1 = make(path)
            auth = AuthService("x" * 20, repo)
            uid = auth.register("a@b.co", "longenoughpw")
            doc = s1.upload(uid, "p.txt", PAPER)
            r1 = s1.query(uid, "What accuracy did DenseNet achieve on ChestXray14?")
            s1.verify_claims(uid, ["DenseNet-121 achieved accuracy of 92.4% on the ChestXray14 dataset."])
            before = s1.dashboard(uid)
            repo.close()

            repo2, s2 = make(path)                      # simulated process restart
            self.assertEqual(s2.list_documents(uid)[0]["id"], doc["id"])
            r2 = s2.query(uid, "What accuracy did DenseNet achieve on ChestXray14?")
            self.assertEqual(r2["answer"], r1["answer"])           # index rebuilt from stored chunks
            self.assertEqual(s2.evidence(uid, r2["citations"][0]["chunk_id"])["page"], 1)
            self.assertTrue(AuthService("x" * 20, repo2).authenticate(AuthService("x" * 20, repo2).login(
                "a@b.co", "longenoughpw")))
            after = s2.dashboard(uid)
            self.assertEqual(after["documents"], 1)
            self.assertEqual(after["queries"], before["queries"] + 1)
            self.assertEqual(after["claims_verified"], 1)
            self.assertEqual(s2.dashboard("someone-else")["queries"], 0)
            repo2.close()

    def test_duplicate_email_rejected_across_instances(self):
        repo = SQLiteRepository()
        AuthService("x" * 20, repo).register("a@b.co", "longenoughpw")
        with self.assertRaises(ServiceError):
            AuthService("x" * 20, repo).register("A@B.co", "longenoughpw")

    def test_migrations_idempotent_and_versioned(self):
        repo = SQLiteRepository()
        self.assertEqual(migrate(repo.conn), [])          # second run applies nothing
        v = [r[0] for r in repo.conn.execute("SELECT version FROM schema_migrations")]
        self.assertEqual(v, sorted(v))
        self.assertEqual(v[:2], ["001_init", "002_tables"])

    def test_failed_migration_rolls_back(self):
        import app.db.repo as m
        from pathlib import Path
        with tempfile.TemporaryDirectory() as d:
            Path(d, "001_a.sql").write_text("CREATE TABLE a (x INTEGER);")
            Path(d, "002_bad.sql").write_text("CREATE TABLE b (x INTEGER); CREATE TABLE a (y INTEGER);")
            old, m.MIGRATIONS = m.MIGRATIONS, Path(d)
            try:
                conn = sqlite3.connect(":memory:", isolation_level=None)
                with self.assertRaises(sqlite3.OperationalError):
                    migrate(conn)
                tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                self.assertIn("a", tables)
                self.assertNotIn("b", tables)             # 002 rolled back atomically
            finally:
                m.MIGRATIONS = old

    def test_cascade_delete_chunks(self):
        repo, s = make(":memory:")
        d = s.upload("u", "p.txt", PAPER)
        repo.conn.execute("DELETE FROM documents WHERE id=?", (d["id"],))
        self.assertEqual(repo.conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
