# Eval Input — sdd-implement-spec case-01
# Cenário: Context Pack com checkpoint humano pendente → deve parar e apresentar o plano

## Context Pack entregue pelo bootstrap
- `target_agent`: `sdd-implement-spec`
- `stage`: `delivery`
- `state.status`: `awaiting-checkpoint`
- `state.blocked_on`: `["CP1: aprovação humana do Technical Design"]`

## task.md (resumido)
```markdown
## Implementation Plan
### Step 1 — Criar o caso de uso de aprovação
### Step 2 — Implementar a validação de entrada
### Step 3 — Publicar o evento de domínio correspondente
### Step 4 — Adicionar teste unitário do caso de uso

## Affected Files
| File | Layer | Change |
|------|-------|--------|
| `<application>/AprovarMetaUseCase` | application | create |
| `<infrastructure>/AprovacaoMetaConsumer` | infrastructure | modify |
```
