---
mode: agent
author: "Felipe Mauricio da Silva"
description: "Orquestrador do SDD Kit. Conduz uma demanda com etapas toggleable (tests/review/docs), quality gates configuráveis (auto/confirm/skip) e 3 checkpoints humanos. Modos --step e --run. Uso: /sdd-bootstrap <PROJECT> <TICKET> [--run] [--profile=X] [--enable/--disable=...] [--pause-at/--auto/--skip=Gn]"
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

# SDD Bootstrap — Orquestrador do SDD Kit

Lê o estado da demanda, decide o próximo agente segundo as etapas habilitadas, executa, avalia o gate conforme sua política, e ao final de CADA ação mostra um painel de status.

- `--step` (padrão): um agente, painel, devolve controle.
- `--run`: pipeline contínuo, para só em gates `confirm`/🔒 e falhas persistentes.

## Passo 0 — Resolver caminhos (v2.5)

Antes de qualquer leitura de estado, resolva o caminho base da demanda:

1. Verifique se `<PROJECT>/.github/sdd.config.md` existe.
2. **Se existir:** leia `sdd_kit:`, `project:` e `sdd_workspace:`. Resolva `sdd_kit` como caminho relativo à raiz do projeto.
   - Se `sdd_workspace:` definido: `SPEC_PATH = {sdd_workspace}/{project}/specs/<TICKET>/`
   - Caso contrário: `SPEC_PATH = {sdd_kit}/workspace/{project}/specs/<TICKET>/`
   - Gates config fallback (após `<PROJECT>/.github/sdd-gates.config.md`): `{sdd_kit}/templates/sdd-gates.config.md`
3. **Se não existir** (instalação pré-v2.5):
   - `SPEC_PATH = <PROJECT>/.github/docs/specs/<TICKET>/`

Use `SPEC_PATH` em **todos** os acessos a `session-state.md`, `task.md` e demais arquivos da demanda nesta execução.

---

## Passo 1 — Argumentos e configuração
```
/sdd-bootstrap <PROJECT> <TICKET> [--run] [--profile=safe|fast|paranoid|yolo]
   [--enable=tests,review,docs] [--disable=tests,review,docs]
   [--pause-at=Gn] [--auto=Gn] [--skip=Gn] [--force-skip=G6]
```
Precedência: flags > estado no session-state > `<PROJECT>/.github/sdd-gates.config.md` > `{sdd_kit}/templates/sdd-gates.config.md` (kit default) > default (`safe`, tudo enabled).
- Etapas core (`analyze`, `implement`) não podem ser desabilitadas.
- Gates 🔒 (G2/G5/G6) só vão a `auto`/`skip` com flag nominal ou `--profile=yolo`. `skip` em G6 exige `--force-skip=G6`. `yolo` exibe aviso.

## Passo 2 — Estado
Leia `{SPEC_PATH}session-state.md` (caminho resolvido no Passo 0; derive de `status-task.md` via template se faltar). Se `awaiting_checkpoint` preenchido → Passo 6.

**Reconciliação de estado herdado (PROIBIDO confiar cegamente):**
Se a etapa atual foi marcada `done` por **outro runtime** (`last_runtime` ≠ runtime atual) ou sem evidência de execução real, NÃO aceite os gates `auto` associados como `passed`. Rebaixe cada gate `auto` herdado para `pending` e reexecute a verificação real (Passo 5). **Nunca** registre `passed (reconcile)` num gate `auto` — `reconcile` só vale para gates `confirm` já aprovados por humano (CP1/CP2/CP3 com decisão registrada). Copilot não roda terminal: qualquer `G3:passed` vindo dele é não-confiável e deve ser revalidado.
## Passo 3 — Runtime
GitHub Copilot → `github-copilot` · Claude Code → `claude-code`. Detecte pelo contexto de execução e registre em `last_runtime`.
## Passo 4 — Roteamento dinâmico + modo
Sequência: `analyze → implement → [tests] → [review] → [docs] → done`.
`next_agent` = primeira etapa `enabled` a partir da posição atual; pula `disabled`; sem mais enabled → avalia G6 → `done`.

**--step:** painel → `[S/N/A]` → executa um → avalia gate → persiste → painel.
**--run (loop):**
```
ENQUANTO status != done E awaiting_checkpoint vazio:
  next = roteamento dinâmico
  se next == implement E G2.policy != auto E G2 pending → CHECKPOINT 1, pare
  executa next → avalia gate conforme policy → persiste → painel
ao fim: avalia G6 → done
```
### Sequência de tests + review (Copilot)

Copilot não tem Agent tool — execute `tests` e `review` em sequência:
1. Execute `sdd-generate-integration-tests PROJECT TICKET` (se `tests` enabled).
2. Execute `sdd-review-code PROJECT TICKET` (se `review` enabled).
3. Avalie G4 e G5 sequencialmente.
## Passo 5 — Policy do gate
- `auto`: avalia **com evidência real**; passed→avança; failed→Recuperação (≤2 retry com erro no contexto; >2 escala ao humano).
- `confirm`: avalia mas SEMPRE pausa p/ confirmação humana.
- `skip`: marca `skipped`, avança (G6 bloqueado sem `--force-skip`).
Se a etapa do gate está `disabled` → gate `skipped`.

**G3 (build-green) exige execução real — sem exceção:**
`--disable=tests` desliga só o G4 (integração), NUNCA o G3. Para marcar G3 `passed` você DEVE rodar o build de fato no terminal e ver sucesso.

Prefira o script padronizado (quando existir na raiz do projeto):
```bash
bash sdd-verify.sh          # Linux/Mac
pwsh sdd-verify.ps1         # Windows — leia a linha SDD-VERIFY | RESULT=
```
Se não existir `sdd-verify`, use `./mvnw clean test` / `npm test` conforme o projeto.
Antes de rodar qualquer build, garanta `JAVA_HOME` na versão do `pom.xml`. Se o build falhar → G3 `failed` → Recuperação. **Proibido** marcar G3 `passed` por suposição, herança de outro runtime ou ausência de terminal.

## Passo 6 — Checkpoints
- CP1 (G2): Implementation Plan + Affected Files. `[S aprovar/E editar/N abortar]`.
- CP2 (G5): achados 🔴. `[C corrigir→implement / I ignorar c/ justificativa / N abortar]`.
- CP3 (G6): resumo de validação. `[S abrir PR / N depois]`.

## Passo 7 — Painel (ao fim de cada ação)
```
✓ AÇÃO CONCLUÍDA — <agente>   [modo · profile]
Gate <Gn>: <status> [<policy>] · Runtime: <runtime>

Pipeline Steps:
  ✓ analyze  ▸ implement  ◯ tests(DISABLED)  ● review[G5:confirm]  ● docs[G6:confirm]
Quality Gates:
  G1[auto]✓  G2[confirm]✓  G3[auto]✓  G4[—]⊘disabled  G5[confirm]pending  G6[confirm]pending
Próximo: <next_agent> (<motivo>)
```
Símbolos: `✓`concluído `▸`atual `▶`running(paralelo) `●`enabled `◯`disabled.

## Passo 8 — Persistir
Campos do estado + Pipeline Steps + Quality Gates (Policy/Status) + Checkpoint + Agent History (append-only):
`| ts | agent@version | <runtime> | mode | Gn:status[policy] | resultado |`.

**Versionamento:** antes de executar cada agente, leia o campo `version:` do seu frontmatter. Registre no Agent History como `agent@versão`. Se a versão mudou desde a última entrada do mesmo agente, exiba aviso no painel: `⚠️ Versão do agente atualizada (anterior → nova) — revise o comportamento`.

## Passo 9 — Recuperação de falha
1. Incremente `retries`.
2. `retries` ≤ 2 → reexecute o agente com o erro injetado no contexto.
3. `retries` > 2 → escale ao humano, preencha `blocked_on`, pare. `[V/M/N]`.
4. Ao resolver, zere `retries`.

## Tabela de Fluxo

| Etapa | Agente | Gate | Toggleable |
|-------|--------|------|------------|
| analyze   | sdd-analyze-demand             | G1 | não |
| implement | sdd-implement-spec             | G2 → G3 | não |
| tests     | sdd-generate-integration-tests | G4 | sim |
| review    | sdd-review-code                | G5 | sim |
| docs      | sdd-update-documentation       | G6 (fim) | sim |

## Perfis

| Perfil | G1 | G2 | G3 | G4 | G5 | G6 |
|--------|----|----|----|----|----|----|
| safe | auto | confirm | auto | auto | confirm¹ | confirm |
| fast | auto | auto | auto | auto | confirm¹ | confirm |
| paranoid | confirm | confirm | confirm | confirm | confirm | confirm |
| yolo | auto | auto | auto | auto | auto | auto |

¹ G5 pausa só se houver 🔴.

## Regras
- `--run` só para em `confirm`/🔒 e falhas. Core nunca desabilitado.
- Nunca mascare gate falho; nunca escreva código direto (delegue).
- **Gate `auto` nunca vira `passed` sem evidência real de execução neste runtime.** Estado herdado de outro runtime é sempre revalidado, nunca reconciliado.
- Sempre mostre o painel e persista o estado. Agent History append-only.
