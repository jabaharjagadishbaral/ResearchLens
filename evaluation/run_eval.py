"""python evaluation/run_eval.py  -> prints metrics, writes evaluation/results/latest.json"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "backend"))
from app.evaluation.metrics import fmt  # noqa: E402
from app.evaluation.runner import run_evaluation  # noqa: E402

rep = run_evaluation(ROOT / "dev_set.json")
(ROOT / "results" / "latest.json").write_text(json.dumps(rep, indent=2))
print(rep["note"])
for group in ("retrieval", "rag", "citations", "verification"):
    for k, v in rep[group].items():
        print(f"{group:13s}{k:30s}{fmt(v) if isinstance(v, (float, type(None))) else v}")
