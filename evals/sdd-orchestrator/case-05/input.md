# Eval Input — sdd-orchestrator case-05
# Cenário: Projeto ainda não ativado → confirmar e ativar sem sair do runtime

## Invocação
```
/sdd-orchestrator ABC-5005 --run
```

## Estado do sistema
- O comando `sdd` existe no PATH e responde `--version`
- `sdd context resolve --ticket ABC-5005 --runtime auto --json` devolve:

```json
{
  "status": "unactivated",
  "project": {"path": "/workspace/exemplo-servico"},
  "workspace": "/home/<user>/sdd-history-implementations/exemplo-servico-ab12cd34/exemplo-servico/specs",
  "runtime": "auto",
  "activation_state": "/home/<user>/.local/SDD-Toolkit/user/activations.json"
}
```

- Não existe registro de ativação para este projeto
- O usuário pediu para iniciar a demanda direto pelo chat do runtime

## Contexto adicional
- `sdd start ABC-5005 --yes --json` ativa o projeto e devolve o handoff numa
  única chamada
- `sdd activate --json` cobre o pedido de ativação sem ticket
- A ativação grava somente no perfil do usuário: `writes_project: false`
