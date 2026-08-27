# Eval Input — sdd-generate-integration-tests case-03
# Cenário: Kafka consumer → gera testes com Testcontainers Kafka

## task.md — Affected Files
- `AuditoriaEventConsumer.java` — novo consumer do tópico `auditoria.eventos`

## Contexto
- Framework: Testcontainers com KafkaContainer
- Tópico: `auditoria.eventos`
- Mensagem: JSON `{ "tipo": "ACESSO", "userId": "uuid" }`
