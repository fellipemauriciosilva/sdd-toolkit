# Eval Input — sdd-analyze-demand case-01
# Cenário: Demanda bem especificada com contexto completo → G1 deve passar

## Contexto
- Projeto: example-api-gestao-meta
- Ticket: ABC-1234
- Spec: task.md com Demand Summary e Expected Behavior preenchidos
- Docs de referência: `.github/docs/migration/STATUS-ONDA-0.md` existe

## task.md atual
```markdown
## Demand Summary
Implementar o Use Case `AprovarMetaUseCase` que processa aprovações de metas
de desempenho via Kafka consumer `AprovacaoMetaConsumer`.

## Expected Behavior
Quando mensagem `meta.aprovada` chega no tópico Kafka, o sistema deve:
1. Validar UUID da meta
2. Atualizar status para APROVADA no banco
3. Publicar evento `MetaAprovadaEvent` no outbox
```

## Código existente relevante
- `MetaRepository.java` — método `findById(UUID)` já existe
- `OutboxEventPublisher.java` — método `publish(String, Object)` existe
- Nenhum `AprovarMetaUseCase.java` no projeto ainda
