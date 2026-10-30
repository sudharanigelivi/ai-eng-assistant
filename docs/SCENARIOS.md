# Example scenarios

Each scenario was run through `python -m planner --file examples/<name>.txt`; the full outputs (`.plan.md`, `.plan.json`) are in [`../examples`](../examples). Plans are **drafts for the engineer to review**, and the planner does not call an LLM.

| Scenario | Input | Classified | Ambiguity | Tasks |
|---|---|---|---|---|
| Greenfield | "Build a scalable URL shortener service with APIs, persistence, and analytics." | greenfield, `url_shortener` | medium | 13 |
| Brownfield | "Fix the bug in the existing checkout service where duplicate orders are created." | brownfield | low | 7 |
| Ambiguous | "Make the app better and faster" | ambiguous | high | 9 |

## 1. Greenfield: URL shortener (implemented in `shortener/`)

- **Breakdown:** clarify scale and analytics targets, design the API and schema, then implement in parallel waves (storage, validation, code generation, caching, analytics), followed by tests, docs and review.
- **AI-assisted execution:** AI drafts the schema, endpoint handlers and test cases from the per-task prompts. The engineer decides the 302 vs 301 redirect, the collision strategy, the SSRF rules and the privacy limits on stored data.
- **Validation:** 105 automated tests, plus a manual run with uvicorn and curl.
- **Working assumptions** (flagged for confirmation): about 1,000 redirects/s per node, p95 redirect under 50 ms, and click events kept raw. These are design targets, **not measured results**.

## 2. Brownfield: fix a bug in an existing service

- **Breakdown:** reproduce with a failing test first, locate the root cause, make the smallest safe fix, add regression tests, check for side effects, and review.
- **AI-assisted execution:** AI helps read unfamiliar code and propose hypotheses. The engineer confirms the root cause by running the code and keeps behaviour otherwise unchanged.
- **Validation:** the failing test passes after the fix, the existing suite stays green, and the diff is reviewed for unrelated changes.

## 3. Ambiguous: "Make the app better and faster"

- **Breakdown:** a clarify task comes first, then a time-boxed spike. The remaining generic tasks depend on the spike, so no implementation begins before there are measurable acceptance criteria.
- **AI-assisted execution:** AI drafts clarifying questions and candidate metrics. The engineer takes them to stakeholders and does not guess.
- **Validation:** the agreed criteria are written down, and before and after measurements are compared against them.
