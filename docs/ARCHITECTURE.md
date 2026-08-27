# Arquitetura do SDD Toolkit

## Componentes

```mermaid
flowchart TB
    subgraph Source[Fontes versionadas]
        A[agents/] 
        T[templates/]
        R[runtimes/]
    end

    Source --> C[Compilador]
    C --> D[dist/ por runtime]

    D --> I[Install e update no escopo user]
    I --> H[Perfis dos harnesses]
    I --> W[Workspace pessoal]

    X[Discovery multicamada] --> I
    X --> H
    X --> CLI

    H --> CLI[sdd context, delivery, architecture e transaction]
    W --> CLI
```

Os arquivos em `agents/` são a fonte canônica. O compilador gera artefatos para
Claude, Copilot, Codex e Cursor; `dist/` não deve ser alterado manualmente.

`Discovery multicamada` correlaciona comandos no PATH, extensões e perfis de
editores, package managers e metadados locais do sistema. O resultado mantém
separados CLI, extensão, aplicativo desktop e destino de assets; logo, não
confunde uma extensão instalada com uma CLI utilizável. O scan padrão é passivo;
o probe de versão exige modo explícito e usa somente argumentos fixos.

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

Consulte [USER-SCOPE.md](USER-SCOPE.md) para comandos e
[FILES-AND-LIFECYCLE.md](FILES-AND-LIFECYCLE.md) para ownership.
