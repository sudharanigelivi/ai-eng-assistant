"""Knowledge base: vague-term catalogue, task templates, risks and trade-offs.

Everything here is authored and reviewed by the engineer. The planner only
selects and instantiates it; AI assistants are used *inside* each task via the
prompts below, never to decide scope or accept results.
"""

# term -> (question, default assumption, impact)
VAGUE_TERMS = {
    "scalable": (
        "What load must it sustain (requests/sec, links, data size) and what latency target applies?",
        "Target ~1,000 redirects/s and 50 creates/s per node, p95 redirect < 50 ms; scale out by adding stateless nodes.",
        "high",
    ),
    "fast": (
        "Which operation must be faster, by how much, and how is it measured?",
        "Latency of the hot path is the target; baseline first, then require a measurable improvement.",
        "medium",
    ),
    "faster": (
        "Which operation must be faster, by how much, and how is it measured?",
        "Latency of the hot path is the target; baseline first, then require a measurable improvement.",
        "medium",
    ),
    "better": (
        "Better by which measurable criterion (speed, correctness, UX, cost)?",
        "No change is made until a measurable acceptance criterion is agreed.",
        "high",
    ),
    "improve": (
        "What is the current problem and what is the success metric?",
        "Improvement is limited to the behaviour that is demonstrably wrong today.",
        "medium",
    ),
    "robust": (
        "Which failure modes must be tolerated (bad input, dependency outage, restarts)?",
        "Validate all input, fail with explicit errors, and survive restarts without data loss.",
        "medium",
    ),
    "secure": (
        "What is the threat model and which compliance rules apply?",
        "OWASP top-10 baseline: input validation, authn on management APIs, no secrets in code.",
        "high",
    ),
    "user-friendly": (
        "Who are the users and which workflows must be easy?",
        "A documented, consistent REST API is the only interface; no UI is built.",
        "medium",
    ),
    "simple": (
        "Simple for whom, and what may be left out?",
        "Prefer the smallest design that satisfies the stated requirements.",
        "low",
    ),
    "modern": (
        "What does modern mean here (language level, framework, architecture)?",
        "Use the repository's current stack; do not introduce new frameworks.",
        "medium",
    ),
    "etc": (
        "What else is included? The list appears open-ended.",
        "Only the explicitly listed items are in scope.",
        "medium",
    ),
    "analytics": (
        "Which metrics (totals, time series, referrers, geo, unique visitors) and what retention?",
        "Total clicks, clicks per day, top referrer hosts and device class; raw events kept, no IP/geo stored.",
        "medium",
    ),
    "apis": (
        "REST, GraphQL or gRPC? Who authenticates and how are errors reported?",
        "JSON REST over HTTP, OpenAPI documented, optional API key on management endpoints.",
        "medium",
    ),
    "persistence": (
        "Which datastore, durability and retention requirements apply?",
        "SQLite behind a repository interface for the prototype; the schema ports to PostgreSQL.",
        "medium",
    ),
}

BROWNFIELD_WORDS = (
    "fix", "bug", "refactor", "existing", "enhance", "enhancement", "legacy", "regression",
    "upgrade", "migrate", "currently", "broken", "crash", "improve test", "add tests",
    "test coverage", "documentation", "docs", "optimi", "performance", "slow",
)
GREENFIELD_WORDS = (
    "build", "create", "new ", "design", "develop", "implement", "from scratch", "set up",
    "greenfield", "launch",
)
URL_SHORTENER_WORDS = ("url shortener", "short link", "shortener", "short url", "link shortener")

NUMBER_RE = r"\d+\s*(k|m|rps|qps|req|requests|users|ms|s|links|gb|mb)?"


def _t(key, title, category, deps, deliverables, prompt, ai_role, owns, validation):
    return dict(
        key=key, title=title, category=category, deps=deps, deliverables=deliverables,
        prompt=prompt, ai_role=ai_role, owns=owns, validation=validation,
    )


GREENFIELD_GENERIC = [
    _t("clarify", "Clarify requirement and acceptance criteria", "clarify", [],
       ["Problem statement", "Numbered acceptance criteria", "Documented assumptions"],
       "Requirement: \"{req}\". List ambiguities, missing non-functional requirements and testable acceptance criteria. Do not propose a design yet.",
       "Surfaces gaps and drafts acceptance criteria.",
       "Decides which assumptions are acceptable and signs off scope.",
       ["Every acceptance criterion is testable", "Open questions have an owner or a recorded assumption"]),
    _t("contract", "Define API contract and data schema", "design", ["clarify"],
       ["OpenAPI contract", "Error model", "Schema definition"],
       "Draft an OpenAPI 3 contract and relational schema for: \"{req}\". Include error responses, pagination and validation limits.",
       "Produces a first-draft contract and schema.",
       "Reviews naming, status codes, backwards compatibility and constraints.",
       ["Contract lints clean", "Every endpoint has success and error cases"]),
    _t("core", "Implement core domain logic", "code", ["contract"],
       ["Domain/service layer", "Repository interface"],
       "Implement the domain service for \"{req}\" behind a repository interface. Keep I/O out of the domain layer and return typed errors.",
       "Generates implementation and boilerplate.",
       "Reviews design boundaries, error handling and complexity line by line.",
       ["Unit tests pass", "No business logic in transport layer"]),
    _t("interfaces", "Implement API/interface layer", "code", ["core"],
       ["HTTP handlers", "Input validation"],
       "Expose the service for \"{req}\" through the OpenAPI contract with strict input validation and consistent errors.",
       "Generates handlers and validation models.",
       "Verifies behaviour matches the contract exactly.",
       ["Contract tests pass", "Invalid input returns 4xx, never 5xx"]),
    _t("hardening", "Security and performance hardening", "code", ["interfaces"],
       ["Auth/rate limiting where needed", "Performance notes"],
       "Review this implementation of \"{req}\" for injection, abuse, resource exhaustion and N+1 queries. List findings with severity.",
       "Acts as a second reviewer producing a findings list.",
       "Triages every finding; fixes or documents each one.",
       ["Each finding resolved or accepted with rationale"]),
    _t("tests", "Write unit and integration tests", "test", ["interfaces"],
       ["Unit tests", "Integration tests", "Coverage report"],
       "Write pytest unit and integration tests for \"{req}\" covering happy path, boundaries, errors and concurrency. Prefer behaviour over implementation.",
       "Generates test cases and fixtures, including edge cases the engineer may miss.",
       "Checks each test can fail (mutation by hand), removes tautologies, sets the coverage bar.",
       ["Tests fail when behaviour is deliberately broken", "Coverage >= 85% on core logic"]),
    _t("docs", "Write documentation", "docs", ["tests", "hardening"],
       ["README", "Architecture notes", "Runbook"],
       "Draft README setup steps and architecture notes for \"{req}\" from the code and contract. Flag anything you cannot verify.",
       "Drafts prose from code and contract.",
       "Executes every documented command and corrects inaccuracies.",
       ["A new engineer can run the project using only the README"]),
    _t("review", "Final review and release checklist", "review", ["docs"],
       ["Review notes", "Known limitations"],
       "Act as a skeptical reviewer of this change for \"{req}\". List correctness, security, maintainability and test gaps.",
       "Independent review pass to catch blind spots.",
       "Owns the merge decision and the known-limitations list.",
       ["All blocking review comments resolved"]),
]

URL_SHORTENER_GREENFIELD = [
    _t("clarify", "Clarify requirement, scale targets and analytics scope", "clarify", [],
       ["Problem statement", "NFR targets (throughput, latency)", "Analytics definition"],
       "Requirement: \"{req}\". Identify ambiguities in 'scalable', 'persistence' and 'analytics'. Propose measurable targets and a minimal analytics set.",
       "Lists ambiguities and proposes targets.",
       "Chooses targets and records them as assumptions.",
       ["Targets are numeric", "Analytics fields are enumerated"]),
    _t("contract", "Design REST API contract (OpenAPI)", "design", ["clarify"],
       ["POST/GET/DELETE /api/v1/links", "GET /api/v1/links/{code}/analytics", "GET /{code} redirect", "Error model"],
       "Draft an OpenAPI 3 contract for a URL shortener: create (custom alias, expiry), fetch, delete, analytics, redirect (302). Define 404/409/410/422/429 semantics.",
       "Drafts endpoints and schemas.",
       "Chooses 302 over 301 (analytics must see every click) and the status code for each failure.",
       ["Every endpoint documents error cases", "Redirect status chosen with rationale"]),
    _t("schema", "Design persistence schema", "design", ["clarify"],
       ["links table", "clicks table + (code, ts) index"],
       "Design a relational schema for short links and click events supporting redirect lookup by code and per-day aggregation. Explain indexes.",
       "Proposes DDL and indexes.",
       "Validates keys, cascade rules and that the hot path is one indexed lookup.",
       ["Redirect lookup is a primary-key read", "Deleting a link removes its clicks"]),
    _t("codegen", "Short-code generation and URL validation", "code", ["contract"],
       ["Code generator", "URL/alias validator"],
       "Implement collision-safe short code generation and strict URL validation (scheme allow-list, no credentials, no private hosts, length limits).",
       "Generates generator and validator.",
       "Reviews randomness source (secrets, not random), collision retry and SSRF/open-redirect risks.",
       ["Property-style tests on alphabet/length", "Malicious URL corpus rejected"]),
    _t("repo", "Implement persistence layer", "code", ["schema"],
       ["Repository class", "Migrations/DDL"],
       "Implement a repository over the schema with create/get/delete/record_click/analytics queries; parameterised SQL only.",
       "Writes SQL and repository code.",
       "Checks parameterisation, transaction scope and locking behaviour.",
       ["No string-built SQL", "Concurrent click recording does not lose counts"]),
    _t("service", "Implement service layer: create, resolve, expire, cache", "code", ["codegen", "repo"],
       ["Service class", "TTL/LRU cache"],
       "Implement the service orchestrating validation, persistence, expiry checks and a read-through cache invalidated on delete.",
       "Generates service and cache.",
       "Reviews cache invalidation, expiry correctness and clock handling.",
       ["Deleted link never served from cache", "Expired link returns 410"]),
    _t("api", "Implement HTTP API and redirect", "code", ["contract", "service"],
       ["FastAPI app", "Pydantic models"],
       "Implement the OpenAPI contract with FastAPI. Record clicks in a background task so redirects stay fast.",
       "Generates routes and models.",
       "Confirms behaviour matches the contract and analytics cannot block redirects.",
       ["Generated OpenAPI matches the contract"]),
    _t("analytics", "Implement click analytics", "code", ["repo", "api"],
       ["Click capture", "Analytics endpoint"],
       "Capture referrer host and device class per click (no raw IP), expose totals, per-day series, top referrers and devices for a window.",
       "Generates capture and aggregation queries.",
       "Decides privacy boundary (what is NOT stored) and verifies aggregation maths.",
       ["Aggregates equal raw event counts", "No PII stored"]),
    _t("hardening", "Abuse protection and security hardening", "code", ["api"],
       ["Rate limiting", "API key on management endpoints", "Reserved aliases"],
       "Review the shortener for abuse: enumeration, alias squatting, SSRF via targets, unbounded input, rate-limit bypass. Provide findings.",
       "Second-reviewer pass producing findings.",
       "Triages each finding and decides the mitigation or accepted risk.",
       ["Each finding closed or documented"]),
    _t("tests", "Unit and integration tests", "test", ["analytics", "hardening"],
       ["Unit tests per module", "API integration tests", "Concurrency test"],
       "Write pytest tests for validation, generator, repository, cache, service, API and analytics including expiry, alias conflicts and concurrent clicks.",
       "Generates tests and edge cases.",
       "Verifies tests can fail, removes weak assertions, owns the coverage threshold.",
       ["Coverage >= 85%", "All tests deterministic (injected clock)"]),
    _t("perf", "Load check and scaling notes", "test", ["api"],
       ["Redirect micro-benchmark", "Scaling plan"],
       "Create a small load script for the redirect path and summarise bottlenecks and the path to PostgreSQL/Redis for horizontal scale.",
       "Writes the benchmark and drafts scaling notes.",
       "Interprets numbers honestly (prototype vs production hardware).",
       ["Throughput/latency recorded with caveats"]),
    _t("docs", "Documentation and runbook", "docs", ["tests", "perf"],
       ["README", "Architecture", "Example scenarios"],
       "Draft README, architecture and runbook from the code. Mark any statement you cannot verify.",
       "Drafts docs.",
       "Runs every documented command and fixes mistakes.",
       ["README steps executed successfully"]),
    _t("review", "Final review", "review", ["docs"],
       ["Review notes", "Known limitations"],
       "Review the whole change as a skeptical maintainer: correctness, security, maintainability, test gaps.",
       "Independent review pass.",
       "Owns merge decision and limitations list.",
       ["No unresolved blocking comments"]),
]

BROWNFIELD = [
    _t("understand", "Understand existing behaviour and reproduce the issue", "clarify", [],
       ["Reproduction steps or failing test", "Affected modules list"],
       "Requirement: \"{req}\". Given the relevant existing code, explain current behaviour, where it deviates from expectation, and how to reproduce it.",
       "Reads and explains unfamiliar code; suggests reproduction.",
       "Confirms the explanation by running the code; never trusts it unverified.",
       ["Issue reproduced locally", "Expected behaviour agreed"]),
    _t("characterize", "Add characterization / failing tests first", "test", ["understand"],
       ["Test that fails for the bug or pins current behaviour"],
       "Write pytest tests that pin the current behaviour around \"{req}\" and one that fails for the reported defect.",
       "Generates tests quickly.",
       "Confirms the new test fails for the right reason before any fix.",
       ["Failing test fails on unchanged code", "Existing suite is green"]),
    _t("design", "Design the smallest safe change", "design", ["characterize"],
       ["Change plan", "Compatibility and rollback notes"],
       "Propose the minimal change for \"{req}\" that preserves public behaviour; list alternatives and blast radius.",
       "Proposes options and enumerates impacted callers.",
       "Chooses the option; verifies callers via search, not memory.",
       ["API/schema compatibility explicitly checked"]),
    _t("implement", "Implement the change / refactor", "code", ["design"],
       ["Focused diff"],
       "Implement the planned change for \"{req}\" with a minimal diff. Do not alter unrelated code.",
       "Generates the diff.",
       "Reads every changed line; rejects unrelated edits.",
       ["Diff touches only planned modules"]),
    _t("regress", "Regression and new-behaviour tests", "test", ["implement"],
       ["Passing new tests", "Full suite green", "Coverage delta"],
       "Extend tests for \"{req}\": boundaries, error paths and regression guards for neighbouring behaviour.",
       "Suggests extra edge cases.",
       "Checks coverage did not fall and tests are meaningful.",
       ["Full suite passes", "Coverage not reduced"]),
    _t("docs", "Update docs and changelog", "docs", ["implement"],
       ["Docs/changelog updates"],
       "Update documentation and changelog for the change described by \"{req}\"; list every doc that references the old behaviour.",
       "Finds and drafts doc updates.",
       "Verifies accuracy against the code.",
       ["No stale references to old behaviour"]),
    _t("review", "Review, rollout and rollback plan", "review", ["regress", "docs"],
       ["Review notes", "Rollback steps"],
       "Review the diff for \"{req}\" for regressions, security and performance impact; suggest a safe rollout.",
       "Independent review pass.",
       "Owns release decision and rollback plan.",
       ["Rollback tested or trivially reversible"]),
]

AMBIGUOUS_PREFIX = [
    _t("clarify", "Resolve ambiguities with stakeholders (blocking)", "clarify", [],
       ["Answered clarification questions", "Measurable acceptance criteria"],
       "Requirement: \"{req}\". Generate the most valuable clarifying questions ranked by impact, with a safe default assumption for each.",
       "Drafts ranked questions and default assumptions.",
       "Asks stakeholders; no implementation starts on unanswered high-impact questions.",
       ["All high-impact ambiguities answered or explicitly assumed"]),
    _t("spike", "Time-boxed spike on a thin vertical slice", "design", ["clarify"],
       ["Throwaway prototype", "Findings and revised estimate"],
       "Sketch the thinnest end-to-end slice that would validate the riskiest assumption in \"{req}\".",
       "Scaffolds the prototype.",
       "Decides what the spike proves and discards the code if it is not production quality.",
       ["Riskiest assumption confirmed or refuted"]),
]

URL_SHORTENER_RISKS = [
    ("functional", "Short-code collisions under concurrency.",
     "UNIQUE constraint plus bounded retry; 62^7 (~3.5e12) code space makes collisions rare."),
    ("functional", "Expired or deleted links still redirecting because of caching.",
     "Expiry is re-checked on every cache hit; delete invalidates the cache; TTL bounds staleness on other nodes."),
    ("design", "Single SQLite writer limits write throughput and horizontal scale.",
     "Repository interface isolates SQL; documented migration to PostgreSQL + Redis cache."),
    ("design", "Click recording on the redirect path could add latency or lose events on crash.",
     "Recorded in a background task; accepted trade-off of possible loss on crash (analytics, not billing)."),
    ("functional", "Open redirect / SSRF abuse through attacker-chosen targets.",
     "Scheme allow-list, no credentials, no private/loopback hosts, rate limiting, optional API key."),
]

GENERIC_RISKS = [
    ("functional", "Requirement interpreted differently by stakeholders.",
     "Acceptance criteria and assumptions are written down and reviewed before coding."),
    ("design", "Over-engineering beyond the stated requirement.",
     "Smallest design satisfying the criteria; extension points documented, not built."),
    ("functional", "Edge cases and error paths are untested.",
     "Tests for boundaries and failures are written for every task; coverage gate in CI."),
]

BROWNFIELD_RISKS = [
    ("functional", "Behavioural regression in code the change does not obviously touch.",
     "Characterization tests before change; full suite must be green."),
    ("design", "Hidden callers depend on current (buggy) behaviour.",
     "Search for all usages; communicate behaviour changes in the changelog."),
]

AMBIGUOUS_RISKS = [
    ("functional", "Building the wrong thing because key questions were never answered.",
     "Blocking clarification task; spike validates the riskiest assumption before commitment."),
    ("design", "Rework from unstable scope.",
     "Keep spike code disposable; plan is regenerated once ambiguities are resolved."),
]

AI_RISKS = [
    ("ai", "AI output looks plausible but is incorrect or uses non-existent APIs.",
     "Every generated unit is run, type-checked and covered by tests before acceptance."),
    ("ai", "AI-written tests may be tautological and miss gaps (coverage illusion).",
     "Engineer breaks the code deliberately to confirm tests fail; coverage is a floor, not proof."),
    ("ai", "Inefficient or insecure patterns (N+1 queries, string-built SQL, weak randomness).",
     "Checklist review for SQL, randomness, input validation and complexity; separate AI review pass."),
    ("ai", "Sensitive data or proprietary code exposed to AI tools.",
     "Prompts contain requirements and snippets only; no secrets or customer data."),
]

TRADE_OFFS_URL = [
    ("Datastore", "SQLite behind a repository interface", "PostgreSQL + Redis from day one",
     "Zero-setup, runnable prototype; the interface keeps migration cheap. Limited write concurrency."),
    ("Short-code strategy", "Random 7-char base62 with retry", "Counter/ID-encoded codes",
     "No coordination between nodes and codes are non-enumerable; needs collision retry."),
    ("Redirect status", "302 Found", "301 Moved Permanently",
     "301 is cached by browsers, which would hide clicks and make delete/expiry ineffective."),
    ("Analytics write path", "Background task after response", "Synchronous write or message queue",
     "Keeps redirect latency low; may drop events on crash. A queue is the production upgrade."),
    ("Caching", "In-process TTL/LRU", "Shared Redis cache",
     "No extra infrastructure; per-node caches can be stale up to the TTL."),
    ("Rate limiting", "In-process token bucket", "Distributed limiter (Redis/gateway)",
     "Simple and testable; limits are per node."),
]

TRADE_OFFS_GENERIC = [
    ("Plan generation", "Deterministic rules + curated templates", "LLM-generated plans",
     "Reproducible and reviewable; less flexible. LLM output would still need engineer review."),
    ("Delivery order", "Contract and tests before wide implementation", "Code first",
     "Slower start, fewer rework cycles and clearer acceptance criteria."),
]

LIMITATIONS_BASE = [
    "Plans are templates tailored by keyword detection, not deep semantic understanding.",
    "AI prompts are generated for an engineer to run in Copilot/ChatGPT; the tool calls no model itself.",
]
