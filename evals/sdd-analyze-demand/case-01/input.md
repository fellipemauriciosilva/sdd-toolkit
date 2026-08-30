# Eval Input — sdd-analyze-demand case-01
# Cenário: Demanda bem especificada com contexto completo → análise suficiente para o orquestrador avaliar G1

## Contexto
- Projeto: `example-api-gestao-meta`
- Ticket: `ABC-1234`
- Spec: `task.md` com Demand Summary e Expected Behavior preenchidos

## task.md atual
```markdown
## Demand Summary
Implementar o caso de uso `AprovarMetaUseCase`, que processa aprovações de metas
de desempenho recebidas por um consumidor de eventos.

## Expected Behavior
Quando a mensagem `meta.aprovada` chega no tópico de eventos, o sistema deve:
1. Validar o identificador da meta
2. Atualizar o status para APROVADA no repositório
3. Publicar o evento `MetaAprovadaEvent` no outbox
```

## Código existente relevante
- `MetaRepository` — operação de busca por identificador já existe
- `OutboxEventPublisher` — operação de publicação já existe
- Nenhum `AprovarMetaUseCase` no projeto ainda
