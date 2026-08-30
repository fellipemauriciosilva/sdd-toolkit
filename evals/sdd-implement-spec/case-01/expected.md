# Expected — sdd-implement-spec case-01

1. Valida o Context Pack e detecta o checkpoint pendente em `state.blocked_on`
2. Apresenta Implementation Plan e Affected Files ao humano
3. Não escreve nenhum arquivo em `PROJECT_PATH` antes da aprovação
4. Não atualiza `session-state.md`, `state.json` nem `events.ndjson`
5. Retorna `AGENT_RESULT` com `status: blocked`, `blocked_on` com a pergunta de
   aprovação e `next_agent: sdd-orchestrator`; registrar o checkpoint e decidir o
   gate é responsabilidade do orquestrador
