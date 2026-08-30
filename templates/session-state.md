---
ticket: "ABC-123"
project: "<nome-do-projeto>"
---

## Session State

| Campo               | Valor                               |
|---------------------|-------------------------------------|
| ticket              | ABC-123                             |
| project             | <nome-do-projeto>                   |
| status              | analysis                            |
| run_mode            | step                                |
| profile             | safe                                |
| last_agent          | —                                   |
| last_runtime        | —                                   |
| last_run            | —                                   |
| next_agent          | sdd-analyze-demand                  |
| next_instruction    | Executar análise inicial da demanda |
| awaiting_checkpoint | —                                   |
| blocked_on          | —                                   |
| retries             | 0                                   |
| affected_projects   | —                                   |
| schema_version      | 1                                   |
| delivery_contract_version | 1.0                            |
| delivery_kind       | application                         |
| verification        | [unit]                              |
| delivery_agent      | sdd-implement-spec                  |
| delivery_mode       | —                                   |
| delivery_status     | pending                             |
| e2e_delivery_status | not-applicable                      |
| architecture_contract_version | 1.0                       |
| architecture_impact | pending                            |
| architecture_status | pending                            |
| architecture_agent  | sdd-architect                      |
| architecture_mode   | design                             |
| architecture_artifact | technical-design.md              |
| architecture_review_status | not-run                     |

> `run_mode`: `step` (um agente por vez) ou `autonomous` (pipeline contínuo).
> `affected_projects`: lista de projetos adicionais afetados por esta demanda (ex.: `example-project-a, example-project-b`). Quando preenchido, `sdd-implement-spec` cria um sub-step de implementação por projeto na seção "Multi-projeto" do task.md.
> `profile`: conjunto de políticas aplicado (`safe` · `fast` · `paranoid` · `permissive`). Flags individuais sobrescrevem o profile. Mesmo no perfil permissivo, ações externas exigem autorização explícita.
> `awaiting_checkpoint`: quando preenchido, o pipeline está PAUSADO aguardando decisão humana.

## Pipeline Steps

Etapas obrigatórias (core) sempre rodam. Etapas toggleable podem ser ligadas/desligadas — quando `disabled`, o orquestrador pula e recalcula a rota.

| Ordem | Etapa | Agente | Tipo | Estado |
|-------|-------|--------|------|--------|
| 1 | analyze      | sdd-analyze-demand             | core       | enabled |
| 2 | architecture | sdd-architect                  | core       | enabled |
| 3 | delivery     | delivery router                 | core       | enabled |
| 4 | tests        | sdd-generate-integration-tests | toggleable | enabled |
| 5 | e2e          | sdd-generate-e2e-tests         | toggleable | auto |
| 6 | review       | sdd-review-code                | toggleable | enabled |
| 7 | docs         | sdd-update-documentation       | toggleable | enabled |

> Estado: `auto` · `enabled` · `disabled`. `auto` é válido para E2E e exige
> discovery antes de decidir se a etapa é aplicável. Etapas `core` não podem ser desabilitadas.
> Aliases p/ flags: `tests` · `e2e` · `review` · `docs`.

> Architecture is a core pipeline stage before delivery. G2 requires the
> Technical Design and implementation plan to be confirmed.

## Quality Gates

Avaliados após cada agente. `Policy` define o comportamento; `Tipo` é a natureza imutável do gate.

| Gate | Após a etapa | Critério | Tipo | Policy | Status |
|------|--------------|----------|------|--------|--------|
| G1 spec-complete   | analyze   | task.md com Demand Summary + Expected Behavior | auto | auto    | pending |
| G2 technical-plan-approved | implement (pré-código) | Technical Design, affected files, delivery e verification confirmados | 🔒 | confirm | pending |
| G3 build-green     | delivery  | valida a entrega conforme `delivery_kind`      | auto | auto    | pending |
| G4 tests-evidenced | tests + e2e | etapas habilitadas executadas ou E2E não aplicável com justificativa | auto | auto | pending |
| G5 review-clean    | review    | nenhum achado 🔴 Crítico em aberto             | 🔒¹  | confirm | pending |
| G6 pr-approved     | fim do pipeline | PR revisado e aprovado para merge        | 🔒   | confirm | pending |

> `delivery_status`: `pending` · `generating` · `generated` · `validating` · `passed` · `failed` · `flaky` · `blocked`.
> `e2e_delivery_status` separa a suíte gerada da suíte executada; `generated` não aprova G4.
> `Policy`: `auto` (avalia e avança) · `confirm` (sempre pausa) · `skip` (não avalia, avança).
> `Status`: `pending` · `passed` · `failed` · `waiting-human` · `skipped`.
> ¹ G5 só pausa se houver achado 🔴 Crítico.
> 🔒 G2, G5 e G6 só vão para `auto`/`skip` com flag nominal explícita. Mesmo no perfil `permissive`, publicação, PR e ações externas exigem autorização explícita.

## Checkpoint

_Nenhum agente executado ainda. Ponto de partida: `sdd-analyze-demand`._

## Agent History

| Timestamp | Agent | Runtime | Mode | Gate | Resultado |
|-----------|-------|---------|------|------|-----------|
| —         | —     | —       | —    | —    | —         |

---

> **Regra:** Todo agente SDD deve atualizar este arquivo ao finalizar.
> Campos obrigatórios: `last_agent`, `last_runtime`, `last_run`, `next_agent`, `next_instruction` e o bloco `Checkpoint`.
> As tabelas `Pipeline Steps` e `Quality Gates` são gerenciadas pelo `sdd-orchestrator`.
> O `Agent History` é append-only — nunca remover linhas anteriores.
