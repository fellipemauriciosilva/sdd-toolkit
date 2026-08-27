# Task: [E2E-XXXX — Jornada de usuário]

## Identification

| Field | Value |
|-------|-------|
| Ticket | E2E-XXXX |
| Type | test-e2e |
| Priority | TODO |
| Status | analysis |

## Demand Summary

TODO — descreva a jornada de navegador que precisa ser entregue como suíte E2E.

## Delivery Strategy

| Field | Value |
|-------|-------|
| schema_version | 1 |
| delivery_contract_version | 1.0 |
| delivery_kind | e2e-tests |
| verification | e2e |
| owner | sdd-analyze-demand |
| rationale | TODO — por que a suíte E2E é a entrega desta demanda? |
| expected_evidence | DELIVERY_RESULT, E2E_RESULT |

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
| rationale | TODO — confirmar boundaries, ambiente, auth e dados da jornada |
| decisions | none |
| required_evidence | ARCHITECTURE_RESULT |

## User Journeys

| Journey | Persona | Entry point | Expected outcome |
|---------|---------|-------------|------------------|
| TODO | TODO | TODO | TODO |

## Environment and Data

- Base URL/start command: TODO
- Browser projects: TODO
- Authentication strategy: TODO — use somente referências de secrets, nunca valores
- Test data/fixtures: TODO
- Readiness/cleanup: TODO

## Acceptance Criteria

- [ ] TODO — critério observável da jornada

## Affected Test Files

| File | Change |
|------|--------|
| `e2e/` ou diretório existente | create / modify |

## Risks and Open Questions

- RISK: TODO
- [ ] Existe Cypress/WebdriverIO/Selenium que deve ser preservado?
- [ ] O ambiente de execução é local, CI ou ambos?

## Decisions Made

<!-- Decisões devem ser registradas pelo agente de análise e aprovadas quando necessário. -->
