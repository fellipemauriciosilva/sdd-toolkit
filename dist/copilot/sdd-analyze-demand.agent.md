---
mode: agent
author: "Felipe Mauricio da Silva"
description: "Lê os documentos de demanda e complementa task.md em um projeto específico do workspace"
model: "Claude Sonnet 4.6"
tools:
  - search/fileSearch
  - search/textSearch
  - edit/editFiles
  - edit/createFile
  - execute/runInTerminal
  - execute/getTerminalOutput
  - vscode/askQuestions
version: "2.5.0"
---

# Analyze Demand

The user invoked this prompt passing the project folder name and optionally the ticket as arguments (e.g. `/analyze-demand gcb-hr-hub-corporate-email JT-1234`). Extract those values and use them as `PROJECT` and `TICKET`.

Read all documents in the demand folder and complement `task.md` based exclusively on what is documented — no code analysis, no implementation.

## Passo 0 — Resolver caminho do workspace (v2.5)

1. Verifique se `PROJECT/.github/sdd.config.md` existe.
2. **Se existir:** leia `sdd_kit:`, `project:` e `sdd_workspace:`. Compute:
   - Se `sdd_workspace:` definido: `SPEC_PATH = {sdd_workspace}/{project}/specs/TICKET/`
   - Caso contrário: `SPEC_PATH = {sdd_kit}/workspace/{project}/specs/TICKET/`
3. **Se não existir:** `SPEC_PATH = PROJECT/.github/docs/specs/TICKET/` (legado pré-v2.5).

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

Also read `PROJECT/.github/docs/project-context/project-overview.md` for domain vocabulary only.

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
> `task.md` updated with document-based analysis. Review the filled sections and run `/implement-spec PROJECT [TICKET]` to start the code analysis and implementation.

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
| next_agent        | sdd-implement-spec                                          |
| next_instruction  | Analisar código e implementar conforme task.md preenchido   |
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
