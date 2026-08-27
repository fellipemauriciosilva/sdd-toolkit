# Eval Input — sdd-generate-tests case-02
# Cenário: Stack de teste desconhecida → bloqueio em vez de escolha padrão

## Invocação
```
/sdd-generate-tests ABC-3202
```

## Contexto
- O projeto não tem diretório de testes nem comando de teste declarado
- O manifesto de build não indica um framework de teste
- `task.md` pede "cobertura de testes para a nova regra"
