# Expected — sdd-generate-integration-tests case-02

1. Detecta pelo pack que a etapa de testes está desabilitada
2. Não gera nenhum arquivo de teste
3. Não atualiza `session-state.md` nem qualquer arquivo de estado
4. Retorna `AGENT_RESULT` com `status: not-applicable` e `payload.integration`
   registrando o motivo do skip e `next_agent: sdd-orchestrator`
5. Registrar a etapa como pulada e avaliar G4 é responsabilidade do orquestrador
