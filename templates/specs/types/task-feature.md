# Task: [ABC-123 — Feature Name]

## Identification

| Field | Value |
|-------|-------|
| Ticket | ABC-123 |
| Type | feature |
| Priority | TODO |
| Status | analysis |

---

## Demand Summary

TODO — one paragraph describing what new capability is being added and why.

## Current Behavior

TODO — how the system works today without this feature.

## Expected Behavior

TODO — how the system should behave after this feature is implemented.
Include acceptance criteria when available.

## Delivery Strategy

| Field | Value |
|-------|-------|
| schema_version | 1 |
| delivery_contract_version | 1.0 |
| delivery_kind | application |
| verification | [unit] |
| rationale | Application behavior is implemented by `sdd-implement-spec`; verification is defined by `sdd-analyze-demand`. |
| owner | `sdd-analyze-demand` |
| expected_evidence | [payload.delivery, payload.unit] |

## Architecture Strategy

| Field | Value |
|-------|-------|
| schema_version | 1 |
| architecture_contract_version | 1.0 |
| architecture_impact | medium |
| architecture_status | pending |
| architecture_agent | `sdd-architect` |
| architecture_mode | design |
| architecture_artifact | `technical-design.md` |
| full_design_required | true |
| rationale | TODO — classificar impacto após discovery técnico |
| decisions | none |
| required_evidence | payload.architecture |

## Affected Files

| File | Layer | Change |
|------|-------|--------|
| `path/to/affected-component` | application | create / modify |

## Entry Point

TODO — where does this feature start? (API, message, scheduler, UI action, CLI, etc.)

## Flow Analysis

TODO — step-by-step of the relevant flow that will be created or modified.

## Implementation Plan

### Step 1 — TODO

### Step 2 — TODO

## Tests to Add / Update

| Test class | Scenario |
|-----------|---------|
| `SomeServiceTest` | happy path / validation error / edge case |

## Non-Functional Requirements

- Performance: TODO
- Security: TODO
- Observability (logs/metrics): TODO

## Risks and Assumptions

- RISK: TODO
- ASSUMPTION: TODO

## Open Questions

- [ ] TODO

## Decisions Made

<!-- Fill as decisions are taken during implementation -->
