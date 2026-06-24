---
ticket: "JT-XXXX"
project: "<nome-do-projeto>"
---

## Session State

| Campo               | Valor                               |
|---------------------|-------------------------------------|
| ticket              | JT-XXXX                             |
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

> `run_mode`: `step` (um agente por vez) ou `autonomous` (pipeline contínuo).
> `affected_projects`: lista de projetos adicionais afetados por esta demanda (ex.: `gcb-project-a, gcb-project-b`). Quando preenchido, `sdd-implement-spec` cria um sub-step de implementação por projeto na seção "Multi-projeto" do task.md.
> `profile`: conjunto de políticas aplicado (`safe` · `fast` · `paranoid` · `yolo`). Flags individuais sobrescrevem o profile.
> `awaiting_checkpoint`: quando preenchido, o pipeline está PAUSADO aguardando decisão humana.

## Pipeline Steps

Etapas obrigatórias (core) sempre rodam. Etapas toggleable podem ser ligadas/desligadas — quando `disabled`, o orquestrador pula e recalcula a rota.

| Ordem | Etapa | Agente | Tipo | Estado |
|-------|-------|--------|------|--------|
| 1 | analyze   | sdd-analyze-demand             | core      | enabled |
| 2 | implement | sdd-implement-spec             | core      | enabled |
| 3 | tests     | sdd-generate-integration-tests | toggleable | enabled |
| 4 | review    | sdd-review-code                | toggleable | enabled |
| 5 | docs      | sdd-update-documentation       | toggleable | enabled |

> Estado: `enabled` · `disabled`. Etapas `core` não podem ser desabilitadas.
> Aliases p/ flags: `tests` · `review` · `docs`.

## Quality Gates

Avaliados após cada agente. `Policy` define o comportamento; `Tipo` é a natureza imutável do gate.

| Gate | Após a etapa | Critério | Tipo | Policy | Status |
|------|--------------|----------|------|--------|--------|
| G1 spec-complete   | analyze   | task.md com Demand Summary + Expected Behavior | auto | auto    | pending |
| G2 plan-approved   | implement (pré-código) | Implementation Plan confirmado     | 🔒   | confirm | pending |
| G3 build-green     | implement | compila + testes unitários passam              | auto | auto    | pending |
| G4 tests-present   | tests     | testes gerados ou skip justificado             | auto | auto    | pending |
| G5 review-clean    | review    | nenhum achado 🔴 Crítico em aberto             | 🔒¹  | confirm | pending |
| G6 pr-approved     | fim do pipeline | PR revisado e aprovado para merge        | 🔒   | confirm | pending |

> `Policy`: `auto` (avalia e avança) · `confirm` (sempre pausa) · `skip` (não avalia, avança).
> `Status`: `pending` · `passed` · `failed` · `waiting-human` · `skipped`.
> ¹ G5 só pausa se houver achado 🔴 Crítico.
> 🔒 G2, G5 e G6 só vão para `auto`/`skip` com flag nominal explícita (`--auto=G6`) ou `--profile=yolo`.

## Checkpoint

_Nenhum agente executado ainda. Ponto de partida: `sdd-analyze-demand`._

## Agent History

| Timestamp | Agent | Runtime | Mode | Gate | Resultado |
|-----------|-------|---------|------|------|-----------|
| —         | —     | —       | —    | —    | —         |

---

> **Regra:** Todo agente SDD deve atualizar este arquivo ao finalizar.
> Campos obrigatórios: `last_agent`, `last_runtime`, `last_run`, `next_agent`, `next_instruction` e o bloco `Checkpoint`.
> As tabelas `Pipeline Steps` e `Quality Gates` são gerenciadas pelo `sdd-bootstrap`.
> O `Agent History` é append-only — nunca remover linhas anteriores.
