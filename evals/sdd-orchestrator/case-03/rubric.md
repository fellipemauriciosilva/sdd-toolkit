# Rubric — sdd-orchestrator case-03 (Spec inexistente)

## Critérios de Avaliação

| # | Critério | Peso | Resultado |
|---|----------|------|-----------|
| 1 | Resolveu o contexto pela CLI antes de agir | 20 | ✓/✗ |
| 2 | Verificou `task.md` e `session-state.md` no `SPEC_PATH` resolvido | 15 | ✓/✗ |
| 3 | Orientou `/sdd-create-spec` com o ticket correto | 30 | ✓/✗ |
| 4 | Encerrou sem executar nenhum agente e sem criar arquivos | 20 | ✓/✗ |
| 5 | Retornou `AGENT_RESULT` `blocked` com `blocked_on` preenchido | 15 | ✓/✗ |

## Score
`(soma dos pesos dos critérios ✓) / 100 × 100 = N%`

## Threshold
Score ≥ 85 = PASSOU | Score < 85 = FALHOU

Procurar artefato legado (`tasks.md`, `status-task.md`) = score 0
