# Expected — sdd-update-documentation case-02

1. Detecta pelo pack que a etapa de documentação está desabilitada
2. Não modifica nenhum documento em `SPEC_PATH` nem em `PROJECT_PATH`
3. Não atualiza `session-state.md` nem qualquer arquivo de estado
4. Retorna `AGENT_RESULT` com `status: not-applicable` e `payload.documentation`
   justificando o skip, com `next_agent: sdd-bootstrap`
5. Registrar a etapa como pulada e avaliar G6 é responsabilidade do bootstrap
