# Task: [MIGR-XXXX — Migration Description]

## Identification

| Field | Value |
|-------|-------|
| Ticket | MIGR-XXXX |
| Type | migration |
| Priority | TODO |
| Status | analysis |
| Wave / Onda | TODO (Onda 0 / Onda 1 / etc.) |
| Source system | TODO (ex.: EAR/DB2/JBoss) |
| Target system | TODO (ex.: Spring Boot 3.3 + Java 21 + PostgreSQL) |

---

## Migration Scope

TODO — what exactly is being migrated in this ticket/wave. Bounded contexts, layers, components.

## Pre-conditions

TODO — what must be true before this migration can start.
(Previous wave complete? Schema migrated? Infra available?)

## Current State (Source)

TODO — describe the legacy system component being migrated.
Include: class names, DB tables, message topics, external integrations.

## Target State

TODO — describe what the migrated component should look like.
Include: new class names, new DB tables/Flyway migrations, new topics, hexagonal boundaries.

## Delivery Strategy

| Field | Value |
|-------|-------|
| schema_version | 1 |
| delivery_contract_version | 1.0 |
| delivery_kind | migration |
| verification | [integration] |
| rationale | Migration delivery requires integration and data-integrity evidence. |
| owner | `sdd-analyze-demand` |
| expected_evidence | [DELIVERY_RESULT, INTEGRATION_RESULT] |

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
| rationale | TODO — consolidar a arquitetura alvo e a estratégia de coexistência |
| decisions | none |
| required_evidence | ARCHITECTURE_RESULT |

## Affected Files

| File | Layer | Change |
|------|-------|--------|
| `legacy/OldClass.java` | — | delete |
| `domain/model/NewEntity.java` | domain | create |

## Migration Plan

### Step 1 — TODO

### Step 2 — TODO

### Step 3 — Validate (run build + check data integrity)

## Data Migration

TODO — describe any data migration needed (Flyway scripts, backfill jobs, data transformations).

| Script | Description |
|--------|-------------|
| `V00XX__migrate_table.sql` | TODO |

## Tests to Add / Update

| Test class | Scenario |
|-----------|---------|
| `NewComponentTest` | data migrated correctly / backward compat |

## Rollback Plan

TODO — how to roll back if the migration fails in production.

## Phase Gates

| Gate | Criterion | Responsible |
|------|-----------|-------------|
| Build passes | `./mvnw clean test` green | sdd-bootstrap G3 |
| Data integrity | TODO | manual check |
| Integration smoke | TODO | team |

## ADRs Referenced

- [ ] TODO — list relevant ADRs or architecture records resolved for this project

## Risks

- RISK: TODO
- ASSUMPTION: TODO

## Open Questions

- [ ] TODO

## Decisions Made

<!-- Fill as decisions are taken during implementation -->
