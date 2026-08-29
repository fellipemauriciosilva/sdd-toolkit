# Task: [ABC-123 — New Project Name]

## Identification

| Field | Value |
|-------|-------|
| Ticket | ABC-123 |
| Type | greenfield |
| Priority | TODO |
| Status | analysis |

---

## Demand Summary

TODO — one paragraph describing what is being created from scratch and why it
does not belong in an existing project.

## Current Behavior

Nothing exists yet. Record here what is done today instead — a manual process,
another system, or nothing at all — so the demand has a baseline.

## Expected Behavior

TODO — what the new project must do to be considered delivered.
Include acceptance criteria when available.

## Foundation Decision

Owned by `sdd-architect`. Nothing here may be filled by convention or default;
every row needs a justification recorded in `technical-design.md`.

| Field | Value |
|-------|-------|
| language | TODO |
| framework | TODO |
| build tool | TODO |
| test framework | TODO |
| project layout | TODO |
| stack skill | TODO — skill that governs implementation |
| decision status | pending |

## Delivery Strategy

| Field | Value |
|-------|-------|
| schema_version | 1 |
| delivery_contract_version | 1.0 |
| delivery_kind | application |
| verification | [unit] |
| rationale | A new project is delivered by `sdd-implement-spec` as a minimum viable skeleton; verification is defined by `sdd-analyze-demand`. |
| owner | `sdd-analyze-demand` |
| expected_evidence | [payload.delivery, payload.unit] |

## Architecture Strategy

| Field | Value |
|-------|-------|
| schema_version | 1 |
| architecture_contract_version | 1.0 |
| architecture_impact | high |
| architecture_status | pending |
| architecture_agent | `sdd-architect` |
| architecture_mode | design |
| architecture_artifact | `technical-design.md` |
| full_design_required | true |
| rationale | A fundação define linguagem, estrutura e build sem base de evidência no repositório e não é revertida na prática. |
| decisions | none |
| required_evidence | payload.architecture |

## Scope Boundaries

| In scope | Out of scope |
|----------|--------------|
| TODO | TODO |

TODO — a first delivery that tries to cover everything has no verifiable end.
Record what is deliberately deferred to a later demand.

## Skeleton Contents

| Artifact | Purpose |
|----------|---------|
| `TODO` | build / dependency manifest |
| `TODO` | first executable entry point |
| `TODO` | first test proving the harness runs |

## Entry Point

TODO — how the new project is started or invoked (API, CLI, job, UI, library).

## Integrations

TODO — external systems this project must reach, and what is unknown about
each one. Do not assume protocol, auth or availability.

## Implementation Plan

### Step 1 — TODO

### Step 2 — TODO

## Tests to Add / Update

| Test class | Scenario |
|-----------|---------|
| `TODO` | first passing test that proves the build and test harness work |

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
