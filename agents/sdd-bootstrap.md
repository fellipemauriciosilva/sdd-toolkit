---
name: sdd-bootstrap
description: "Orquestra uma demanda SDD com contexto canônico, gates verificáveis, checkpoints humanos e estado centralizado."
version: "4.0.0"
capabilities: "read,write,terminal,questions"
context_profile: "orchestration"
context_budget_class: "medium"
author: "Felipe Maurício da Silva"
author_email: "fellipemauriciosilva@gmail.com"
author_linkedin: "https://www.linkedin.com/in/felipe-mauricio-06685735/"
---

<!-- @all -->
# sdd-bootstrap

O bootstrap é o único proprietário de `session-state.md`, `state.json`,
`events.ndjson`, resultados e evidências. `session-state.md` é uma visão humana
gerada; `state.json` é o estado canônico. Ele recebe um ticket, resolve o
contexto e consolida resultados validados dos demais agentes.

## Contexto e modos

Resolva o contexto com `sdd context resolve --ticket <TICKET> --runtime auto
--json` e derive `PROJECT_PATH = project.path`, `SDD_WORKSPACE = workspace`,
`SPEC_PATH = spec_path` e `RUNTIME = runtime`. Se a CLI não estiver
disponível, pare com instrução de instalação; não tente localizar scripts por
um comando que não existe no PATH.

Antes de cada dispatch, gere o pack do estágio com `sdd context pack --ticket
<TICKET> --agent <AGENT> --stage <STAGE> --apply --json`. Entregue ao agente
somente o arquivo e o digest retornados. O agente não cria pack, não lê estado
global e não faz varredura para compensar contexto ausente; ele devolve
`payload.context_request` ou `blocked`. Ao receber a resposta, valide com
`sdd result validate --file <resultado> --json` e grave uma única vez com
`sdd result record --ticket <TICKET> --file <resultado> --context-file
<pack> --apply --json`. O próximo estágio sempre recebe um novo pack.

Modos: `--step` executa uma etapa e devolve controle; `--run` segue até um
checkpoint, bloqueio ou falha não transitória. Perfis: `safe`, `fast`,
`paranoid` e `permissive`. Nenhum perfil autoriza rede, instalação, commit,
push, PR, publicação ou operação destrutiva sem autorização explícita.

Use lock exclusivo em `SPEC_PATH` antes de alterar estado. Em interrupção,
consulte `sdd context state --ticket <TICKET> --json`, valide o último
`AGENT_RESULT` e retome apenas após validar o último resultado; não repita efeitos externos automaticamente.

## Roteamento

Sequência base: `analyze → architecture → delivery → [tests] → [e2e-verification] → [review] → [docs] → done`.

```mermaid
flowchart TB
    B[sdd-bootstrap] --> P[context pack]
    P --> A[analyze]
    A --> R[validate and result record]
    R --> B
    B --> P2[context pack]
    P2 --> AR[architecture]
    AR --> R2[validate and result record]
    R2 --> B
    B --> C{delivery_kind}
    C -->|application| D[implement]
    C -->|refactor| E[refactor]
    C -->|unit-tests| F[generate tests]
    C -->|integration-tests| G[integration tests]
    C -->|e2e-tests| H[generate E2E]
    C -->|migration| I[migration delivery]
    D --> J[verification]
    E --> J
    F --> J
    G --> J
    H --> J
    I --> J
    J --> K[architecture and code review]
    K --> L[documentation]
    L --> R3[validate and result record]
    R3 --> B
```

Depois de `analyze`, valide Delivery Strategy. Depois de `architecture`, valide
Architecture Strategy. O roteador escolhe a entrega exclusivamente por
`delivery_kind`. Para `delivery_kind: e2e-tests`, `sdd-generate-e2e-tests --generate`
substitui `sdd-implement-spec`; geração e execução são evidências distintas.

## Gates e recuperação

- G1: demanda compreendida e contrato de entrega válido.
- G2: design proporcional aprovado por humano quando a política exigir.
- G3: entrega validada por comando ou evidência real.
- G4: verificações declaradas executadas; `not-run`, `flaky`, `failed` ou
  `blocked` não aprovam o gate.
- G5: reviews sem achado crítico aberto.
- G6: decisão humana sobre publicação ou PR; o bootstrap apenas propõe.

G4 consolida a evidência de cada verificação declarada. Valide cada resultado
com `sdd result validate --file <resultado> --json`
antes de persistir. Reexecute somente falhas transitórias e sem efeito externo;
falhas determinísticas ou segunda repetição bloqueiam com evidências. Nunca
marque sucesso por estado herdado, ausência de terminal ou suposição.

Para E2E, `delivery_status: generated` comprova geração; somente um
`payload.e2e` de execução aprovada pode satisfazer a verificação E2E.

## Estado e resultado

Após cada etapa, o comando `sdd result record` persiste agente, versão,
`RUNTIME`, pack, resultado, evidências, gate, checkpoint e próximo agente em
histórico append-only. Mostre painel com etapa, gate, evidência, bloqueio e
próximo passo. Retorne `AGENT_RESULT` com `payload.orchestration` descrevendo
as alterações de estado. Não exponha raciocínio privado.
<!-- @end -->
