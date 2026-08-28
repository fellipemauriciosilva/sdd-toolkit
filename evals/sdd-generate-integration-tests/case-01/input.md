# Eval Input — sdd-generate-integration-tests case-01
# Cenário: Endpoint REST novo → gera testes de integração no framework já adotado

## task.md — Affected Files
- `CompetenciaController` — novo endpoint `GET /competencias/{id}`

## Contexto descoberto no projeto
- Suíte de integração já existente, com mock de dependências externas e
  containers efêmeros para o banco
- Pasta de testes de integração já definida pela convenção do repositório
- Step definitions existentes em `CompetenciaSteps`
