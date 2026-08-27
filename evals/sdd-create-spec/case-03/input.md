# Eval Input — sdd-create-spec case-03
# Cenário: Ticket com descrição → cria spec.md opcional

## Invocação
```
/sdd-create-spec ABC-4567 --type=bugfix --description="Meta duplicada ao aprovar duas vezes"
```

## Contexto
- `SPEC_PATH` ainda não existe para ABC-4567
- Nenhum critério de aceite foi informado pelo usuário
