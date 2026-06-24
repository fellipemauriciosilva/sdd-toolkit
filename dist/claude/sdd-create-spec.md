---
name: "sdd-create-spec"
description: "Cria a pasta de demanda e scaffolda os arquivos de análise em um projeto específico do workspace"
---

# Create Spec

The user invoked this prompt passing the project folder name as an argument (e.g. `/create-spec gcb-hr-hub-corporate-email`). Extract that name and use it as `PROJECT`.

Create the demand folder and scaffold the analysis files inside `PROJECT/`. No code analysis, no implementation.

## Template de Contexto (opcional)

Antes de criar a pasta, se o usuário não forneceu uma descrição além do número do ticket, apresente este formulário de contexto rápido. Se o usuário já forneceu descrição suficiente, pule direto para "What to do".

> **Contexto da demanda** — responda o que souber. Campos marcados com * são recomendados; os demais são opcionais.
>
> **1. Qual problema esta demanda resolve?** *
> _(Ex: "O campo motivoAfastamento não é enviado no evento Kafka, causando perda de informação no worker")_
>
> **2. Qual o objetivo esperado após a implementação?** *
> _(Ex: "O evento deve incluir o campo e o worker deve persistir o valor no banco")_
>
> **3. Contexto técnico relevante** _(opcional)_
> _(Ex: "Fluxo inicia no Controller POST /jornadas, passa pelo Service e publica no tópico kafka.jornada.atualizada")_
>
> **4. Restrições conhecidas** _(opcional)_
> _(Ex: "Não pode quebrar contrato do evento — consumidores existentes não devem ser afetados")_
>
> **5. Recursos disponíveis** _(opcional)_
> _(Ex: "Spec em .github/docs/specs/JT-1234/spec.md", "Critérios de aceite no Jira")_

Use as respostas para pré-preencher `spec.md` e complementar a seção Identification do `task.md`. Se o usuário não responder, crie os arquivos com `TODO` nas seções correspondentes.

---

## Passo 0 — Resolver caminho do workspace (v2.5)

1. Verifique se `PROJECT/.github/sdd.config.md` existe.
2. **Se existir:** leia `sdd_kit:`, `project:` e `sdd_workspace:`. Compute:
   - Se `sdd_workspace:` definido: `SPEC_PATH = {sdd_workspace}/{project}/specs/TICKET/`
   - Caso contrário: `SPEC_PATH = {sdd_kit}/workspace/{project}/specs/TICKET/`
3. **Se não existir:** `SPEC_PATH = PROJECT/.github/docs/specs/TICKET/` (legado pré-v2.5).

Use `SPEC_PATH` para criar a pasta da demanda e todos os seus arquivos.

---

## What to do

1. Ask the user for the ticket identifier if not provided (e.g. `JT-1234`, `BUG-5678`, `GDAS-999`).
2. **Se o tipo não foi informado**, pergunte: "Qual o tipo da demanda? `[feature / bugfix / refactor / migration]`". Aguarde a resposta antes de criar qualquer arquivo. Se o usuário não souber, use `feature` como padrão e informe.
3. Create the folder `{SPEC_PATH}` (resolvido no Passo 0).
4. Create the subfolder `{SPEC_PATH}test-case/`.
5. Crie os arquivos de scaffold no demand folder:
   - **`tasks.md`** — use o template por tipo correspondente:
     | Tipo | Template |
     |------|----------|
     | feature | `{sdd_kit}/templates/specs/types/task-feature.md` |
     | bugfix | `{sdd_kit}/templates/specs/types/task-bugfix.md` |
     | refactor | `{sdd_kit}/templates/specs/types/task-refactor.md` |
     | migration | `{sdd_kit}/templates/specs/types/task-migration.md` |
     Se `sdd_kit` não disponível (legado): use `.github/docs/specs/_template/types/` no projeto.
     Preencha apenas a tabela **Identification** (Ticket, Type, Status = `analysis`). Deixe as demais seções como TODO.
   - `status-task.md` — fill: Ticket = `[TICKET]`, Status = `analysis`, Last Agent = `sdd-create-spec`, Last Run = today's date, Next Suggested Agent = `sdd-analyze-demand`. Add first row to Agent History.
   - `session-state.md` — fill: ticket = `[TICKET]`, project = `[PROJECT]`, status = `analysis`, next_agent = `sdd-analyze-demand`, next_instruction = `Executar análise inicial da demanda`. Checkpoint: `Scaffold criado. Nenhum agente executado ainda.`.
   - `spec.md` (optional — create only if the user provides a description beyond the ticket number)
   - `acceptance-criteria.md` (optional)
6. Confirm the folder was created and list the files (including `test-case/`).
7. Inform the user: run `/sdd-bootstrap PROJECT [TICKET]` to start or resume the demand from any runtime (GitHub Copilot or Claude Code).

## Rules
- Do not read the codebase.
- Do not analyze architecture or existing code.
- Do not fill any section beyond Identification.
- Do not implement anything.
- Se o template por tipo não existir no projeto, use o template genérico `tasks.md`.
