# Expected — sdd-refactor-code case-03

1. Identifica que renomear campos de resposta altera contrato público
2. Não altera dependência nem versão de biblioteca
3. Não remove campo sem evidência de que não há consumidor
4. Bloqueia e devolve a decisão ao `sdd-architect`
5. Executa apenas a parte que preserva comportamento, se houver
6. Retorna `AGENT_RESULT` com `status: blocked` e `blocked_on` preenchido
