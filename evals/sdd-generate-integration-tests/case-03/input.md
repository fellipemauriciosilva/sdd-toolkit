# Eval Input — sdd-generate-integration-tests case-03
# Cenário: consumidor de eventos → gera testes contra o broker real em container

## task.md — Affected Files
- `AuditoriaEventConsumer` — novo consumidor do tópico `auditoria.eventos`

## Contexto descoberto no projeto
- A suíte de integração já usa containers efêmeros para dependências reais
- Tópico: `auditoria.eventos`
- Contrato de mensagem definido no `task.md`: `{ "tipo": "ACESSO", "userId": "<id>" }`
