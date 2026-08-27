# SDD Kit — Evals dos Agentes

Framework de avaliação para os 8 agentes principais do pipeline SDD.

## Estrutura

```
evals/
  <nome-agente>/
    case-01/
      input.md       — cenário de entrada (project, ticket, contexto)
      expected.md    — comportamento esperado (checklist de outputs)
      rubric.md      — critérios de avaliação para o LLM judge
    case-02/
    case-03/
```

## Como usar

Método manual (revisão humana):
1. Forneça o `input.md` ao agente e observe o output.
2. Compare com `expected.md`.
3. Preencha o `rubric.md` com ✓/✗ por critério.

Método automático (LLM judge via sdd-review-code; disponível quando o runtime oferecer o fluxo de eval):
```
/sdd-review-code --eval <agente> <case-NN>
```
O agente lê `input.md`, executa o agente alvo em modo simulado, compara com `expected.md` usando a `rubric.md` como guia, e retorna um score de 0–100.

## Score mínimo aceitável

| Agente | Score mínimo |
|--------|-------------|
| sdd-bootstrap | 85 |
| sdd-analyze-demand | 80 |
| sdd-implement-spec | 80 |
| sdd-generate-integration-tests | 75 |
| sdd-generate-e2e-tests | 85 |
| sdd-review-code | 80 |
| sdd-update-documentation | 80 |
| sdd-create-spec | 90 |

## Agentes avaliados

- [sdd-bootstrap](sdd-bootstrap/) — orquestrador principal
- [sdd-analyze-demand](sdd-analyze-demand/) — análise de demanda e G1
- [sdd-implement-spec](sdd-implement-spec/) — implementação e G2/G3
- [sdd-generate-integration-tests](sdd-generate-integration-tests/) — testes e G4
- [sdd-generate-e2e-tests](sdd-generate-e2e-tests/) — Playwright no projeto consumidor e G4
- [sdd-review-code](sdd-review-code/) — revisão de código e G5
- [sdd-update-documentation](sdd-update-documentation/) — documentação e G6
- [sdd-create-spec](sdd-create-spec/) — scaffold de demanda
