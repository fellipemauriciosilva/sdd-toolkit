# Expected — sdd-refactor-code case-01

1. Declara os comportamentos e contratos que devem ser preservados
2. Estabelece baseline de build/testes antes do primeiro edit
3. Faz alterações pequenas e reversíveis, restritas aos arquivos aprovados
4. Executa os testes relevantes após cada bloco coerente
5. Não altera API, schema, eventos, dependências nem regra de negócio
6. Retorna `AGENT_RESULT` com `payload.delivery` e `next_agent: sdd-bootstrap`
