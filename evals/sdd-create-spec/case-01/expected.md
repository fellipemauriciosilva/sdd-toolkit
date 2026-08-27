# Expected — sdd-create-spec case-01

1. Resolve o contexto com `sdd context resolve --ticket ABC-2345 --runtime auto --json`
   e deriva `PROJECT_PATH`, `SDD_WORKSPACE`, `SPEC_PATH` e `RUNTIME`
2. Cria `SPEC_PATH` e a subpasta `test-case/`
3. Cria `task.md` a partir do template de `feature`, com apenas Identification
   preenchido (Ticket=ABC-2345, Type=feature, Status=analysis)
4. Cria `session-state.md` a partir do template canônico, com ticket e project
5. Não cria `tasks.md` nem `status-task.md`: eles não fazem parte do contrato
6. Não declara G1 aprovado e não altera `session-state.md` como orquestrador
7. Retorna `AGENT_RESULT` com `status: completed`, `payload.scaffold` e
   `next_agent: sdd-analyze-demand`
8. NÃO analisa código, NÃO preenche Demand Summary
