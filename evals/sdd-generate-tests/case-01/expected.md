# Expected — sdd-generate-tests case-01

1. Descobre linguagem, framework e comando de teste existentes por evidência
2. Mapeia cada teste criado a um critério de aceite ou risco confirmado
3. Cria testes apenas no diretório de testes do projeto, com as convenções existentes
4. Executa o menor comando de teste aplicável e reporta o resultado real
5. Separa falhas preexistentes das introduzidas
6. Retorna `AGENT_RESULT` com `payload.unit` e `next_agent: sdd-orchestrator`
