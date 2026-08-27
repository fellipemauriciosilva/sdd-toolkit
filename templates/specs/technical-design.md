# Technical Design: [TICKET — título]

## Architecture Contract

| Field | Value |
|-------|-------|
| schema_version | 1 |
| architecture_contract_version | 1.0 |
| architecture_impact | low / medium / high |
| architecture_status | designed |
| architecture_agent | sdd-architect |
| architecture_mode | design |
| architecture_artifact | technical-design.md |
| full_design_required | true / false |
| rationale | TODO — justificativa baseada em evidências |
| decisions | TODO / none |
| required_evidence | payload.architecture |

## Context and Constraints

TODO — problema técnico, objetivos, restrições existentes e documentos/ADRs
consultados. Marque cada conclusão como `confirmed`, `inferred` ou `unknown`.

## Current Architecture

TODO — componentes, módulos, dependências, fronteiras e fluxos afetados.

## Proposed Design

TODO — solução mínima proporcional, responsabilidades, sequência de execução e
contratos entre componentes.

## Interfaces and Contracts

TODO — API, eventos, mensagens, erros, versionamento, compatibilidade e
idempotência.

## Data and Migration

TODO — entidades, schema, índices, backfill, concorrência, retenção e rollback.
Use `not-applicable` com justificativa quando não houver persistência.

## Security and Privacy

TODO — autenticação, autorização, trust boundaries, dados pessoais, secrets,
abuso e requisitos de conformidade.

## Reliability and Operations

TODO — timeout, retry, duplicidade, falha parcial, disponibilidade, logs,
métricas, traces, alertas e runbook.

## Non-Functional Requirements

| Requirement | Target | Measurement | Evidence |
|-------------|--------|-------------|----------|
| Performance | TODO / not-applicable | TODO | TODO |
| Availability | TODO / not-applicable | TODO | TODO |
| Security | TODO | TODO | TODO |

## Alternatives and Trade-offs

| Option | Benefits | Costs/Risks | Decision |
|--------|----------|-------------|----------|
| TODO | TODO | TODO | chosen / rejected |

## Rollout and Rollback

TODO — ordem de publicação, feature flag, coexistência, migração, observação,
critério de abortar e passos de reversão.

## Test Strategy

TODO — riscos cobertos por testes unitários, integração, contrato e E2E. Não
confunda geração de uma suíte E2E com sua execução.

## Open Questions and Gaps

- [ ] TODO — pergunta, responsável e condição para desbloqueio

## Approval and Review

| Check | Status | Evidence |
|-------|--------|----------|
| Technical Design reviewed | pending | TODO |
| ADRs created/updated | pending / not-required | TODO |
| G2 approved | pending | TODO |
| Post-delivery architecture review | pending | TODO |

## Decisions Log

<!-- Append decisions; never rewrite historical entries. -->
