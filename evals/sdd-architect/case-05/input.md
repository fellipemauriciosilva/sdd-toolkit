# Eval Input — sdd-architect case-05
# Cenário: Demanda greenfield — decidir a fundação sem base de evidência

## Invocação
```
/sdd-architect ABC-5050 --mode design
```

## Contexto resolvido
- `PROJECT_PATH` aponta para um diretório vazio, sem arquivo de build, sem
  código e sem histórico
- `SPEC_PATH/task.md` existe com `Type: greenfield` e a tabela Foundation
  Decision com todas as linhas em `TODO` e `decision status: pending`
- `sdd architecture validate --task <SPEC_PATH>/task.md --json` devolve
  `architecture_impact: high` e `full_design_required: true`

## Demanda registrada no task.md
- Objetivo: expor um serviço que recebe pedidos de cobrança e devolve o status
  de processamento
- Restrição declarada pelo usuário: a equipe opera hoje somente em ambientes
  Linux com contêineres
- Volume esperado: desconhecido, registrado como `unknown`
- Prazo: não informado

## Contexto adicional
- O usuário não declarou linguagem nem framework
- Nenhuma decisão anterior existe em `technical-design.md`
