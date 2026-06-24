---
name: "sdd-implement-spec"
description: "Analisa o código e implementa a demanda definida no spec em um projeto específico do workspace"
---

# Implement Spec

The user invoked this prompt passing the project folder name and optionally the ticket as arguments (e.g. `/implement-spec gcb-hr-hub-corporate-email JT-1234`). Extract those values and use them as `PROJECT` and `TICKET`.

Analyze the demand, fill the spec documents and implement exactly what was defined — nothing more, nothing less.

## Passo 0 — Resolver caminho do workspace (v2.5)

1. Verifique se `PROJECT/.github/sdd.config.md` existe.
2. **Se existir:** leia `sdd_kit:`, `project:` e `sdd_workspace:`. Compute:
   - Se `sdd_workspace:` definido: `SPEC_PATH = {sdd_workspace}/{project}/specs/TICKET/`
   - Caso contrário: `SPEC_PATH = {sdd_kit}/workspace/{project}/specs/TICKET/`
3. **Se não existir:** `SPEC_PATH = PROJECT/.github/docs/specs/TICKET/` (legado pré-v2.5).

Use `SPEC_PATH` em todos os acessos a `session-state.md`, `task.md` e demais arquivos da demanda.

---

## Passo 0.5 — Runtime

Você está executando como `claude-code`. Use a ferramenta bash para todos os comandos de terminal (testes, build, git). Registre `last_runtime: claude-code` no session-state ao finalizar.

---

## Step 1 — Identify the spec folder

Ask the user for the ticket identifier if not provided.
The spec folder is at `SPEC_PATH` (resolvido no Passo 0).

## Step 2 — Read project context

Before touching any code or spec file, read:
- `PROJECT/.github/copilot-instructions.md`
- `PROJECT/.github/AGENTS.md`
- `PROJECT/.github/docs/project-context/project-overview.md`
- `PROJECT/.github/docs/project-context/current-architecture.md`
- `PROJECT/.github/docs/project-context/module-map.md`
- `PROJECT/.github/docs/project-context/decisions-log.md` (se existir) — leia as decisões anteriores para evitar conflitos. Se houver decisão que contradiz o plano atual, sinalize antes de implementar.
- Any relevant spec already in the folder (e.g. `spec.md`, `acceptance-criteria.md`)

## Step 3 — Analyze the codebase

Based on the demand description in `task.md → Identification` and any notes the user provided:
- Identify the entry point (Kafka consumer, REST endpoint, scheduler, etc.)
- Trace the relevant flow through the existing code inside `PROJECT/src/`
- Identify all files that will need to be created or modified
- Identify existing tests near the target implementation

## Step 3.5 — Multi-projeto (se `affected_projects` preenchido)

Se `session-state.md` tiver `affected_projects` com um ou mais projetos (ex.: `gcb-project-a, gcb-project-b`):

1. Leia o contexto de cada projeto adicional (passos 2–3 repetidos para cada um).
2. Adicione ao `task.md` uma seção **Multi-projeto** abaixo de **Affected Files**:

```markdown
## Multi-projeto

Esta demanda afeta múltiplos projetos. Sub-plano por projeto:

### Projeto: gcb-project-a
| File | Layer | Change |
|------|-------|--------|
| `path/to/File.java` | application | modify |

### Projeto: gcb-project-b
| File | Layer | Change |
|------|-------|--------|
| `path/to/Other.java` | domain | create |
```

3. Durante o **Step 6 (Implement)**, execute os sub-passos para cada projeto na ordem declarada.
4. Faça commits separados por projeto: `feat(TICKET): <desc> [gcb-project-a]`.
5. Se um projeto falhar (G3), não avance para o próximo — pare e escale ao humano.

Se `affected_projects` estiver vazio ou `—`, ignore este step.

## Step 4 — Fill `task.md` with the full analysis

Update `{SPEC_PATH}task.md` filling every section based on evidence found:
- **Demand Summary**: one paragraph of what is being requested
- **Current Behavior**: how the system behaves today based on code analysis
- **Expected Behavior**: how it should behave after the demand
- **Affected Files**: each file, its layer and the change type (modify/create/delete)
- **Entry Point**: where the flow starts
- **Flow Analysis**: step-by-step of the relevant current flow
- **Implementation Plan**: concrete steps, one per class or group of changes
- **Tests to Add/Update**: which test classes and which scenarios
- **Risks and Assumptions**: anything that could go wrong or was assumed
- **Open Questions**: unresolved items that need clarification
- **Decisions Made**: leave empty for now; fill during implementation

## Step 5 — Confirm understanding before coding

Present a summary to the user:
- Scope: what will be implemented
- Files to create or modify (with layer)
- Tests to add or update
- Any open questions from the spec that could block implementation

If there are unresolved open questions, ask the user before proceeding.
Wait for explicit confirmation before writing any production code.

## Step 6 — Implement

Follow the **Implementation Plan** from `task.md` step by step:
- Implement only the scope defined in the spec
- Follow the architecture rules from `PROJECT/.github/copilot-instructions.md`
- Do not refactor unrelated code
- Do not change public contracts unless the spec explicitly requires it
- Do not add dependencies unless the spec requires it
- Follow the existing code style and naming conventions

### Step 6A — Ciclo TDD por Passo do Plano (Red → Green → Refactor)

Para **cada passo** do Implementation Plan, siga obrigatoriamente o ciclo TDD:

1. **🔴 Red** — Escreva o teste primeiro. O teste deve falhar porque a implementação ainda não existe.
   - Crie ou atualize a classe de teste correspondente ao passo atual
   - Defina os cenários: happy path, erro esperado, edge case relevante para esse passo
   - Execute os testes e confirme que estão **falhando** (red)
   - Nunca pule esta etapa: código sem teste red primeiro não é TDD

2. **🟢 Green** — Implemente o mínimo necessário para o teste passar.
   - Escreva apenas o código suficiente para os testes do passo atual ficarem verdes
   - Não antecipe funcionalidades de passos futuros
   - Execute os testes e confirme que estão **passando** (green)

3. **🔵 Refactor** — Melhore o código sem quebrar os testes.
   - Elimine duplicação, melhore nomes, extraia métodos
   - Execute os testes novamente e confirme que continuam **verdes**

4. **Commit atômico** — Após o ciclo Red/Green/Refactor de cada passo, faça um commit atômico:
   ```
   git add <arquivos do passo>
   git commit -m "feat(TICKET): <descrição do passo> — TDD Green"
   ```

### Como executar testes e commits por runtime

Use a ferramenta bash em cada fase do ciclo:
```bash
# Red / Green — rodar apenas a classe do passo atual
./mvnw test -Dtest=NomeDaClasse --no-transfer-progress 2>&1 | tail -20

# Validação final após todos os passos (G3 — prefira sdd-verify se existir)
bash sdd-verify.sh
# fallback: ./mvnw clean test --no-transfer-progress

# Commit atômico
git add <arquivos> && git commit -m "feat(TICKET): <desc> — TDD Green"
```

**Regras invioláveis do TDD:**
- Nunca edite um teste para fazê-lo passar — ajuste o código de produção
- Nunca enfraqueça asserts (remova verificações, relaxe thresholds, adicione `@Disabled`)
- Nunca avance para o próximo passo sem o ciclo Red/Green/Refactor concluído
- Se um teste existente quebrar durante a implementação, investigue e corrija o código — não o teste

## Step 7 — Add / update tests

For each entry in `task.md → Tests to Add/Update`:
- Create or update the test class inside `PROJECT/src/test/`
- Cover: happy path, validation errors, exceptions, edge cases
- Use the same testing libraries and patterns already used in the project
- Unit tests: `@ExtendWith(MockitoExtension.class)` — no Spring context
- Controller tests: `@WebMvcTest` — no `@SpringBootTest`
- Use `@MockitoBean` instead of the deprecated `@MockBean` in Spring test slices
- For `@WebMvcTest`, inject `MockMvc` and use `.perform()` with `MockMvcRequestBuilders`
- Negative scenarios are mandatory: test HTTP 400, 404, 409, 422, 500 as appropriate
- Use `.as('response')` alias pattern in Cypress tests for chained assertions
- Test names must follow `metodo_cenario_comportamentoEsperado` convention
- Ensure every test is independent: no shared mutable state between test methods

## Step 8 — Update spec status

After implementation, update `task.md`:
- Change `Status` from `analysis` to `implemented`
- Fill `Decisions Made` with decisions taken during implementation
- Close resolved `Open Questions` with the answers found

## Step 9 — Summary

Report:
- Files created or modified (with layer)
- Tests added or updated (with scenarios covered)
- Risks identified during implementation
- How to validate locally (commands, endpoints, scenarios)
- Related spec: ticket and acceptance criteria verified

## Rules

- Do not implement before completing Steps 2–4 and receiving confirmation in Step 5.
- Do not invent requirements not present in the spec or inferable from code.
- Do not create broad refactors unless explicitly in the Implementation Plan.
- Do not change public contracts unless the spec says so.
- Always update `task.md` status after implementation.

---

## Ao Finalizar — Obrigatório

Atualize `{SPEC_PATH}session-state.md` (caminho resolvido no Passo 0) com os seguintes campos:

`last_runtime: claude-code`

| Campo             | Valor                                                           |
|-------------------|-----------------------------------------------------------------|
| status            | implemented                                                     |
| last_agent        | sdd-implement-spec                                              |
| last_runtime      | conforme runtime acima                                          |
| last_run          | \<timestamp ISO 8601\>                                          |
| next_agent        | sdd-generate-integration-tests                                  |
| next_instruction  | Gerar testes de integração para os fluxos implementados no ticket |
| blocked_on        | — (ou descreva se houver impedimento)                           |

Escreva um **Checkpoint** descrevendo:
- Quais arquivos foram criados ou modificados (com caminho relativo)
- Quais arquivos da lista `Affected Files` do `task.md` ainda não foram tocados (se houver)
- Quais testes foram adicionados ou atualizados
- Qualquer decisão relevante tomada durante a implementação

Adicione uma linha no `Agent History`:

```
| <timestamp> | sdd-implement-spec | <runtime> | Implementação concluída — <N> arquivos modificados, <M> testes adicionados |
```

Se a implementação foi **interrompida antes de terminar**, escreva o checkpoint assim mesmo, indicando o que falta:
> "Parou após criar `<último arquivo>`. Faltam: `<lista de arquivos pendentes>` conforme `task.md §Affected Files`."
