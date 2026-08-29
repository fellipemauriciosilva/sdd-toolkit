# Expected — sdd-generate-integration-tests case-01

1. Faz discovery do framework já adotado em vez de presumir um
2. Gera cenários de happy path, recurso inexistente e requisição inválida
3. Segue o padrão dos step definitions existentes
4. Mantém o mock de dependências externas e os containers já usados no projeto
5. Não declara G4: retorna `AGENT_RESULT` com `payload.integration` informando
   `delivery_status: generated`, o comando de execução e `next_agent: sdd-bootstrap`
6. Geração não é execução — a evidência de execução é um resultado distinto
