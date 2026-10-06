import os, tempfile, unittest

from app.core.config import Settings
from app.core.security import ServiceError
from app.db.repo import SQLiteRepository
from app.documents.chunking import PageText
from app.documents.tables import mention_pattern, parse_tables, referenced_object
from app.providers.local import ExtractiveLLM, HashingEmbeddingProvider, LexicalReranker
from app.services.research_service import ResearchService
from app.verification.verifier import LexicalVerifier

DOC = ("Grad-CAM Study\n\n3 Results\n\nFigure 3: Grad-CAM heatmaps overlaid on chest X-rays show activation near the lung opacity.\n\n"
       "As shown in Figure 3, the highlighted regions agree with the radiologist annotation.\n\n"
       "Table 2: Accuracy by model\nModel   Accuracy   AUROC\nDenseNet-121   92.4   0.951\nResNet-50   90.1   0.938\n\n"
       "Figure 30: An unrelated plot of training loss curves over epochs.\n").encode()


def svc(repo=None):
    return ResearchService(Settings(chunk_min_chars=60), HashingEmbeddingProvider(), LexicalReranker(),
                           ExtractiveLLM(), LexicalVerifier(), repo=repo)


class TableTests(unittest.TestCase):
    def test_parse_table_with_caption(self):
        t = parse_tables([PageText(4, DOC.decode())])
        self.assertEqual(len(t), 1)
        self.assertEqual((t[0].table_id, t[0].page, t[0].caption), ("table_2", 4, "Accuracy by model"))
        self.assertEqual(t[0].headers, ["Model", "Accuracy", "AUROC"])
        self.assertEqual(t[0].rows, [["DenseNet-121", "92.4", "0.951"], ["ResNet-50", "90.1", "0.938"]])

    def test_prose_is_not_a_table(self):
        self.assertEqual(parse_tables([PageText(1, "Plain prose line.\nAnother line with words only.\n")]), [])

    def test_reference_parsing(self):
        self.assertEqual(referenced_object("Explain Figure 3."), ("Figure", 3))
        self.assertEqual(referenced_object("what does table 2 show?"), ("Table", 2))
        self.assertEqual(referenced_object("Fig. 12 details"), ("Figure", 12))
        self.assertIsNone(referenced_object("how does grad-cam work"))
        self.assertIsNone(mention_pattern("Figure", 3).search("see Figure 30"))


class FigureQuestionTests(unittest.TestCase):
    def setUp(self):
        self.s = svc()
        self.d = self.s.upload("u", "p.txt", DOC)

    def test_explain_figure_uses_caption_and_not_other_figures(self):
        r = self.s.query("u", "Explain Figure 3.")
        self.assertEqual(r["status"], "answered")
        self.assertIn("heatmaps", r["answer"])
        self.assertNotIn("training loss", r["answer"])
        self.assertTrue(all("Figure 3" in self.s.evidence("u", c["chunk_id"])["text"] for c in r["citations"]))

    def test_table_question(self):
        r = self.s.query("u", "What does Table 2 show?")
        self.assertEqual(r["status"], "answered")
        self.assertIn("Accuracy by model", r["answer"])

    def test_missing_figure_refuses_instead_of_guessing(self):
        r = self.s.query("u", "Explain Figure 7.")
        self.assertEqual(r["status"], "insufficient_evidence")
        self.assertEqual(r["citations"], [])

    def test_scope_and_tables_endpoint(self):
        self.assertEqual(self.s.tables("u", self.d["id"])[0]["table_id"], "table_2")
        with self.assertRaises(ServiceError):
            self.s.tables("other", self.d["id"])
        self.assertEqual(self.s.query("other", "Explain Figure 3.")["status"], "insufficient_evidence")

    def test_tables_persist(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "t.db")
            r1 = SQLiteRepository(path); s1 = svc(r1); doc = s1.upload("u", "p.txt", DOC); r1.close()
            s2 = svc(SQLiteRepository(path))
            self.assertEqual(s2.tables("u", doc["id"])[0]["rows"][0], ["DenseNet-121", "92.4", "0.951"])


if __name__ == "__main__":
    unittest.main()
