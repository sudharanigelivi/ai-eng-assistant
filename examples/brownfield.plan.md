# Engineering plan: Fix the bug in the existing checkout service where duplicate orders are created.

- **Type:** brownfield  |  **Domain:** generic  |  **Ambiguity:** low

## Problem statement
Change existing behaviour safely: "Fix the bug in the existing checkout service where duplicate orders are created". Preserve public behaviour except where intentionally changed, proven by tests written before the change.

## Ambiguities and assumptions
| Term | Impact | Question | Working assumption |
|---|---|---|---|
| reproduction details | high | What is the expected vs actual behaviour and how is it reproduced? | The first task produces a failing test that defines expected behaviour. |

## Task breakdown (execution order; tasks in the same wave can run in parallel)

### Wave 1

**T1 - Understand existing behaviour and reproduce the issue** `[clarify]` depends on: none
- Deliverables: Reproduction steps or failing test; Affected modules list
- AI prompt: _Requirement: "Fix the bug in the existing checkout service where duplicate orders are created.". Given the relevant existing code, explain current behaviour, where it deviates from expectation, and how to reproduce it._
- AI does: Reads and explains unfamiliar code; suggests reproduction.
- Engineer owns: Confirms the explanation by running the code; never trusts it unverified.
- Validation: Issue reproduced locally; Expected behaviour agreed

### Wave 2

**T2 - Add characterization / failing tests first** `[test]` depends on: T1
- Deliverables: Test that fails for the bug or pins current behaviour
- AI prompt: _Write pytest tests that pin the current behaviour around "Fix the bug in the existing checkout service where duplicate orders are created." and one that fails for the reported defect._
- AI does: Generates tests quickly.
- Engineer owns: Confirms the new test fails for the right reason before any fix.
- Validation: Failing test fails on unchanged code; Existing suite is green

### Wave 3

**T3 - Design the smallest safe change** `[design]` depends on: T2
- Deliverables: Change plan; Compatibility and rollback notes
- AI prompt: _Propose the minimal change for "Fix the bug in the existing checkout service where duplicate orders are created." that preserves public behaviour; list alternatives and blast radius._
- AI does: Proposes options and enumerates impacted callers.
- Engineer owns: Chooses the option; verifies callers via search, not memory.
- Validation: API/schema compatibility explicitly checked

### Wave 4

**T4 - Implement the change / refactor** `[code]` depends on: T3
- Deliverables: Focused diff
- AI prompt: _Implement the planned change for "Fix the bug in the existing checkout service where duplicate orders are created." with a minimal diff. Do not alter unrelated code._
- AI does: Generates the diff.
- Engineer owns: Reads every changed line; rejects unrelated edits.
- Validation: Diff touches only planned modules

### Wave 5

**T5 - Regression and new-behaviour tests** `[test]` depends on: T4
- Deliverables: Passing new tests; Full suite green; Coverage delta
- AI prompt: _Extend tests for "Fix the bug in the existing checkout service where duplicate orders are created.": boundaries, error paths and regression guards for neighbouring behaviour._
- AI does: Suggests extra edge cases.
- Engineer owns: Checks coverage did not fall and tests are meaningful.
- Validation: Full suite passes; Coverage not reduced

**T6 - Update docs and changelog** `[docs]` depends on: T4
- Deliverables: Docs/changelog updates
- AI prompt: _Update documentation and changelog for the change described by "Fix the bug in the existing checkout service where duplicate orders are created."; list every doc that references the old behaviour._
- AI does: Finds and drafts doc updates.
- Engineer owns: Verifies accuracy against the code.
- Validation: No stale references to old behaviour

### Wave 6

**T7 - Review, rollout and rollback plan** `[review]` depends on: T5, T6
- Deliverables: Review notes; Rollback steps
- AI prompt: _Review the diff for "Fix the bug in the existing checkout service where duplicate orders are created." for regressions, security and performance impact; suggest a safe rollout._
- AI does: Independent review pass.
- Engineer owns: Owns release decision and rollback plan.
- Validation: Rollback tested or trivially reversible

## Risks and mitigations
| Kind | Risk | Mitigation |
|---|---|---|
| functional | Behavioural regression in code the change does not obviously touch. | Characterization tests before change; full suite must be green. |
| design | Hidden callers depend on current (buggy) behaviour. | Search for all usages; communicate behaviour changes in the changelog. |
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

