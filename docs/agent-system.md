# Agent system

`agents/workflow.py` is a controlled state machine: `plan -> search -> retrieve -> analyze -> compare -> verify -> synthesize`.

- Static transition table; the only conditional edge skips `compare` when fewer than two papers were cited.
- Hard cap `max_steps` (default 12); exceeding it records "step limit reached".
- A failing node is recorded (`node:failed`, type name only: no stack trace) and the run continues.
- The planner is rule-based (keyword triggers), not an LLM. Nodes are pure functions of `ResearchState`, so they map one-to-one onto a
  LangGraph `StateGraph`; **LangGraph itself is not used** (not installable in the build sandbox).
- The synthesis step labels sections `Source evidence`, `Comparison`, `Verification`, `Model inference`. In mock mode no model inference is generated.
