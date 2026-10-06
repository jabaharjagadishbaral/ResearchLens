# Evaluation

`python evaluation/run_eval.py` (or `make eval`) writes `evaluation/results/latest.json`; the UI shows "Not evaluated" until it exists.

Metrics: Recall@K, Precision@K, MRR, nDCG@K (document-level, binary relevance); context relevance/recall; faithfulness (share of answer
sentences judged supported/partial by the verifier); citation correctness (cited evidence comes from an expected source) and completeness (share of sentences cited);
answer-point coverage (keyword proxy for answer relevance); abstention accuracy; verifier label accuracy and unsupported-claim recall.

**Caveat.** The dev set (`evaluation/dev_set.json`) is 5 invented documents, 6 questions and 6 labelled claims, run with mock providers.
Scores near 1.0 show the pipeline is wired correctly; they are not evidence of research-grade quality. Replace the dataset with real papers and
real providers before quoting numbers.
