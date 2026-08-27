# Expected — sdd-create-spec case-03

1. Cria o scaffold canônico: `SPEC_PATH`, `test-case/`, `task.md` e `session-state.md`
2. Cria `spec.md` com a descrição literal fornecida pelo usuário
3. Não cria `acceptance-criteria.md`, porque nenhum critério foi informado
4. `task.md` Identification tem Type=bugfix e Status=analysis
5. Não preenche Demand Summary: isso é responsabilidade do `sdd-analyze-demand`
6. Retorna `AGENT_RESULT` com `payload.scaffold` e `next_agent: sdd-analyze-demand`
