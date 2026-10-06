# RAG pipeline

1. **Retrieve** (`retrieval/hybrid.py`): top-30 by `alpha*semantic + (1-alpha)*keyword`, each min-max normalised (default alpha 0.6, env `HYBRID_ALPHA`).
2. **Rerank** (`rerank`): reranker scores in [0,1]; keep top 8 (`FINAL_K`).
3. **Filter**: drop chunks below `MIN_RERANK_SCORE` (0.15) and stop at `MAX_CONTEXT_CHARS`. Nothing left means the answer is exactly
   *"I could not find sufficient evidence in the indexed sources to support this claim."*
4. **Quarantine**: chunks matching prompt-injection patterns are excluded before the LLM sees them and reported in `injection_flagged`.
5. **Generate**: system / user / evidence are separated; evidence is escaped and wrapped in `<evidence id=n>` tags and labelled as data.
6. **Validate citations**: any `[n]` outside the real evidence range is stripped and reported; uncited sentences are listed.

**Figure/table questions** ("Explain Figure 3"): evidence is restricted to chunks that literally mention that figure/table
(word-boundary match, so Figure 30 never matches Figure 3). If no source mentions it, the system refuses.
Only the caption and surrounding text are used: no vision model analyses the image itself.

**Mock mode:** hashing embeddings, a lexical reranker and an extractive "LLM" (`providers/local.py`) run offline and set `mock_mode=true`.
Real providers: `providers/remote.py` (OpenAI-compatible/Ollama LLM, sentence-transformers embeddings, cross-encoder reranker; unexecuted here).
