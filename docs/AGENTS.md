# Catálogo de agentes

Os 17 agentes são escritos em `agents/` e compilados para todos os runtimes.
Todos devem resolver contexto pela CLI, respeitar capabilities declaradas e
preservar a revisão humana nos gates.

## Como os agentes cooperam

```mermaid
flowchart LR
    C[sdd-create-spec] --> A[sdd-analyze-demand]
    A --> R[sdd-architect]
    R --> B[sdd-bootstrap]
    B --> D{Tipo de entrega}
    D -->|Aplicação| I[sdd-implement-spec]
    D -->|Refactor| F[sdd-refactor-code]
    D -->|Bug| G[sdd-investigate-bug]
    D -->|Migração| M[sdd-analyze-migration]
    D -->|E2E| E[sdd-generate-e2e-tests]
    I --> T[Testes e verificações]
    F --> T
    G --> T
    M --> T
    E --> T
    T --> V[sdd-review-code]
    V --> U[sdd-update-documentation]
```

`sdd-architect` é o ponto de aprofundamento técnico: ele define impacto,
trade-offs, arquivos afetados, riscos e evidências antes de o bootstrap escolher
o agente que produz a entrega. `sdd-read-document`, `sdd-setup-project`,
`sdd-install-sdd-kit` e `sdd-workspace-sync` são agentes de apoio e podem ser
acionados conforme a necessidade, sem pular os gates.

| Grupo | Agentes |
|---|---|
| Orquestração | `sdd-bootstrap`, `sdd-architect`, `sdd-create-spec`, `sdd-analyze-demand` |
| Entrega | `sdd-implement-spec`, `sdd-refactor-code`, `sdd-investigate-bug`, `sdd-analyze-migration` |
| Testes | `sdd-generate-tests`, `sdd-generate-integration-tests`, `sdd-generate-e2e-tests` |
| Revisão e documentação | `sdd-review-code`, `sdd-update-documentation`, `sdd-read-document` |
| Setup e operação | `sdd-setup-project`, `sdd-install-sdd-kit`, `sdd-workspace-sync` |

## Regras de integração

- Edite apenas `agents/*.md`; nunca altere `dist/` manualmente.
- Atualize a versão do agente quando o contrato comportamental mudar.
- Recompile com `python scripts/sdd_compile.py --runtime all`.
- Execute testes, evals e validação de conteúdo público.
- O arquiteto produz ou revisa artefatos de spec; não implementa código de
  produção diretamente.

As capabilities `read`, `write`, `terminal` e `questions` são declaradas no
frontmatter. O compilador reduz as tools do Copilot conforme essa declaração.
