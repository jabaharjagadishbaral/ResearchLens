# Citation and claim verification

**Citations.** Evidence blocks are numbered 1..n per answer. The UI only links `[n]` that map to a real citation.

**Verification** (`verification/verifier.py`) classifies each answer sentence against the evidence it cites (or all evidence if uncited):
`SUPPORTED`, `PARTIALLY_SUPPORTED`, `UNSUPPORTED`, `CONTRADICTED`, `INSUFFICIENT_EVIDENCE`.

The shipped `LexicalVerifier` is a **mock**: token coverage of the best evidence sentence window, plus rules for standalone-number
mismatch (92.4 vs 97.8 => contradicted) and negation flips. It cannot detect paraphrased contradictions or reasoning errors.
Production should implement `ClaimVerifier` with an NLI model or LLM judge. Measured on 6 labelled synthetic claims it scores 6/6, which says little about real text.
