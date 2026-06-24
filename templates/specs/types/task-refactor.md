# Task: [JT-XXXX — Refactor Description]

## Identification

| Field | Value |
|-------|-------|
| Ticket | JT-XXXX |
| Type | refactor |
| Priority | TODO |
| Status | analysis |

---

## Motivation

TODO — why is this refactor needed? (technical debt, performance, maintainability, compliance, etc.)

## Current Problems

TODO — specific problems with the current implementation.
List observable issues: slow builds, high coupling, test fragility, violation of architecture rules, etc.

## Current Behavior (to be preserved)

TODO — what behavior must remain identical after the refactor? (public contracts, API responses, message schemas)

## Proposed Architecture / Approach

TODO — describe the target state after refactor.
Include patterns to apply (e.g.: Extract Service, Replace Inheritance with Composition, Introduce Port/Adapter).

## Affected Files

| File | Layer | Change |
|------|-------|--------|
| `path/to/Class.java` | application | refactor |

## Implementation Plan

### Step 1 — TODO

## Tests to Add / Update

| Test class | Scenario |
|-----------|---------|
| `SomeServiceTest` | same behavior, cleaner implementation |

## Compatibility Constraints

TODO — what must NOT change:
- Public API contracts: TODO
- Database schema: TODO
- Kafka message format: TODO
- External service calls: TODO

## Rollback Strategy

TODO — if the refactor breaks something in production, how do we roll back quickly?

## Risks

- RISK: TODO (breaking change in contract not yet identified?)
- ASSUMPTION: TODO

## Open Questions

- [ ] TODO

## Decisions Made

<!-- Fill as decisions are taken during implementation -->
