---
mode: agent
author: "Felipe Maurício da Silva"
description: "Gera e valida testes de integração no projeto consumidor, seguindo o stack, contratos e convenções já existentes."
model: "Claude Sonnet 4.6"
capabilities: "read,write,terminal"
tools:
  - search/fileSearch
  - search/textSearch
  - edit/editFiles
  - edit/createFile
  - execute/runInTerminal
  - execute/getTerminalOutput
version: "3.2.0"
---

> **Autor:** Felipe Maurício da Silva · **E-mail:** fellipemauriciosilva@gmail.com · **LinkedIn:** https://www.linkedin.com/in/felipe-mauricio-06685735/

# SDD Generate Integration Tests

Gere testes de integração no **projeto consumidor aberto**, sem assumir nome de
repositório, linguagem, framework, banco, infraestrutura ou ferramenta de
teste. Esta etapa valida fronteiras entre componentes — por exemplo HTTP,
mensageria, persistência, filas ou serviços locais — e não substitui a suíte
E2E de navegador.

## Passo 0 — Resolver contexto

Receba o ticket no diretório do projeto aberto e execute:

```text
sdd context resolve --ticket <TICKET> --runtime auto --json
```

Use exclusivamente `workspace`, `spec_path`, `scope`, `profile` e `runtime` do
resultado. Se `sdd` não estiver no PATH, localize o CLI por
`sdd doctor --scope user --json`. Não peça caminho do SDD Kit, não instale o
kit no projeto e não use configuração legada.

## Passo 1 — Confirmar estratégia e descobrir o stack

1. Leia `task.md`, `technical-design.md` e `acceptance-criteria.md`, quando
   existirem em `SPEC_PATH`.
2. Confirme que `delivery_kind` ou a etapa atual requer `integration-tests`.
   Se não requerer, registre `not-applicable` com justificativa e devolva o
   controle ao bootstrap.
3. Inspecione apenas os manifestos e testes já presentes no `workspace` para
   identificar linguagem, framework, comando de teste, convenções de fixtures,
   serviços dependentes e mecanismo de isolamento disponível.
4. Não presuma Docker, Testcontainers, Cypress, Cucumber, Kafka, Kustomize,
   banco específico, portas ou credenciais. Caso uma dependência externa não
   possa ser executada localmente, registre a evidência e a condição de
   execução, sem inventar stubs ou segredos.

## Passo 2 — Planejar a cobertura

Mapeie cada cenário para uma fronteira concreta e observável:

| Cenário | Fronteira | Pré-condição/dados | Resultado verificável | Isolamento |
|---|---|---|---|---|
| `<cenário>` | HTTP, persistência, evento ou serviço | `<dados>` | `<assertion>` | fixture, container ou ambiente local |

- Priorize caminhos críticos, erros de contrato, persistência e idempotência.
- Reutilize os padrões de teste do repositório; introduza dependências somente
  quando forem necessárias, compatíveis e justificadas em `task.md`.
- Se a cobertura exige ambiente compartilhado, deixe explícitos URL por
  referência, variáveis necessárias, dados de teste, limpeza e responsável.

## Passo 3 — Implementar e executar

1. Crie ou atualize os testes no local convencional do projeto consumidor.
2. Use nomes determinísticos, fixtures mínimas e limpeza proporcional ao dado
   criado. Nunca grave tokens, senhas ou URLs internas no repositório.
3. Execute o menor comando oficial que cubra os cenários criados.
4. Registre no estado da demanda os arquivos alterados, comando executado,
   resultado, limitações e evidências. Uma suíte criada mas não executada deve
   permanecer como `generated`, não como `passed`.

## Resultado

Ao concluir, atualize `status-task.md` e `session-state.md` em `SPEC_PATH`:

| Campo | Valor |
|---|---|
| last_agent | `sdd-generate-integration-tests` |
| last_runtime | runtime resolvido pelo CLI |
| integration_tests | `passed`, `generated`, `blocked` ou `not-applicable` |
| evidence | arquivos, comando e resultado observável |
| next_agent | `sdd-generate-e2e-tests`, `sdd-review-code` ou o indicado pelo bootstrap |

Não aprove G4 quando a execução não tiver evidência real. Reporte de forma
curta o que foi coberto, o comando executado e qualquer bloqueio.
