# Engineering plan: Make the app better and faster

- **Type:** ambiguous  |  **Domain:** generic  |  **Ambiguity:** high

## Problem statement
The request "Make the app better and faster" is underspecified. Convert it into measurable acceptance criteria before committing to a design.

## Ambiguities and assumptions
| Term | Impact | Question | Working assumption |
|---|---|---|---|
| better | high | Better by which measurable criterion (speed, correctness, UX, cost)? | No change is made until a measurable acceptance criterion is agreed. |
| scope | high | What outcome, for which users, would make this successful? | No implementation begins until success criteria are agreed. |
| faster | medium | Which operation must be faster, by how much, and how is it measured? | Latency of the hot path is the target; baseline first, then require a measurable improvement. |

## Task breakdown (execution order; tasks in the same wave can run in parallel)

### Wave 1

**T1 - Resolve ambiguities with stakeholders (blocking)** `[clarify]` depends on: none
- Deliverables: Answered clarification questions; Measurable acceptance criteria
- AI prompt: _Requirement: "Make the app better and faster". Generate the most valuable clarifying questions ranked by impact, with a safe default assumption for each._
- AI does: Drafts ranked questions and default assumptions.
- Engineer owns: Asks stakeholders; no implementation starts on unanswered high-impact questions.
- Validation: All high-impact ambiguities answered or explicitly assumed

### Wave 2

**T2 - Time-boxed spike on a thin vertical slice** `[design]` depends on: T1
- Deliverables: Throwaway prototype; Findings and revised estimate
- AI prompt: _Sketch the thinnest end-to-end slice that would validate the riskiest assumption in "Make the app better and faster"._
- AI does: Scaffolds the prototype.
- Engineer owns: Decides what the spike proves and discards the code if it is not production quality.
- Validation: Riskiest assumption confirmed or refuted

### Wave 3

**T3 - Define API contract and data schema** `[design]` depends on: T2
- Deliverables: OpenAPI contract; Error model; Schema definition
- AI prompt: _Draft an OpenAPI 3 contract and relational schema for: "Make the app better and faster". Include error responses, pagination and validation limits._
- AI does: Produces a first-draft contract and schema.
- Engineer owns: Reviews naming, status codes, backwards compatibility and constraints.
- Validation: Contract lints clean; Every endpoint has success and error cases

### Wave 4

**T4 - Implement core domain logic** `[code]` depends on: T3
- Deliverables: Domain/service layer; Repository interface
- AI prompt: _Implement the domain service for "Make the app better and faster" behind a repository interface. Keep I/O out of the domain layer and return typed errors._
- AI does: Generates implementation and boilerplate.
- Engineer owns: Reviews design boundaries, error handling and complexity line by line.
- Validation: Unit tests pass; No business logic in transport layer

### Wave 5

**T5 - Implement API/interface layer** `[code]` depends on: T4
- Deliverables: HTTP handlers; Input validation
- AI prompt: _Expose the service for "Make the app better and faster" through the OpenAPI contract with strict input validation and consistent errors._
- AI does: Generates handlers and validation models.
- Engineer owns: Verifies behaviour matches the contract exactly.
- Validation: Contract tests pass; Invalid input returns 4xx, never 5xx

### Wave 6

**T6 - Security and performance hardening** `[code]` depends on: T5
- Deliverables: Auth/rate limiting where needed; Performance notes
- AI prompt: _Review this implementation of "Make the app better and faster" for injection, abuse, resource exhaustion and N+1 queries. List findings with severity._
- AI does: Acts as a second reviewer producing a findings list.
- Engineer owns: Triages every finding; fixes or documents each one.
- Validation: Each finding resolved or accepted with rationale

**T7 - Write unit and integration tests** `[test]` depends on: T5
- Deliverables: Unit tests; Integration tests; Coverage report
- AI prompt: _Write pytest unit and integration tests for "Make the app better and faster" covering happy path, boundaries, errors and concurrency. Prefer behaviour over implementation._
- AI does: Generates test cases and fixtures, including edge cases the engineer may miss.
- Engineer owns: Checks each test can fail (mutation by hand), removes tautologies, sets the coverage bar.
- Validation: Tests fail when behaviour is deliberately broken; Coverage >= 85% on core logic

### Wave 7

**T8 - Write documentation** `[docs]` depends on: T7, T6
- Deliverables: README; Architecture notes; Runbook
- AI prompt: _Draft README setup steps and architecture notes for "Make the app better and faster" from the code and contract. Flag anything you cannot verify._
- AI does: Drafts prose from code and contract.
- Engineer owns: Executes every documented command and corrects inaccuracies.
- Validation: A new engineer can run the project using only the README

### Wave 8

**T9 - Final review and release checklist** `[review]` depends on: T8
- Deliverables: Review notes; Known limitations
- AI prompt: _Act as a skeptical reviewer of this change for "Make the app better and faster". List correctness, security, maintainability and test gaps._
- AI does: Independent review pass to catch blind spots.
- Engineer owns: Owns the merge decision and the known-limitations list.
- Validation: All blocking review comments resolved

## Risks and mitigations
| Kind | Risk | Mitigation |
|---|---|---|
| functional | Building the wrong thing because key questions were never answered. | Blocking clarification task; spike validates the riskiest assumption before commitment. |
| design | Rework from unstable scope. | Keep spike code disposable; plan is regenerated once ambiguities are resolved. |
| ai | AI output looks plausible but is incorrect or uses non-existent APIs. | Every generated unit is run, type-checked and covered by tests before acceptance. |
| ai | AI-written tests may be tautological and miss gaps (coverage illusion). | Engineer breaks the code deliberately to confirm tests fail; coverage is a floor, not proof. |
| ai | Inefficient or insecure patterns (N+1 queries, string-built SQL, weak randomness). | Checklist review for SQL, randomness, input validation and complexity; separate AI review pass. |
| ai | Sensitive data or proprietary code exposed to AI tools. | Prompts contain requirements and snippets only; no secrets or customer data. |

## Trade-offs
| Decision | Chosen | Alternative | Rationale |
|---|---|---|---|
| Plan generation | Deterministic rules + curated templates | LLM-generated plans | Reproducible and reviewable; less flexible. LLM output would still need engineer review. |
| Delivery order | Contract and tests before wide implementation | Code first | Slower start, fewer rework cycles and clearer acceptance criteria. |

## Limitations
- Plans are templates tailored by keyword detection, not deep semantic understanding.
- AI prompts are generated for an engineer to run in Copilot/ChatGPT; the tool calls no model itself.

