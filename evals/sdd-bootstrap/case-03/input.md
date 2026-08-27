# Eval Input — sdd-bootstrap case-03
# Cenário: Ticket sem spec criada → orientar sdd-create-spec e encerrar

## Invocação
```
/sdd-bootstrap ABC-9999 --run
```

## Estado do sistema
- `sdd context resolve --ticket ABC-9999 --runtime auto --json` resolve o
  workspace, mas `SPEC_PATH` não existe
- Não há `task.md` nem `session-state.md` para ABC-9999

## Contexto adicional
- O projeto está ativado para trabalho SDD user-scoped
- Nenhuma spec foi criada para ABC-9999
