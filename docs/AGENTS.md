# Catálogo de agentes

Os 17 agentes são escritos em `agents/` e compilados para todos os runtimes.
O orquestrador resolve o ticket, entrega Context Packs por estágio, respeita as
capabilities declaradas e preserva a revisão humana nos gates.

O contrato comum está em [AGENT-CONTRACT.md](AGENT-CONTRACT.md): contexto
canônico, classificação entre agentes de demanda e de apoio, capabilities versus
efeitos reais, envelope `AGENT_RESULT` e chave `payload` de cada agente. A
política operacional vive em `templates/agent-policy.md` e é injetada como
prefixo estável de todo agente compilado, nos quatro runtimes.

## Como os agentes cooperam

```mermaid
flowchart TB
    B[sdd-orchestrator] --> P[Context Pack]
    P --> A[sdd-analyze-demand]
    A --> R[AGENT_RESULT]
    R --> B
    B --> P2[Context Pack de arquitetura]
    P2 --> AR[sdd-architect]
    AR --> R2[AGENT_RESULT]
    R2 --> B
    B --> D{delivery_kind}
    D --> I[sdd-implement-spec]
    D --> F[sdd-refactor-code]
    D --> E[sdd-generate-e2e-tests]
    D --> T[sdd-generate tests]
    I --> V[resultado validado]
    F --> V
    E --> V
    T --> V
    V --> B
    B --> RV[sdd-review-code]
    RV --> U[sdd-update-documentation]
    U --> B
```

`sdd-architect` é o ponto de aprofundamento técnico: ele define impacto,
trade-offs, arquivos afetados, riscos e evidências antes de o orquestrador escolher
o agente que produz a entrega. `sdd-read-document`, `sdd-setup-project`,
`sdd-install-sdd-kit` e `sdd-workspace-sync` são agentes de apoio e podem ser
acionados conforme a necessidade, sem pular os gates.

| Grupo | Agentes |
|---|---|
| Orquestração | `sdd-orchestrator`, `sdd-architect`, `sdd-create-spec`, `sdd-analyze-demand` |
| Entrega | `sdd-implement-spec`, `sdd-refactor-code`, `sdd-investigate-bug`, `sdd-analyze-migration` |
| Testes | `sdd-generate-tests`, `sdd-generate-integration-tests`, `sdd-generate-e2e-tests` |
| Revisão e documentação | `sdd-review-code`, `sdd-update-documentation`, `sdd-read-document` |
| Setup e operação | `sdd-setup-project`, `sdd-install-sdd-kit`, `sdd-workspace-sync` |

## Resultado dos agentes

Nenhum agente de execução escreve `state.json`, `events.ndjson` ou
`session-state.md`. A criação inicial de `session-state.md` a partir do template
é a única exceção e pertence ao `sdd-create-spec` no scaffold da demanda;
atualizá-la depois é exclusivo do `sdd-orchestrator`. Cada agente devolve um
`AGENT_RESULT` validável por `sdd result validate --file <resultado> --json`, e
o `sdd-orchestrator` consolida o estado a partir de resultados validados. Testes ou
builds não executados são registrados como `not-run`; falhas anteriores à
demanda vão em `preexisting_failures`.

## Regras de integração

- Edite apenas `agents/*.md`; nunca altere `dist/` manualmente.
- A versão do agente acompanha o `VERSION` do toolkit; `sdd lint` falha em caso
  de divergência.
- Recompile com `python scripts/sdd_compile.py --runtime all` e regenere o
  inventário com `python scripts/build_inventory.py --write dist/build-manifest.json`.
- Execute `sdd lint --json`, os testes e a validação de conteúdo público.
- O arquiteto produz ou revisa artefatos de spec; não implementa código de
  produção diretamente.

As capabilities `read`, `write`, `terminal` e `questions` são declaradas no
frontmatter e propagadas para os quatro runtimes. O compilador reduz as tools do
Copilot conforme essa declaração, e o linter recusa um agente que instrua um
efeito fora das capabilities que declara.
