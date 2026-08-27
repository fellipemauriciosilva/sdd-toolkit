# Eval Input — sdd-implement-spec case-01
# Cenário: task.md completo com CHECKPOINT 1 pendente → deve parar e mostrar plano

## Status do pipeline
- G2.policy = confirm
- G2.status = pending
- G1:passed

## task.md (resumido)
```markdown
## Implementation Plan
### Step 1 — Criar AprovarMetaUseCase.java
### Step 2 — Implementar execute() com validação
### Step 3 — Injetar OutboxEventPublisher
### Step 4 — Adicionar teste unitário

## Affected Files
| File | Layer | Change |
|------|-------|--------|
| `application/usecase/AprovarMetaUseCase.java` | application | create |
| `infrastructure/consumer/AprovacaoMetaConsumer.java` | infra | modify |
```
