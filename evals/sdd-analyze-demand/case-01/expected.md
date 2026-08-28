# Expected — sdd-analyze-demand case-01

1. Lê `task.md` e identifica Demand Summary e Expected Behavior preenchidos
2. Analisa o contexto disponível sem presumir framework, broker ou banco
3. Preenche "Entry Point" com o consumidor de eventos declarado na demanda
4. Preenche "Affected Files" com a lista de arquivos a criar ou modificar
5. Preenche "Flow Analysis" com o fluxo evento → caso de uso → repositório → outbox
6. Preenche "Implementation Plan" com passos concretos
7. Atualiza somente `task.md`; não toca em `session-state.md`
8. Não declara G1 aprovado: retorna `AGENT_RESULT` com `payload.analysis`,
   evidências e `next_agent: sdd-architect`, e o bootstrap avalia o gate
