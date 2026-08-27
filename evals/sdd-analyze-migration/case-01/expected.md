# Expected — sdd-analyze-migration case-01

1. Resolve o contexto pela CLI e deriva `PROJECT_PATH`, `SDD_WORKSPACE`, `SPEC_PATH` e `RUNTIME`
2. Inventaria apenas o que tem evidência em `PROJECT_PATH` e nos anexos
3. Registra para cada achado o caminho, o método de detecção e a confiança (`confirmed`, `inferred`, `unknown`)
4. Escreve `migration-analysis.md` em `SPEC_PATH` com escopo, riscos, coexistência, ondas, rollback e perguntas
5. Não escolhe stack alvo: encaminha a decisão estrutural ao `sdd-architect`
6. Retorna `AGENT_RESULT` com `payload.migration_analysis` e `next_agent: sdd-architect`
