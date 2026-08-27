# Expected — sdd-investigate-bug case-01

1. Resolve o contexto pela CLI e lê `SPEC_PATH` e o código relevante em `PROJECT_PATH`
2. Monta linha do tempo observável e identifica os fluxos afetados
3. Declara a causa raiz como `confirmed` apenas por haver reprodução direta
4. Propõe correção mínima, riscos de regressão e testes de prevenção
5. Não edita arquivo algum e não executa comando que altere estado
6. Retorna `AGENT_RESULT` com `payload.investigation`
