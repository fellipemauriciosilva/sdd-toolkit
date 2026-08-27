# Rubric — sdd-create-spec case-01

| # | Critério | Peso | Resultado |
|---|----------|------|-----------|
| 1 | Resolveu o contexto pela CLI em vez de adivinhar caminhos | 15 | ✓/✗ |
| 2 | Criou `SPEC_PATH`, `test-case/`, `task.md` e `session-state.md` | 25 | ✓/✗ |
| 3 | `task.md` tem APENAS Identification preenchido | 20 | ✓/✗ |
| 4 | Não criou `tasks.md` nem `status-task.md` | 15 | ✓/✗ |
| 5 | Retornou `AGENT_RESULT` com `payload.scaffold` e `next_agent` correto | 15 | ✓/✗ |
| 6 | Não analisou código nem preencheu Demand Summary | 10 | ✓/✗ |

Threshold: ≥ 90 = PASSOU
Critérios 4 e 6 são bloqueantes — artefato legado ou análise de código = score 0
