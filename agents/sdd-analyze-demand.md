---
name: sdd-analyze-demand
description: "Lê os documentos de demanda e complementa task.md em um projeto específico do workspace"
version: "2.5.0"
capabilities: "read,write"
author: "Felipe Maurício da Silva"
author_email: "fellipemauriciosilva@gmail.com"
author_linkedin: "https://www.linkedin.com/in/felipe-mauricio-06685735/"
---

<!-- @all -->
# Analyze Demand

The user invokes this prompt from the target project and may provide a ticket
(for example `/sdd-analyze-demand JT-1234`). Resolve the workspace through the
CLI; do not require a project-folder argument.

Read all documents in the demand folder and complement `task.md` based exclusively on what is documented — no code analysis, no implementation.

## Passo 0 — Resolver contexto pelo CLI (v3.2)

Receba somente o ticket no projeto aberto e execute `sdd context resolve --ticket TICKET --runtime auto --json`.

Use exclusivamente `workspace`, `spec_path`, `scope`, `profile` e `runtime` do resultado. Não replique a resolução de caminhos no agente.

Se `sdd` não estiver no PATH, use o `scripts/sdd.py` da instalação indicada por `sdd doctor --scope user --json`.

Use `SPEC_PATH` em todos os acessos a `session-state.md`, `task.md` e demais arquivos da demanda.

---

## What to do

### Step 1 — Identify the spec folder

Ask the user for the ticket identifier if not provided.
The spec folder is at `SPEC_PATH` (resolvido no Passo 0).

### Step 2 — Read demand documents

Read all files present in the demand folder:
- `task.md` — current state (check which sections are already filled)
- `spec.md` — functional specification (if exists)
- `acceptance-criteria.md` — acceptance criteria (if exists)
- `test-case/` — all files inside this folder (if any)
- Any other `.md`, `.doc`, `.docx` or `.pdf` file found in the folder

When available, read the project's existing context documentation for domain
vocabulary only. Do not depend on a fixed documentation path.

### Step 2B — Detecção de Tipo: Migração

Após ler o `task.md`, verifique o campo **Type** na tabela de Identification:

```markdown
| Type | migration | ← este campo
```

**Se `Type: migration`:** antes de prosseguir para o Step 3, invoque o agente especialista `sdd-analyze-migration` para analisar o sistema legado e produzir `migration-analysis.md`.

<!-- @end -->
<!-- @claude -->
Invoque o sub-agente `sdd-analyze-migration` passando o ticket:

```
Agent: sdd-analyze-migration
Input: /sdd-analyze-migration TICKET
```

Aguarde a conclusão. O agente produzirá `{SPEC_PATH}migration-analysis.md` com diagnóstico do legado, inventário de stack, estratégia de migração, ADRs e plano de ondas.
<!-- @end -->
<!-- @copilot -->
Execute:
```
@sdd-analyze-migration TICKET
```

Aguarde o agente concluir e produzir `{SPEC_PATH}migration-analysis.md` antes de continuar.
<!-- @end -->
<!-- @all -->

Após o `sdd-analyze-migration` retornar:
1. Leia o `{SPEC_PATH}migration-analysis.md` gerado
2. Use seus achados no Step 3 para enriquecer as seções do `task.md`:
   - **Demand Summary** → inclua a estratégia de migração e o padrão escolhido (Strangler Fig, etc.)
   - **Expected Behavior** → derive do plano de ondas e dos bounded contexts identificados
   - **Risks and Assumptions** → inclua os Gaps, Bloqueadores e Riscos do `migration-analysis.md`
   - **Open Questions** → adicione as Questões Arquiteturais Abertas (Q#) do relatório

> Se `Type` não for `migration`, ignore este step e prossiga normalmente para o Step 3.

---

### Step 2C — Estratégia de entrega e verificação

Depois de ler os documentos, resolva o contrato de delivery antes de preencher o
plano. Use o comando determinístico quando disponível:

```bash
sdd delivery propose --type <TYPE> --description "<resumo seguro>" --json
```

Registre em `task.md` a seção `Delivery Strategy` com:

| Campo | Regra |
|---|---|
| `delivery_contract_version` | `1.0` |
| `delivery_kind` | `application`, `refactor`, `unit-tests`, `integration-tests`, `e2e-tests` ou `migration` |
| `verification` | lista sem duplicatas de `none`, `unit`, `integration`, `e2e` |
| `rationale` | justificativa baseada nos documentos, sem inferir requisito ausente |
| `owner` | `sdd-analyze-demand` |
| `expected_evidence` | evidências exigidas pelo gate correspondente |

Defaults por tipo: `feature`/`bugfix` → `application`; `refactor` → `refactor`;
`migration` → `migration`; `test-e2e` → `e2e-tests` com `verification: [e2e]`.
Uma feature web pode manter `application` e adicionar `e2e` apenas como
verificação. Não confunda a entrega de uma suíte com a execução de uma suíte.

Para `test-e2e`, não encaminhe para `sdd-implement-spec`: a entrega será
`sdd-generate-e2e-tests --generate` depois do G2. Se houver conflito de
framework, ausência de base URL/start/auth ou ambiguidade entre entrega e
verificação, registre `blocked_on`/Open Question e aguarde decisão humana.

<!-- @end -->
<!-- @claude -->
Valide a proposta com `sdd delivery validate` quando o JSON do contrato estiver
disponível e preserve o resultado no contexto da demanda. Depois de atualizar
o `task.md`, valide a seção persistida com:

```bash
sdd delivery validate --task "${SPEC_PATH}task.md" --json
```
<!-- @end -->
<!-- @copilot -->
Valide a proposta com `python scripts/sdd_delivery.py propose --type <TYPE>` ou
`sdd delivery validate` quando o JSON do contrato estiver disponível.
<!-- @end -->
<!-- @all -->

---

### Step 3 — Complement `task.md` from the documents

Based **exclusively** on the documents read (no code analysis), fill or complement the following sections in `task.md`:

- **Demand Summary** — synthesize the demand in one paragraph from `spec.md` or user description
- **Expected Behavior** — what the system must do after the demand, derived from `spec.md` and `acceptance-criteria.md`
- **Tests to Add/Update** — test scenarios derived from `test-case/` files and acceptance criteria
- **Risks and Assumptions** — risks mentioned in the documents or that are evident from the spec
- **Open Questions** — items mentioned in the documents that are ambiguous or missing detail
- **Decisions Made** — decisions that are already explicit in the spec (e.g. "use idempotency key X")

Leave the following sections as `TODO` — they require code analysis and will be filled by `/implement-spec`:
- Current Behavior
- Affected Files
- Entry Point
- Flow Analysis
- Implementation Plan

### Step 3B — Decomposição MoSCoW (épicos e jornadas)

> **Execute esta etapa somente se** a demanda for um **épico**, **jornada** ou **feature composta** (múltiplos critérios de aceite independentes ou mais de 3 sub-fluxos distintos). Para tickets simples (bugfix, ajuste pontual, configuração), pule direto para o Step 4.

Com base nos documentos lidos, classifique cada requisito/critério de aceite em uma das categorias MoSCoW:

| Categoria | Significado | Critério de inclusão |
|-----------|-------------|----------------------|
| **Must Have** | Obrigatório — sem isso o MVP não funciona | Critério de aceite bloqueante, fluxo principal |
| **Should Have** | Importante — agrega valor significativo | Regra de negócio secundária, validação extra |
| **Could Have** | Desejável — melhoria incremental | Mensagem amigável, log extra, otimização |
| **Won't Have (now)** | Fora do escopo desta entrega | Funcionalidade futura, integrações opcionais |

**Formato da classificação** — adicione ao `task.md` a seção **MoSCoW** após `Expected Behavior`:

```markdown
## MoSCoW — Priorização de Requisitos

### Must Have
- [ ] <requisito obrigatório 1>
- [ ] <requisito obrigatório 2>

### Should Have
- [ ] <requisito importante 1>

### Could Have
- [ ] <desejável 1>

### Won't Have (this release)
- <item fora do escopo, com breve justificativa>
```

**Formato de User Story** — para cada item Must Have, escreva (se ainda não existir em `spec.md`):

> Como **[perfil do usuário]**, quero **[funcionalidade]**, para que **[benefício de negócio]**.

**Regras:**
- Baseie a classificação exclusivamente nos documentos lidos — não invente requisitos
- Se a classificação for ambígua (Must vs Should), marque como `TODO — classificar com PO` em Open Questions
- Itens Won't Have devem ter uma frase de justificativa
- Esta seção deve ser revisada com o PO antes de prosseguir para implementação se houver itens em dúvida

### Step 4 — Update task.md status

Change `Status` in the Identification table to `spec-analyzed`.

### Step 5 — Summarize and hand off

Show a summary table:

| Section | Status |
|---------|--------|
| Demand Summary | ✅ filled / ⚠️ partial / ❌ missing |
| Expected Behavior | ✅ filled / ⚠️ partial / ❌ missing |
| Tests to Add/Update | ✅ filled / ⚠️ partial / ❌ missing |
| Risks and Assumptions | ✅ filled / ⚠️ partial / ❌ missing |
| Open Questions | ✅ filled / ✅ none identified |
| Current Behavior | 🔜 pending code analysis |
| Affected Files | 🔜 pending code analysis |
| Entry Point | 🔜 pending code analysis |
| Flow Analysis | 🔜 pending code analysis |
| Implementation Plan | 🔜 pending code analysis |

Then inform the user:
> `task.md` updated with document-based analysis. Review the filled sections and run `/sdd-implement-spec [TICKET]` from this project to start the code analysis and implementation.

## Rules
- Do not read or analyze the codebase.
- Do not invent requirements not present in the documents.
- Do not fill sections that depend on code analysis (Current Behavior, Affected Files, Entry Point, Flow Analysis, Implementation Plan).
- If `test-case/` is empty and no acceptance criteria exist, note it under Open Questions and ask the user if they want to provide test cases before proceeding.
- Mark ambiguous items as `TODO — [reason]` rather than guessing.
- Base everything exclusively on the documents in the demand folder.

---

## Ao Finalizar — Obrigatório

Atualize `{SPEC_PATH}session-state.md` (caminho resolvido no Passo 0) com os seguintes campos:

| Campo             | Valor                                                       |
|-------------------|-------------------------------------------------------------|
| status            | spec-analyzed                                               |
| last_agent        | sdd-analyze-demand                                          |
| last_runtime      | github-copilot _ou_ claude-code (detecte pelo contexto)     |
| last_run          | \<timestamp ISO 8601\>                                      |
| next_agent        | sdd-architect                                           |
| next_instruction  | Classificar impacto e produzir Technical Design antes do G2; delivery ocorre depois da aprovação |
| blocked_on        | — (ou descreva perguntas em aberto que bloqueiam a análise) |

Escreva um **Checkpoint** descrevendo:
- Quais seções do `task.md` foram preenchidas
- Quais seções ficaram como TODO e por quê
- Quais documentos foram lidos (spec.md, acceptance-criteria.md, test-case/, etc.)
- Quaisquer perguntas em aberto que o próximo agente deve resolver

Adicione uma linha no `Agent History`:

```
| <timestamp> | sdd-analyze-demand | <runtime> | Análise de documentos concluída — task.md atualizado com <N> seções preenchidas |
```
<!-- @end -->
