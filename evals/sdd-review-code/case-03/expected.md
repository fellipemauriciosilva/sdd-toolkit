# Expected — sdd-review-code case-03

1. Detecta pelo pack que a etapa de review está desabilitada
2. Não lê nenhum arquivo de código em `PROJECT_PATH`
3. Não atualiza estado nem declara G5 — o bootstrap persiste o gate
4. Retorna `AGENT_RESULT` com `status: not-applicable`, `payload.review`
   registrando o motivo do skip e `next_agent: sdd-bootstrap`
