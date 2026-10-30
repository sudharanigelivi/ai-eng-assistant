# Engineering Summary

## Assignment outcome

This repository provides a runnable, engineer-led prototype for turning a software requirement into an actionable delivery plan, alongside the assignment's mandatory URL-shortener use case. It covers greenfield, brownfield and ambiguous inputs. The planner is deterministic and does not make an LLM call; AI assistance is scoped to individual engineering tasks, with a prompt, expected AI contribution, engineer ownership and validation criteria attached to each task.

## Implementation approach and rationale

- **Requirement planning:** keyword-based classification selects curated templates. The planner identifies ambiguities and assumptions, creates tasks with dependencies and parallel waves, and renders Markdown or JSON. Deterministic output is easy to review and reproduce; it is not presented as deep semantic understanding.
- **URL shortener:** FastAPI routes call a service layer, which uses a SQLite repository and a thread-safe TTL/LRU cache. Short codes use a cryptographic random source; aliases and target URLs are validated; clicks are recorded as background tasks and aggregated without storing IP addresses or full referrer URLs.
- **HTTP behavior:** management endpoints support create, metadata lookup, delete and analytics; redirects use 302 so each request can be observed and link expiry or deletion is not hidden by permanent browser caching. Optional API-key protection and create-rate limiting are available.
- **Concurrency refinement in this revision:** a cache miss and link deletion could interleave so that an old database read repopulated the cache after deletion. A deterministic regression test reproduced the stale redirect. Cache-miss filling and deletion are now coordinated; normal cache hits remain outside that lock.

## Generated artifacts

- Working FastAPI URL shortener with SQLite persistence and analytics.
- Planner CLI and HTTP endpoint producing structured task plans.
- OpenAPI contract at [docs/openapi.json](docs/openapi.json) and API schemas in the implementation.
- Render deployment Blueprints at [render.yaml](render.yaml) (persistent production) and [render.test.yaml](render.test.yaml) (ephemeral test), each with a generated management key.
- Public demo form in the test deployment: create rate-limited links without a visitor API key; management endpoints remain protected.
- Unit and integration tests, including expiry, validation, rate limiting, persistence, analytics and concurrency cases.
- Scenario inputs and generated Markdown/JSON plans in [examples/](examples).
- Architecture, scenario, validation/risk and setup documentation.

## AI-assisted development and ownership

AI assistance is task-scoped rather than autonomous. Planner tasks provide ready-to-use prompts for implementation, debugging, test creation, documentation and review. For this enhancement, AI assistance identified a cache/delete race, drafted a concurrency regression test, and proposed a narrowly scoped synchronization fix. The test was observed failing before the fix and passing afterward; the complete suite was then run. No AI output is accepted automatically. The engineer is responsible for reviewing the diff, deciding whether the change is appropriate, and owning the final submission.

The planner itself does not call an AI model and the repository does not contain external Copilot/ChatGPT conversation transcripts. The prompts are guidance for human-directed AI work, not evidence that an external model executed every task.

## Validation performed

- Full test command: `python -m pytest --cov --cov-report=term-missing`
- Result on Python 3.12.10: **111 passed**, **96% total line coverage**.
- Regression validation: the new cache/delete race test failed against the pre-fix implementation and passed after the fix.
- Mandatory planner scenario was run through the CLI and classified as `greenfield`, domain `url_shortener`, with medium ambiguity and explicit scale/analytics/API/persistence assumptions.

The assignment's sample output is available in [examples/greenfield.plan.md](examples/greenfield.plan.md) and [examples/greenfield.plan.json](examples/greenfield.plan.json).

## Risks, trade-offs and limitations

| Area | Decision / limitation | Mitigation or next step |
|---|---|---|
| Persistence and scale | SQLite is a single-node store and limits write throughput. | Keep the repository boundary; move to PostgreSQL for multi-node production use. |
| Cache and rate limits | Both are in-process and are not shared across replicas. | Use Redis or a gateway-provided shared limiter/cache when scaling out. |
| Click reliability | Background click recording can lose events if the process exits before the task completes. | Acceptable for prototype analytics; use a durable queue if events become business-critical. |
| Click retention | Raw click events grow over time. | Define retention and add rollups/partitioning before sustained production use. |
| URL screening | Literal private/loopback hosts are rejected, but DNS names are not resolved and checked. | Redirects are not fetched by this service; perform DNS/IP policy checks at resolution time if the threat model requires it. |
| Planner quality | Classification and domain selection use keyword heuristics and curated templates. | Treat plans as drafts; confirm scope and assumptions with stakeholders. |
| Performance | No load test or production latency/throughput measurements are included. | Benchmark on target hardware and representative traffic before making SLO claims. |

## Assumptions

- The URL-shortener requirements are evaluated as a prototype rather than a production multi-region service.
- SQLite, an in-process cache, optional shared API key, 302 redirects and per-link click analytics are acceptable prototype choices.
- Planner scale targets in the sample plan are assumptions for discussion, not measured performance claims.
