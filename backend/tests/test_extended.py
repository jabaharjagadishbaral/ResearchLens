import json
import unittest
from pathlib import Path

from app.agents.workflow import ResearchWorkflow
from app.analysis.compare import compare_papers
from app.analysis.paper import NOT_REPORTED, analyze_paper
from app.core.config import Settings
from app.evaluation import metrics as M
from app.evaluation.runner import build_pipeline, run_evaluation
from app.knowledge_graph.graph import InMemoryGraphStore, Node, build_graph
from app.rag.citations import CITATION_RE
from app.reports.literature_review import generate_review
from app.research.sources import UnsafeURL, parse_arxiv_atom, validate_url
from app.verification.verifier import (CONTRADICTED, INSUFFICIENT, PARTIAL, SUPPORTED, LexicalVerifier,
                                       summarize, verify_answer)

DEV = Path(__file__).resolve().parents[2] / "evaluation" / "dev_set.json"
S = Settings(chunk_min_chars=60)


def pipe():
    return build_pipeline(json.loads(DEV.read_text()), S)[0]


class MetricTests(unittest.TestCase):
    def test_known_values(self):
        r = ["x", "a", "y", "b"]
        rel = {"a", "b"}
        self.assertEqual(M.recall_at_k(r, rel, 2), 0.5)
        self.assertEqual(M.precision_at_k(r, rel, 2), 0.5)
        self.assertEqual(M.mrr(r, rel), 0.5)
        self.assertAlmostEqual(M.ndcg_at_k(["a", "b"], rel, 2), 1.0)
        self.assertLess(M.ndcg_at_k(r, rel, 4), 1.0)
        self.assertEqual(M.fmt(None), "Not evaluated")

    def test_runner_returns_measured_values(self):
        rep = run_evaluation(DEV, S)
        self.assertEqual(rep["retrieval"]["recall@5"], 1.0)
        self.assertTrue(rep["mock_mode"])


class VerifierTests(unittest.TestCase):
    ev = None

    def v(self, claim, text):
        from app.core.types import Chunk, ScoredChunk
        return LexicalVerifier().verify(claim, [ScoredChunk(Chunk("e:p1:c0", "e", "T", 1, "s", 1, text), 1.0)])

    def test_supported(self):
        t = "DenseNet-121 achieved accuracy of 92.4% on the ChestXray14 dataset."
        self.assertEqual(self.v(t, t).status, SUPPORTED)

    def test_number_mismatch_contradicted(self):
        r = self.v("DenseNet-121 achieved accuracy of 97.8% on the ChestXray14 dataset.",
                   "DenseNet-121 achieved accuracy of 92.4% on the ChestXray14 dataset.")
        self.assertEqual(r.status, CONTRADICTED)

    def test_negation_contradicted(self):
        r = self.v("The saliency maps were validated by radiologists.",
                   "The saliency maps were not validated by radiologists.")
        self.assertEqual(r.status, CONTRADICTED)

    def test_unrelated_is_insufficient(self):
        self.assertEqual(self.v("Quantum annealing speeds up grading.", "ViT reached accuracy of 88.1%.").status,
                         INSUFFICIENT)

    def test_answer_verification_uses_cited_evidence(self):
        p = pipe()
        res = p.answer("What accuracy did DenseNet achieve on ChestXray14?")
        vs = verify_answer(res, LexicalVerifier())
        self.assertTrue(vs and all(x.status in (SUPPORTED, PARTIAL) for x in vs))
        self.assertTrue(all(x.page for x in vs))
        self.assertEqual(summarize(vs)["total"], len(vs))


class AnalysisTests(unittest.TestCase):
    def test_extraction_has_evidence_and_not_reported(self):
        p = pipe()
        a1 = analyze_paper(p.retriever.chunks_for("d1"))
        self.assertEqual(a1.metrics["Accuracy"].value, "92.4%")
        self.assertEqual(a1.metrics["Accuracy"].page, 5)
        self.assertEqual(a1.datasets[0].value, "ChestXray14")
        a4 = analyze_paper(p.retriever.chunks_for("d4"))
        rows = compare_papers([a1, a4])
        self.assertEqual(rows["Accuracy"][1], NOT_REPORTED)   # d4 reports Dice only
        self.assertEqual(rows["Year"], [NOT_REPORTED, NOT_REPORTED])
        self.assertIn("p. 5", rows["Accuracy"][0])

    def test_graph(self):
        a = analyze_paper(pipe().retriever.chunks_for("d1"))
        a.authors = ("Author One",)
        nodes, edges = build_graph([a])
        st = InMemoryGraphStore(); st.write(nodes, edges)
        rels = {e.rel for e in st.neighbors(Node("Paper", a.title))}
        self.assertTrue({"AUTHORED_BY", "USES_MODEL", "USES_DATASET", "EVALUATES_ON"} <= rels)


class WorkflowReportTests(unittest.TestCase):
    def test_workflow_trace_and_compare_skip(self):
        wf = ResearchWorkflow(pipe(), LexicalVerifier())
        st = wf.run("What accuracy did DenseNet achieve on ChestXray14?")
        self.assertEqual(st.trace[:3], ["plan", "search", "retrieve"])
        self.assertNotIn("compare", st.trace)       # single paper -> deterministic skip
        self.assertEqual(st.errors, [])
        self.assertIn("Source evidence", st.final)

    def test_workflow_compare_and_step_cap(self):
        st = ResearchWorkflow(pipe(), LexicalVerifier()).run(
            "Compare Grad-CAM chest X-ray accuracy versus attention rollout retinal accuracy")
        self.assertIn("compare", st.trace) if len(st.analyses) > 1 else None
        capped = ResearchWorkflow(pipe(), LexicalVerifier(), max_steps=2).run("grad-cam chest")
        self.assertIn("step limit reached", capped.errors)

    def test_node_failure_is_contained(self):
        wf = ResearchWorkflow(pipe(), LexicalVerifier())
        wf.nodes["analyze"] = lambda s: (_ for _ in ()).throw(RuntimeError("boom"))
        st = wf.run("What accuracy did DenseNet achieve on ChestXray14?")
        self.assertIn("analyze:failed", st.trace)
        self.assertTrue(st.final)

    def test_review_references_are_real_and_numbers_valid(self):
        md = generate_review(pipe(), "Review", "explainable AI medical imaging")
        refs = {int(n) for n in __import__("re").findall(r"^\[(\d+)\] ", md, __import__("re").M)}
        used = {int(n) for n in CITATION_RE.findall(md.split("## References")[0])}
        self.assertTrue(used and used <= refs)
        for line in md.split("## References")[1].splitlines():
            if line.strip():
                self.assertTrue(any(t in line for t in ("Grad-CAM", "Attention", "Concept", "Counterfactual", "Federated")))
        self.assertIn("Potential research directions", md)


class SourceTests(unittest.TestCase):
    def test_ssrf_guard(self):
        for bad in ("http://export.arxiv.org/x", "https://evil.example.com/x", "https://127.0.0.1/x",
                    "file:///etc/passwd"):
            with self.assertRaises((UnsafeURL, OSError)):
                validate_url(bad, {"export.arxiv.org"})

    def test_parse_atom(self):
        xml = ('<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>http://arxiv.org/abs/0000.0000</id>'
               '<title>A  Test\n Title</title><summary>Sum.</summary><published>2020-01-02T00:00:00Z</published>'
               '<author><name>Writer One</name></author></entry></feed>')
        r = parse_arxiv_atom(xml)[0]
        self.assertEqual((r.title, r.authors, r.published), ("A Test Title", ["Writer One"], "2020-01-02"))


if __name__ == "__main__":
    unittest.main()
