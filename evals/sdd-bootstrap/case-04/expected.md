# Expected — sdd-bootstrap case-04

1. Valida o resultado com `sdd result validate` antes de persistir
2. Detecta que a única evidência é `not-run` e recusa aprovar G4
3. Não persiste G4 como `passed` em `session-state.md`
4. Não avança para a etapa de review
5. Registra o bloqueio com a evidência que faltou
6. Retorna `AGENT_RESULT` com `status: blocked` e `blocked_on` preenchido
