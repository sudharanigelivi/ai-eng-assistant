# Engineering plan: Build a scalable URL shortener service with APIs, persistence, and analytics.

- **Type:** greenfield  |  **Domain:** url_shortener  |  **Ambiguity:** medium

## Problem statement
Deliver a stateless HTTP service that maps long URLs to short codes, redirects with low latency, persists links durably, and reports per-link click analytics, with explicit numeric scale targets and abuse protection.

## Ambiguities and assumptions
| Term | Impact | Question | Working assumption |
|---|---|---|---|
| scalable | high | What load must it sustain (requests/sec, links, data size) and what latency target applies? | Target ~1,000 redirects/s and 50 creates/s per node, p95 redirect < 50 ms; scale out by adding stateless nodes. |
| analytics | medium | Which metrics (totals, time series, referrers, geo, unique visitors) and what retention? | Total clicks, clicks per day, top referrer hosts and device class; raw events kept, no IP/geo stored. |
| apis | medium | REST, GraphQL or gRPC? Who authenticates and how are errors reported? | JSON REST over HTTP, OpenAPI documented, optional API key on management endpoints. |
| persistence | medium | Which datastore, durability and retention requirements apply? | SQLite behind a repository interface for the prototype; the schema ports to PostgreSQL. |

## Task breakdown (execution order; tasks in the same wave can run in parallel)

### Wave 1

**T1 - Clarify requirement, scale targets and analytics scope** `[clarify]` depends on: none
- Deliverables: Problem statement; NFR targets (throughput, latency); Analytics definition
- AI prompt: _Requirement: "Build a scalable URL shortener service with APIs, persistence, and analytics.". Identify ambiguities in 'scalable', 'persistence' and 'analytics'. Propose measurable targets and a minimal analytics set._
- AI does: Lists ambiguities and proposes targets.
- Engineer owns: Chooses targets and records them as assumptions.
- Validation: Targets are numeric; Analytics fields are enumerated

### Wave 2

**T2 - Design REST API contract (OpenAPI)** `[design]` depends on: T1
- Deliverables: POST/GET/DELETE /api/v1/links; GET /api/v1/links/{code}/analytics; GET /{code} redirect; Error model
- AI prompt: _Draft an OpenAPI 3 contract for a URL shortener: create (custom alias, expiry), fetch, delete, analytics, redirect (302). Define 404/409/410/422/429 semantics._
- AI does: Drafts endpoints and schemas.
- Engineer owns: Chooses 302 over 301 (analytics must see every click) and the status code for each failure.
- Validation: Every endpoint documents error cases; Redirect status chosen with rationale

**T3 - Design persistence schema** `[design]` depends on: T1
- Deliverables: links table; clicks table + (code, ts) index
- AI prompt: _Design a relational schema for short links and click events supporting redirect lookup by code and per-day aggregation. Explain indexes._
- AI does: Proposes DDL and indexes.
- Engineer owns: Validates keys, cascade rules and that the hot path is one indexed lookup.
- Validation: Redirect lookup is a primary-key read; Deleting a link removes its clicks

### Wave 3

**T4 - Short-code generation and URL validation** `[code]` depends on: T2
- Deliverables: Code generator; URL/alias validator
- AI prompt: _Implement collision-safe short code generation and strict URL validation (scheme allow-list, no credentials, no private hosts, length limits)._
- AI does: Generates generator and validator.
- Engineer owns: Reviews randomness source (secrets, not random), collision retry and SSRF/open-redirect risks.
- Validation: Property-style tests on alphabet/length; Malicious URL corpus rejected

**T5 - Implement persistence layer** `[code]` depends on: T3
- Deliverables: Repository class; Migrations/DDL
- AI prompt: _Implement a repository over the schema with create/get/delete/record_click/analytics queries; parameterised SQL only._
- AI does: Writes SQL and repository code.
- Engineer owns: Checks parameterisation, transaction scope and locking behaviour.
- Validation: No string-built SQL; Concurrent click recording does not lose counts

### Wave 4

**T6 - Implement service layer: create, resolve, expire, cache** `[code]` depends on: T4, T5
- Deliverables: Service class; TTL/LRU cache
- AI prompt: _Implement the service orchestrating validation, persistence, expiry checks and a read-through cache invalidated on delete._
- AI does: Generates service and cache.
- Engineer owns: Reviews cache invalidation, expiry correctness and clock handling.
- Validation: Deleted link never served from cache; Expired link returns 410

### Wave 5

**T7 - Implement HTTP API and redirect** `[code]` depends on: T2, T6
- Deliverables: FastAPI app; Pydantic models
- AI prompt: _Implement the OpenAPI contract with FastAPI. Record clicks in a background task so redirects stay fast._
- AI does: Generates routes and models.
- Engineer owns: Confirms behaviour matches the contract and analytics cannot block redirects.
- Validation: Generated OpenAPI matches the contract

### Wave 6

**T8 - Implement click analytics** `[code]` depends on: T5, T7
- Deliverables: Click capture; Analytics endpoint
- AI prompt: _Capture referrer host and device class per click (no raw IP), expose totals, per-day series, top referrers and devices for a window._
- AI does: Generates capture and aggregation queries.
- Engineer owns: Decides privacy boundary (what is NOT stored) and verifies aggregation maths.
- Validation: Aggregates equal raw event counts; No PII stored

**T9 - Abuse protection and security hardening** `[code]` depends on: T7
- Deliverables: Rate limiting; API key on management endpoints; Reserved aliases
- AI prompt: _Review the shortener for abuse: enumeration, alias squatting, SSRF via targets, unbounded input, rate-limit bypass. Provide findings._
- AI does: Second-reviewer pass producing findings.
- Engineer owns: Triages each finding and decides the mitigation or accepted risk.
- Validation: Each finding closed or documented

**T11 - Load check and scaling notes** `[test]` depends on: T7
- Deliverables: Redirect micro-benchmark; Scaling plan
- AI prompt: _Create a small load script for the redirect path and summarise bottlenecks and the path to PostgreSQL/Redis for horizontal scale._
- AI does: Writes the benchmark and drafts scaling notes.
- Engineer owns: Interprets numbers honestly (prototype vs production hardware).
- Validation: Throughput/latency recorded with caveats

### Wave 7

**T10 - Unit and integration tests** `[test]` depends on: T8, T9
- Deliverables: Unit tests per module; API integration tests; Concurrency test
- AI prompt: _Write pytest tests for validation, generator, repository, cache, service, API and analytics including expiry, alias conflicts and concurrent clicks._
- AI does: Generates tests and edge cases.
- Engineer owns: Verifies tests can fail, removes weak assertions, owns the coverage threshold.
- Validation: Coverage >= 85%; All tests deterministic (injected clock)

### Wave 8

**T12 - Documentation and runbook** `[docs]` depends on: T10, T11
- Deliverables: README; Architecture; Example scenarios
- AI prompt: _Draft README, architecture and runbook from the code. Mark any statement you cannot verify._
- AI does: Drafts docs.
- Engineer owns: Runs every documented command and fixes mistakes.
- Validation: README steps executed successfully

### Wave 9

**T13 - Final review** `[review]` depends on: T12
- Deliverables: Review notes; Known limitations
- AI prompt: _Review the whole change as a skeptical maintainer: correctness, security, maintainability, test gaps._
- AI does: Independent review pass.
- Engineer owns: Owns merge decision and limitations list.
- Validation: No unresolved blocking comments

## Risks and mitigations
| Kind | Risk | Mitigation |
|---|---|---|
| functional | Short-code collisions under concurrency. | UNIQUE constraint plus bounded retry; 62^7 (~3.5e12) code space makes collisions rare. |
| functional | Expired or deleted links still redirecting because of caching. | Expiry is re-checked on every cache hit; delete invalidates the cache; TTL bounds staleness on other nodes. |
| design | Single SQLite writer limits write throughput and horizontal scale. | Repository interface isolates SQL; documented migration to PostgreSQL + Redis cache. |
| design | Click recording on the redirect path could add latency or lose events on crash. | Recorded in a background task; accepted trade-off of possible loss on crash (analytics, not billing). |
| functional | Open redirect / SSRF abuse through attacker-chosen targets. | Scheme allow-list, no credentials, no private/loopback hosts, rate limiting, optional API key. |
| functional | Requirement interpreted differently by stakeholders. | Acceptance criteria and assumptions are written down and reviewed before coding. |
| design | Over-engineering beyond the stated requirement. | Smallest design satisfying the criteria; extension points documented, not built. |
| functional | Edge cases and error paths are untested. | Tests for boundaries and failures are written for every task; coverage gate in CI. |
| ai | AI output looks plausible but is incorrect or uses non-existent APIs. | Every generated unit is run, type-checked and covered by tests before acceptance. |
| ai | AI-written tests may be tautological and miss gaps (coverage illusion). | Engineer breaks the code deliberately to confirm tests fail; coverage is a floor, not proof. |
| ai | Inefficient or insecure patterns (N+1 queries, string-built SQL, weak randomness). | Checklist review for SQL, randomness, input validation and complexity; separate AI review pass. |
| ai | Sensitive data or proprietary code exposed to AI tools. | Prompts contain requirements and snippets only; no secrets or customer data. |

## Trade-offs
| Decision | Chosen | Alternative | Rationale |
|---|---|---|---|
| Datastore | SQLite behind a repository interface | PostgreSQL + Redis from day one | Zero-setup, runnable prototype; the interface keeps migration cheap. Limited write concurrency. |
| Short-code strategy | Random 7-char base62 with retry | Counter/ID-encoded codes | No coordination between nodes and codes are non-enumerable; needs collision retry. |
| Redirect status | 302 Found | 301 Moved Permanently | 301 is cached by browsers, which would hide clicks and make delete/expiry ineffective. |
| Analytics write path | Background task after response | Synchronous write or message queue | Keeps redirect latency low; may drop events on crash. A queue is the production upgrade. |
| Caching | In-process TTL/LRU | Shared Redis cache | No extra infrastructure; per-node caches can be stale up to the TTL. |
| Rate limiting | In-process token bucket | Distributed limiter (Redis/gateway) | Simple and testable; limits are per node. |
| Plan generation | Deterministic rules + curated templates | LLM-generated plans | Reproducible and reviewable; less flexible. LLM output would still need engineer review. |
| Delivery order | Contract and tests before wide implementation | Code first | Slower start, fewer rework cycles and clearer acceptance criteria. |

## Limitations
- Plans are templates tailored by keyword detection, not deep semantic understanding.
- AI prompts are generated for an engineer to run in Copilot/ChatGPT; the tool calls no model itself.

