---
name: sdd-update-documentation
description: "Atualiza a documentação do projeto após implementação. Uso: sdd-update-documentation <TICKET>."
---

> **Autor:** Felipe Maurício da Silva · **E-mail:** fellipemauriciosilva@gmail.com · **LinkedIn:** https://www.linkedin.com/in/felipe-mauricio-06685735/

# Update Documentation

O usuário invoca este agente no projeto aberto com o ticket (ex. `/sdd-update-documentation ABC-123`). Resolva `PROJECT` pelo contexto do runtime e extraia somente `TICKET` do argumento.

Atualize a documentação do projeto para refletir as mudanças implementadas no ticket.

---

## Passo 0 — Resolver contexto pelo CLI (v3.2)

Receba somente o ticket no projeto aberto e execute `sdd context resolve --ticket TICKET --runtime auto --json`. Consuma `workspace`, `spec_path`, `scope`, `profile` e `runtime`.

Use `SPEC_PATH` em todos os acessos a `session-state.md`, `task.md` e demais arquivos da demanda. A resolução centralizada cobre a ativação user. Se `sdd` não estiver no PATH, use o `scripts/sdd.py` indicado por `sdd doctor --scope user --json`.

---

## Passo 1 — Ler o task.md

Leia `{SPEC_PATH}task.md` com foco em:
- **Affected Files**: quais arquivos foram criados ou modificados
- **Implementation Plan**: o que foi implementado
- **Decisions Made**: decisões técnicas tomadas
- **Entry Point**: ponto de entrada do fluxo

---

## Passo 2 — Atualizar project-context/

Verifique e atualize os seguintes arquivos conforme necessário:

- `PROJECT/.github/docs/project-context/project-overview.md` — se a demanda introduziu novo módulo, funcionalidade ou capacidade relevante
- `PROJECT/.github/docs/project-context/current-architecture.md` — se houve mudança arquitetural (nova camada, novo padrão, nova dependência)
- `PROJECT/.github/docs/project-context/module-map.md` — se foram criados novos arquivos de classe relevantes

Regra: só atualize se houver mudança real. Não adicione conteúdo redundante com o que já está documentado.

---

## Passo 3 — Atualizar architecture/ (se aplicável)

Se a implementação introduziu uma nova decisão arquitetural relevante, crie ou atualize:

`PROJECT/.github/docs/architecture/decisions/ADR-<NNNN>-<titulo-kebab-case>.md`

Use o template:

```markdown
# ADR-NNNN — <Título>

## Status
Aceito

## Contexto
<Por que essa decisão foi necessária>

## Decisão
<O que foi decidido>

## Consequências
<Impactos positivos e negativos>
```

---

## Passo 4 — Fechar a spec

Atualize `{SPEC_PATH}task.md`:
- Mude `Status` para `done`
- Preencha qualquer `Open Question` que tenha sido resolvida durante a implementação
- Confirme que `Decisions Made` está completo

---

## Passo 4.5 — Append ao Decision Log do projeto

Se `task.md → Decisions Made` tiver pelo menos uma decisão preenchida (não-TODO, não vazio):

1. Leia `PROJECT/.github/docs/project-context/decisions-log.md`. Se não existir, crie a partir do template do SDD Kit (`{sdd_kit}/templates/decisions-log.md`).
2. Para cada decisão registrada em `Decisions Made`, adicione uma entrada ao decision log (append-only, nunca remova entradas anteriores):

```markdown
### [TICKET] — <Título da decisão em uma linha>

**Ticket:** [TICKET]
**Data:** YYYY-MM-DD
**Agente:** sdd-update-documentation

**Contexto:** <por que esta decisão foi necessária — extraído de task.md>

**Decisão:** <o que foi decidido — extraído de Decisions Made>

**Consequências:** <impacto no código ou arquitetura — infira do Affected Files se não explícito>

---
```

3. Se `task.md → Decisions Made` estiver vazio ou com `TODO`, pule este passo sem erro.

---

## Passo 5 — Resumo

Apresente ao usuário:

| Arquivo | Ação |
|---------|------|
| `project-context/current-architecture.md` | Atualizado / Sem mudança necessária |
| `project-context/module-map.md` | Atualizado / Sem mudança necessária |
| `architecture/decisions/ADR-NNNN.md` | Criado / Não necessário |
| `specs/TICKET/task.md` | Status → done |

---

## Regras

- Nunca invente documentação — baseie-se exclusivamente no `task.md` e no código implementado.
- Não duplique informação já presente nos docs.
- Atualize apenas o que realmente mudou.
- Mantenha o estilo e formato já existente em cada arquivo.

---

## Ao Finalizar — Obrigatório

Atualize `{SPEC_PATH}session-state.md` (caminho resolvido no Passo 0) com os seguintes campos:

| Campo             | Valor                                                    |
|-------------------|----------------------------------------------------------|
| status            | done                                                     |
| last_agent        | sdd-update-documentation                                 |
| last_runtime      | github-copilot ou claude-code (detecte pelo contexto)    |
| last_run          | \<timestamp ISO 8601\>                                   |
| next_agent        | — (demanda concluída)                                    |
| next_instruction  | Abrir PR com o diff completo                             |
| blocked_on        | —                                                        |

Escreva um **Checkpoint**:
> "Documentação atualizada. Demanda `TICKET` concluída. PR pode ser aberto."

Adicione uma linha no `Agent History`:

```
| <timestamp> | sdd-update-documentation | <runtime> | Documentação atualizada — demanda encerrada |
```
