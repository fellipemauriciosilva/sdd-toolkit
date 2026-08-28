# Arquitetura do SDD Toolkit

## Componentes

```mermaid
flowchart TB
    subgraph Source[Fontes versionadas do toolkit]
        A[agents/]
        T[templates/]
        R[runtimes/ e schemas/]
    end

    Source --> C[Compilador]
    C --> D[dist/ por runtime]

    D --> I[Install e update user]
    I --> H[Perfis de Claude Copilot Codex Cursor]
    I --> CLI[CLI sdd]

    X[Discovery multicamada] --> I
    X --> H
    X --> CLI

    P[Projeto consumidor] -->|activate e context resolve| CLI
    CLI --> W[Workspace pessoal da demanda]
    W --> B[Context Builder]
    B --> K[Context Pack imutável]
    K --> H
    H --> AG[Agente do estágio]
    AG --> AR[AGENT_RESULT]
    AR --> V[Result validator e recorder]
    V --> S[state.json events results evidence]
    S --> B
```

Os arquivos em `agents/` são a fonte canônica. O compilador gera artefatos para
Claude, Copilot, Codex e Cursor; `dist/` não deve ser alterado manualmente.

`Discovery multicamada` correlaciona comandos no PATH, extensões e perfis de
editores, package managers e metadados locais do sistema. O resultado mantém
separados CLI, extensão, aplicativo desktop e destino de assets; logo, não
confunde uma extensão instalada com uma CLI utilizável. O scan padrão é passivo;
o probe de versão exige modo explícito e usa somente argumentos fixos.

## Orquestração de uma demanda

```mermaid
sequenceDiagram
    participant U as Usuário
    participant B as sdd-bootstrap
    participant C as Context Builder
    participant A as Agente do estágio
    participant R as Result Recorder
    participant S as Stores da demanda

    U->>B: ticket e intenção
    B->>C: context pack para agente e estágio
    C->>S: lê estado resumo e referências permitidas
    C-->>B: pack com context_id e digest
    B->>A: pack imutável
    alt contexto suficiente
        A-->>B: AGENT_RESULT
        B->>R: validate e record
        R->>S: resultado evento estado e resumo
    else contexto insuficiente
        A-->>B: payload.context_request
        B->>C: expansão autorizada
        C-->>B: pack filho
    end
```

O bootstrap é o único componente que cria packs, aprova expansões e muda o
estado. Um agente não transfere contexto diretamente a outro agente: ele
produz um resultado validável e o próximo pack seleciona somente o delta útil.

## Fluxo de distribuição

```mermaid
flowchart LR
    A[agents e templates] --> B[compile]
    B --> C[dist por runtime]
    C --> D[install --scope user]
    D --> E[Perfis Claude, Copilot, Codex e Cursor]
    D --> F[Shim sdd e PATH owned]
    F --> G[CLI e resolução de contexto]
    G --> H[Workspace pessoal de specs]
```

O projeto consumidor entra somente em `activate` e `context resolve`; agentes,
skills e estado não são instalados nele.

## Escopos

- `user`: instalação e estado fora do projeto; é o único fluxo local suportado.
- `organization`: permanece bloqueado até existir provider com autenticação,
  aprovação e rollback auditável.

## Contratos principais

| Contrato | Finalidade |
|---|---|
| `context-resolution` | Resolve projeto, runtime, workspace e spec sem o agente adivinhar paths. |
| `delivery-contract` | Define o tipo de entrega e as verificações necessárias. |
| `architecture-contract` | Define impacto, design técnico e evidências arquiteturais. |
| `context-pack` | Vincula agente, ticket, referências, orçamento, digest e omissões explícitas. |
| `agent-result` | Registra saída compacta, evidências e proveniência do pack consumido. |
| `transaction-plan` e `transaction-journal` | Protegem install, update e uninstall user. |

Os schemas ficam em `schemas/` e devem falhar fechados para versão, campo ou
path não suportado.

## Estado e recuperação

O lifecycle user usa plano identificado por hash, lock e journal persistente.
Uma operação incompleta bloqueia novas alterações até `sdd transaction recover`
ser revisado e aplicado. O rollback restaura somente itens comprovadamente
gerenciados e preserva mudanças do usuário como conflito.

```mermaid
stateDiagram-v2
    [*] --> Planned
    Planned --> Applying: --apply + plan_id
    Applying --> Completed
    Applying --> Interrupted: encerramento ou falha
    Interrupted --> RecoveryPreview
    RecoveryPreview --> Recovered: recover --apply
    Recovered --> [*]
    Completed --> [*]
```

Cada etapa registra no journal apenas os alvos e hashes que pertencem à operação.
Isso permite recuperar assets, shim, PATH e manifest sem apagar alterações externas.

O journal de instalação é independente do estado de uma demanda. Para o segundo,
`state.json` guarda apenas o presente, `events.ndjson` registra a sequência e
`results/` / `evidence/` preservam a auditoria.

Consulte [USER-SCOPE.md](USER-SCOPE.md) para comandos e
[FILES-AND-LIFECYCLE.md](FILES-AND-LIFECYCLE.md) para ownership.
