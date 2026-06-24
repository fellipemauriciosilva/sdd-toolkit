# SDD Kit — Roadmap

> Última atualização: 2026-06-22 (v3.1 implementado — `templates/` na raiz, `.github/` somente metadados do kit)

---

## O que é este documento

Registro das decisões arquiteturais tomadas na evolução do SDD Kit e do plano de melhorias futuras. Serve como referência para onboarding de novos colaboradores e como backlog técnico priorizado.

---

## Histórico de Evolução

### Versão 1.0 — Kit Base (estado inicial)

**O que existia:**
- 38 agentes: 15 sem prefixo `sdd-`, vários redundantes entre si
- Agentes organizados por papel isolado (reviewer, developer, qa-engineer, architect etc.) sem orquestração entre eles
- `status-task.md` rastreava o estado de cada demanda, mas apenas por ticket — sem visibilidade de sessão ou runtime
- Usuário era o orquestrador: escolhia manualmente qual agente invocar a cada passo
- Nenhum mecanismo de retomada automática ao trocar entre GitHub Copilot e Claude Code
- Fluxo SDD existia conceitualmente mas não era executado de forma contínua

**Classificação N0–N5:** **N2** — Workflow LLM predefinido, etapas fixas, orquestração 100% humana.

---

### Versão 2.0 — Consolidação e Estado Persistente

**Decisões tomadas:**
- Consolidação de 38 → 18 agentes, todos com prefixo `sdd-`
- Absorção do conhecimento dos agentes não-SDD nos agentes SDD correspondentes:
  - `reviewer` + 5 sub-revisores → `sdd-review-code` (multi-dimensional: arquitetura, corretude, qualidade, OWASP, testes)
  - `developer` + `task-worker` → `sdd-implement-spec` (TDD Red→Green→Refactor + commits atômicos)
  - `qa-engineer` → `sdd-generate-integration-tests` (+ exportação Zephyr Scale)
  - `architect` → `sdd-architect` (+ Well-Architected Framework + C4)
  - `code-lens` + `sdd-analyze-project` + `sdd-fill-project-context` → `sdd-setup-project`
  - `sdd-read-doc` + `sdd-read-pdf` → `sdd-read-document`
  - `sdd-map-infra-credentials` + `sdd-kubectl-inspector` + `gda-devops` → `sdd-inspect-infra`
- Criação do `session-state.md` como **fonte de verdade entre runtimes**
- Criação do `sdd-bootstrap` como proto-orquestrador (modo passo-a-passo)
- Agente global no Claude Code: `~/.claude/agents/sdd-bootstrap.md`
- Bloco "Ao Finalizar" adicionado em todos os agentes do fluxo principal — cada agente escreve o próximo passo

**Resultado:** qualquer demanda pode ser retomada em qualquer runtime com um único comando. O arquivo `session-state.md` contém o checkpoint exato de onde o trabalho parou.

**Classificação N0–N5:** **N3** — Workflow com tools, estado persistente, orquestração ainda humana (um agente por vez).

---

### Versão 2.1 — Orquestrador Autônomo com Quality Gates

**Decisões tomadas:**
- `sdd-bootstrap` evoluiu de menu interativo para **orquestrador com loop**
- Dois modos de operação:
  - `--step`: um agente por vez, devolve controle ao humano (comportamento anterior preservado)
  - `--run`: pipeline contínuo, para apenas em quality gates e checkpoints humanos
- **6 Quality Gates** definidos no `session-state.md`:
  - G1 spec-complete (auto): task.md com Demand Summary + Expected Behavior
  - G2 plan-approved (🔒 humano): aprovar plano antes de qualquer código
  - G3 build-green (auto): compilação + testes unitários passam
  - G4 tests-present (auto): testes de integração gerados ou skip justificado
  - G5 review-clean (🔒 se 🔴): nenhum achado Crítico em aberto
  - G6 pr-approved (🔒 humano): PR autorizado para abertura
- **3 Checkpoints humanos** explícitos: plano, crítico no review, PR
- **Recuperação de falha automática**: até 3 tentativas com erro injetado no contexto; escala para humano se persistir
- `session-state.md` expandido: campos `run_mode`, `awaiting_checkpoint`, `retries` e tabela de Quality Gates
- Nota de paralelização no Claude Code: `sdd-generate-integration-tests` e leitura do `sdd-review-code` podem rodar como subagents paralelos

**O que mudou na prática:** o humano não confirma mais cada passo. Digita um único comando (`--run`) e só é chamado para decisões que realmente precisam de julgamento humano.

**Classificação N0–N5:** **N4** — Agent único com loop, tools, avaliação dinâmica de qualidade e critérios de parada explícitos.

---

### Versão 2.2 — Controle Granular: Políticas de Gate e Etapas Toggleable

**Decisões tomadas:**
- **Política por gate** em 3 valores: `auto` (avalia e avança), `confirm` (sempre pausa), `skip` (não avalia)
- **Precedência de 4 camadas**: flag na invocação → policy no session-state → `.github/sdd-gates.config.md` → default (`safe`)
- **Perfis** como atalho de configuração: `safe`, `fast`, `paranoid`, `yolo`
- **Flags de política**: `--profile`, `--pause-at`, `--auto`, `--skip`, `--force-skip`
- **Etapas toggleable**: `tests`, `review`, `docs` podem ser `enabled`/`disabled` via `--enable`/`--disable`. Etapas core (`analyze`, `implement`) são imutáveis
- **Roteamento dinâmico**: quando uma etapa está `disabled`, o orquestrador recalcula `next_agent` pulando-a
- **Painel de status pós-ação**: ao final de cada agente, exibe o que aconteceu, quais etapas estão habilitadas/desabilitadas e a política de cada gate
- **Regras de segurança**: gates 🔒 (G2/G5/G6) só relaxam com flag nominal explícita ou `--profile=yolo`; `skip` no G6 exige `--force-skip`
- `session-state.md` expandido: campo `profile`, tabela `Pipeline Steps`, coluna `Policy` na tabela de gates
- Novo arquivo `.github/sdd-gates.config.md` — configuração default do projeto

**O que mudou na prática:** o controle deixou de ser binário (`--step` vs `--run`). Agora cada gate e cada etapa opcional é configurável por demanda ou por projeto, e o usuário é informado do estado completo do pipeline após cada ação.

**Classificação N0–N5:** **N4** — mesma classe, com controle de execução muito mais fino e auditável.

---

### Versão 2.3 — Integridade de Gates: Fim do "Reconcile" em Gates Automáticos

**Motivação (incidente real):** Ao retomar a demanda `MIGRACAO-ONDA-0` (migração do `gcb-hr-api-gestao-meta`, iniciada no GitHub Copilot e continuada no Claude Code), o `sdd-bootstrap` marcou o pipeline como `done` com **G3 (build-green) verde — sem nunca ter compilado o projeto**. O build real estava quebrado em três frentes (JAVA_HOME apontando para JDK 17 com `pom` exigindo Java 21, 35 violações de `spotless`, use cases incompletos).

**Causa raiz:** O bootstrap fez uma "reconciliação de estado" — leu no `Agent History` que o Copilot havia registrado `G3:passed[auto]` e **confiou nesse registro** em vez de reexecutar o build. O agravante: o GitHub Copilot **não executa terminal**, então aquele `passed` original era fictício desde a origem. A reconciliação apenas propagou a mentira. Era exatamente o risco previsto no backlog ("G3 com resultado real degrada para 'assumir que passou'"), agora materializado.

**Decisões tomadas:**
- **Proibição do `passed (reconcile)` em gates `auto`.** O termo `reconcile` passa a valer **somente** para gates `confirm`/🔒 cuja decisão humana (CP1/CP2/CP3) já está registrada. Gate `auto` só vira `passed` com **evidência real de execução no runtime atual**.
- **Revalidação obrigatória de estado herdado.** Quando `last_runtime` ≠ runtime atual (ou não há evidência de execução), todo gate `auto` herdado (G1/G3/G4) é rebaixado para `pending` e reexecutado.
- **G3 exige terminal, sem exceção.** Esclarecido que `--disable=tests` desliga **apenas o G4** (testes de integração) — o G3 (build + unitários) **nunca** é pulado por esse flag. Marcar G3 sem rodar `./mvnw clean test` (ou equivalente) é proibido.
- **Checagem de ambiente no G3.** O agente deve conferir `JAVA_HOME`/`mvn -version` contra a versão do `pom.xml` antes de validar o build (o `java -version` do PATH pode divergir do JDK que o Maven usa). Falha de `spotless`/format também reprova o G3.
- **Escalada honesta.** Runtime sem terminal para validar um gate `auto` herdado → para, preenche `blocked_on` e escala ao humano. Nunca propaga `passed`.

**O que mudou na prática:** o pipeline deixou de poder "mentir verde". Um gate automático agora é uma afirmação verificável, não um campo herdado. Estado escrito por um runtime sem terminal nunca mais conclui uma demanda sozinho.

**Arquivos alterados:** `.github/agents/sdd-bootstrap.agent.md` (Copilot) e `~/.claude/agents/sdd-bootstrap.md` (Claude Code) — Passo 2 (reconciliação), Passo 5 (evidência real do G3) e Regras.

**Classificação N0–N5:** **N4+** — mesma classe, com integridade de gates reforçada. Pré-requisito para o item "G3 com resultado real" (script `sdd-verify`) sair do backlog.

---

### Versão 2.4 — Backlog Completo: Paralelismo, Evals, Versionamento e Templates

**Decisões tomadas (8 itens implementados):**

**Alta prioridade:**
- **Paralelização real (tests + review):** `sdd-bootstrap` (Claude Code) agora dispara `sdd-generate-integration-tests` e `sdd-review-code` como subagents paralelos via Agent tool após `implement` + G3 passed, quando ambos estiverem habilitados. Novos estados intermediários: `tests:running` e `review:running` (exibidos como `▶` no painel). Copilot mantém sequencial.
- **Script `sdd-verify` padronizado:** `sdd-install-sdd-kit` agora cria `sdd-verify.sh` e `sdd-verify.ps1` na raiz de projetos Java. Saída estruturada com prefixo `SDD-VERIFY | RESULT=PASSED/FAILED`. Bootstrap usa o script se existir; cai back para `./mvnw clean test` caso contrário. G3 completamente resolvido.

**Média prioridade:**
- **PIPELINE-STATUS.md:** `sdd-workspace-sync` gera automaticamente `.github/PIPELINE-STATUS.md` com pass rate por gate, demandas bloqueadas, demandas em checkpoint e histórico agregado de todos os projetos.
- **Versionamento de agentes (semver):** `version: "2.3.0"` adicionado ao frontmatter de todos os 18 agentes. Bootstrap registra versão no Agent History como `agente@versão` e avisa quando a versão mudou desde a última execução da demanda.
- **Evals dos 7 agentes principais:** Framework de evals criado em `.github/evals/` com 3 casos por agente (21 casos totais, 63 arquivos: `input.md` + `expected.md` + `rubric.md`). Score mínimo definido por agente. Critérios bloqueantes explícitos nas rubricas.
- **Multi-projeto por ticket:** Campo `affected_projects` adicionado ao template `session-state.md`. `sdd-implement-spec` cria sub-plan por projeto afetado e faz commits separados. Falha em qualquer projeto para o pipeline.

**Baixa prioridade:**
- **Templates spec por tipo:** 4 variantes criadas em `.github/docs/specs/_template/types/`: `task-feature.md`, `task-bugfix.md`, `task-refactor.md`, `task-migration.md`. Cada variante tem seções específicas ao tipo. `sdd-create-spec` pergunta o tipo se não informado e usa o template correspondente.
- **Decision log por projeto:** Template `decisions-log.md` criado em `.github/docs/project-context/`. `sdd-install-sdd-kit` o inclui na instalação. `sdd-update-documentation` faz append das decisões de `Decisions Made` a cada demanda concluída. `sdd-implement-spec` lê o log antes de analisar código para detectar conflitos.

**Classificação N0–N5:** **N4 (v2.4)** — qualidade, observabilidade, evals e paralelismo operacionais. Estado atual: N4 (v3.1) com source único, compilador e estrutura `templates/`. Próximo salto: N5 (trigger externo + notificação assíncrona de checkpoints).

---

### Versão 2.5 — Kit como Produto: Workspace Centralizado _(implementado em 2026-06-22)_

**Motivação:** Hoje o kit instala engines (agentes), contexto (copilot-instructions, AGENTS.md) e **estado** (specs, session-states, decisions-log) todos dentro do projeto do cliente. Isso acopla o kit ao projeto, impede visibilidade cross-project e força o cliente a versionar artefatos de pipeline junto com código de produção. O kit está sendo tratado como um conjunto de arquivos a copiar, não como um produto a instalar.

**Status de implementação:** ✅ Implementado. `sdd-toolkit/workspace/` criado, `sdd.config.md` instalado em `gcb-hr-api-gestao-meta`, bootstrap e todos os sub-agentes atualizados com Passo 0 de resolução de caminhos, `install.sh`/`install.ps1` criados, `runtimes/copilot.yaml` e `runtimes/claude.yaml` criados como stubs.

**Decisões tomadas:**

**Separação em 2 tiers:**

| Tier | O que contém | Onde vive |
|------|-------------|-----------|
| **Kit** | agents, templates, evals, scripts | `sdd-toolkit/` |
| **Workspace** | specs, session-states, PIPELINE-STATUS | `sdd-toolkit/workspace/{project}/` |
| **Projeto** | código, copilot-instructions, AGENTS.md, module-map, decisions-log | `{project}/.github/` |

O `decisions-log.md` permanece no projeto (é contexto que o desenvolvedor consulta enquanto lê o código; o Copilot também o usa). O workspace centraliza apenas o estado volátil do pipeline.

**`sdd.config.md` — o arquivo pivô:**
Instalado pelo `sdd-install-sdd-kit` na raiz de cada projeto em `.github/sdd.config.md`:
```yaml
project: gcb-hr-hub
sdd_kit: ../sdd-toolkit
version_required: "2.4"
```
Campo `sdd_kit` pode ser relativo ao project root, absoluto, ou variável de ambiente `$SDD_KIT_HOME`.

**Resolução de caminhos no bootstrap (4 passos):**
1. Lê `{project}/.github/sdd.config.md` → extrai `project` e `sdd_kit`
2. Resolve `sdd_kit`: relativo → join com project root; fallback → `$SDD_KIT_HOME`; fallback → busca `sdd-toolkit/` nos diretórios pai
3. Monta paths derivados: `workspace = {sdd_kit}/workspace/{project}/`, `spec_types = {sdd_kit}/templates/specs/types/`
4. Contexto do projeto (leitura only): sempre de `{project}/.github/`

**Config em camadas para `sdd-gates.config.md`:**
```
Prioridade 1 — flag na invocação           (--disable=review)
Prioridade 2 — {project}/.github/sdd-gates.config.md   (override do projeto)
Prioridade 3 — {sdd_kit}/templates/sdd-gates.config.md   (default do kit)
```
Projetos sem opinião sobre gates herdam o default do kit sem precisar de arquivo.

**O que `sdd-install-sdd-kit` passa a fazer (v2.5):**

| Artefato | Copilot | Claude Code |
|----------|---------|-------------|
| Agentes | ainda copiados para `.github/agents/` ¹ | bootstrap global em `~/.claude/agents/` (no kit) |
| `copilot-instructions.md`, `AGENTS.md`, `instructions/` | criados no projeto | idem |
| `.github/sdd.config.md` | criado no projeto | idem |
| `sdd-verify.sh`/`.ps1` | criados no projeto | idem |
| `docs/specs/` | **não cria mais** — vai para workspace | idem |

¹ O Copilot exige que os agentes estejam em `.github/agents/` dentro do projeto — não consegue ler de um diretório externo. Em v2.5 os agentes continuam sendo copiados para o projeto no caso do Copilot. A eliminação dessa duplicação é o objetivo da v3.0 (compilador gera os artefatos sob demanda em vez de serem mantidos manualmente).

**Habilitado para N5:** com workspace como pasta, a troca para cloud storage (branch git, banco, blob storage) só muda o resolver de caminhos — os agentes não precisam mudar.

**O que muda na prática:** `git status` no projeto do cliente mostra apenas código e contexto. Specs, session-states e pipeline history ficam no kit, versionados independentemente.

---

### Versão 3.0 — Agentes Runtime-Agnostic: Source Único + Compilação _(implementado em 2026-06-22)_

**Motivação:** Hoje cada agente existe em dois arquivos com ~90% de conteúdo idêntico: `.github/agents/sdd-bootstrap.agent.md` (Copilot) e `.claude/agents/sdd-bootstrap.md` (Claude Code). Qualquer mudança na lógica do agente deve ser replicada nos dois lugares. Com novos runtimes emergindo (Cursor, Windsurf, SDK headless para N5), manter N cópias não é escalável. O kit precisa de um source canônico que compile para cada target.

**Decisões tomadas:**

**Nova estrutura de diretórios do kit:**
```
sdd-toolkit/
├── agents/                    ← SOURCE OF TRUTH (novo)
│   ├── sdd-bootstrap.md       ← lógica pura, sem frontmatter
│   ├── sdd-analyze-demand.md
│   └── ...
├── runtimes/                  ← ADAPTERS por runtime (novo)
│   ├── copilot.yaml
│   ├── claude.yaml
│   └── cursor.yaml            ← (futuro)
└── dist/                      ← GERADO pelo sdd-install-sdd-kit
    ├── copilot/
    └── claude/
```

**Runtime adapter (ex: `runtimes/copilot.yaml`):**
```yaml
target: copilot
output: .github/agents/{name}.agent.md
frontmatter:
  mode: agent
  tools: [codebase, terminal, fetch]
  description: "{description}"
install_path: "{project}/.github/agents/"
```

**Seções condicionais no corpo do agente:**
```markdown
<!-- @all -->
Conteúdo compartilhado entre todos os runtimes.

<!-- @claude -->
Dispare tests e review como subagents paralelos via Agent tool.

<!-- @copilot -->
Execute tests e review em sequência.
```
O compilador inclui `@all` e a seção do runtime alvo; remove as demais.

**`sdd-install-sdd-kit` vira um compilador:**
```
sdd-install-sdd-kit --runtime=copilot --project=gcb-hr-hub

  1. Lê agents/*.md (source)
  2. Lê runtimes/copilot.yaml (adapter)
  3. Para cada agente:
     a. Injeta frontmatter do runtime
     b. Filtra @copilot + @all, remove @claude
     c. Escreve em dist/copilot/ e copia para {project}/.github/agents/
```

**Contrato de um agente SDD:**

| Camada | Conteúdo | Runtime-specific? |
|--------|---------|:-----------------:|
| Metadata | name, version, description | não |
| Lógica core (`@all`) | pipeline, gates, session-state protocol | não |
| Overrides (`@claude`/`@copilot`) | paralelismo, tool calls específicos | sim |

**Progressão de implementação:**
- **v2.4:** dois arquivos, lógica duplicada — estado anterior
- **v2.5:** `runtimes/copilot.yaml` e `runtimes/claude.yaml` criados como stubs; `install.sh`/`install.ps1` criados; agent é thin wrapper ✅
- **v3.0:** mover 18 agentes para `agents/` (source único), marcar seções `@all/@claude/@copilot`, implementar compilador (~100 linhas), `dist/` gerado automaticamente

**O que muda na prática:** adicionar suporte a um novo runtime significa criar um `runtimes/novo.yaml` de ~10 linhas. O conteúdo dos 18 agentes não precisa mudar.

---

---

### Versão 3.1 — Estrutura do Kit: `templates/` e limpeza de `.github/` _(implementado em 2026-06-22)_

**Motivação:** Com v3.0, os agentes saíram de `.github/agents/` para `agents/`. Ficou aparente que `.github/` mistura dois papéis incompatíveis: (1) metadados do repo GitHub (README, ROADMAP, evals, images) e (2) recursos deployáveis nos projetos (instructions, skills, templates de spec/session-state, sdd-gates.config.md). O papel (2) não tem relação com GitHub — são insumos do compilador e do install. Separar os dois torna o kit mais legível e prepara a estrutura para N5 (CI/CD).

**Decisões tomadas:**

**Nova estrutura de diretórios do kit após v3.1:**
```
sdd-toolkit/
├── agents/             ← source única dos 18 agentes
├── dist/               ← artefatos compilados (gerado)
├── runtimes/           ← adapters por runtime
├── templates/          ← recursos deployados a projetos (NOVO)
│   ├── instructions/   ← ← de .github/instructions/
│   ├── skills/         ← ← de .github/skills/
│   ├── specs/
│   │   └── types/      ← ← de .github/docs/specs/_template/types/
│   ├── session-state.md ← ← de .github/agents/_template/session-state.md
│   ├── decisions-log.md ← ← de .github/docs/project-context/decisions-log.md
│   └── sdd-gates.config.md ← ← de .github/sdd-gates.config.md
├── workspace/          ← specs e session-states por projeto
├── install.sh
├── install.ps1
└── .github/            ← SOMENTE metadados do repo
    ├── README.md
    ├── ROADMAP.md
    ├── sdd-kit-status.md
    ├── evals/
    └── images/         ← somente PNGs finais (sem _* intermediários)
```

**Referências atualizadas:**

| Quem | Antes | Depois |
|------|-------|--------|
| `install.ps1`/`install.sh` | `.github/sdd-gates.config.md` | `templates/sdd-gates.config.md` |
| `agents/sdd-bootstrap.md` | `{sdd_kit}/.github/sdd-gates.config.md` | `{sdd_kit}/templates/sdd-gates.config.md` |
| `agents/sdd-create-spec.md` | `{sdd_kit}/.github/docs/specs/_template/types/` | `{sdd_kit}/templates/specs/types/` |
| `agents/sdd-update-documentation.md` | `.github/docs/project-context/decisions-log.md` | `{sdd_kit}/templates/decisions-log.md` |
| `agents/sdd-read-document.md` | `.github/skills/{skill}/SKILL.md` | `{sdd_kit}/templates/skills/{skill}/SKILL.md` |

**Limpeza de `.github/images/`:**
- Deletar arquivos `_*` (fontes intermediárias: `_diagrama-1-ecossistema.html`, `_diagrama-2-pipeline.html`, `_diagramas-readme.html`, `_diagramas-completo.png`, `_screenshot-diagramas.js`)
- Manter apenas os PNGs finais referenciados pelo README

---

**Decisão adicional (2026-06-22): `sdd-install-sdd-kit` vira CLI script, não agente**

**Problema identificado:** O agente `sdd-install-sdd-kit.agent.md` vive em `.github/agents/`, o que força o instalador a rodar **somente via GitHub Copilot** com o kit aberto no IDE. Claude Code, GitHub Actions e o terminal não conseguem invocar o install de forma autônoma.

**Decisão tomada:** O install é refatorado como um **script CLI independente de runtime**:

```
sdd-toolkit/
  install.sh        ← instalador principal (Linux/Mac/Git Bash)
  install.ps1       ← instalador principal (Windows/PowerShell)
  runtimes/         ← adapters de runtime (stubs em v2.5, lidos pelo compilador em v3.0)
```

O agente `.github/agents/sdd-install-sdd-kit.agent.md` torna-se um **thin wrapper** que detecta o OS e delega para o script:

```
# Como cada runtime invoca o install
Claude Code     → Bash tool: bash install.sh PROJECT --runtime=all
Copilot         → thin wrapper agent chama o script via terminal
GitHub Actions  → run: bash install.sh ${{ inputs.project }} --runtime=copilot
Terminal humano → bash install.sh PROJECT --runtime=all
```

**O que foi implementado em v2.5:**
- `install.sh` criado — resolve caminho relativo, cria workspace, `sdd.config.md`, copia agentes por runtime
- `install.ps1` criado — equivalente para Windows PowerShell
- `runtimes/copilot.yaml` e `runtimes/claude.yaml` criados como stubs do compilador v3.0
- `sdd-install-sdd-kit.agent.md` reescrito como thin wrapper (Passo 1: coletar args; Passo 2: detectar KIT_ROOT; Passo 3: executar script; Passo 4: pós-instalação)

**Consequência para N5:** o mesmo `install.sh` que roda localmente é o que a GitHub Action usa. Nenhuma duplicação de lógica entre runtimes.

---

## Agentes Atuais (18)

### Fluxo Principal (7)

| Agente | Responsabilidade | Gates associados |
|--------|-----------------|-----------------|
| `sdd-bootstrap` | Orquestrador — lê estado, executa loop, avalia gates | todos |
| `sdd-create-spec` | Scaffolda pasta da demanda com formulário de contexto | — |
| `sdd-analyze-demand` | Lê docs, preenche task.md, MoSCoW, decomposição de épicos | G1 |
| `sdd-implement-spec` | Analisa código, TDD Red→Green→Refactor, commits atômicos | G2, G3 |
| `sdd-generate-integration-tests` | Testes E2E por fluxo (BDD/Cypress) + Zephyr Scale | G4 |
| `sdd-review-code` | Revisão multi-dimensional: spec, arquitetura, corretude, qualidade, OWASP, testes | G5 |
| `sdd-update-documentation` | Atualiza project-context/, architecture/, specs/ | G6 |

### Setup (3)

| Agente | Responsabilidade |
|--------|-----------------|
| `sdd-install-sdd-kit` | Instala o kit completo em um novo projeto |
| `sdd-workspace-sync` | Catálogo de repositórios + painel de demandas + métricas de sprint |
| `sdd-setup-project` | Discovery técnico completo + docs de contexto + índice DeepWiki |

### Especializados (8)

| Agente | Responsabilidade |
|--------|-----------------|
| `sdd-investigate-bug` | Investigação estruturada de bug sem alterar código |
| `sdd-refactor-code` | Refatoração com rastreabilidade e preservação de contratos |
| `sdd-read-document` | Lê Word (.docx) e PDF, extrai conteúdo estruturado |
| `sdd-architect` | ADRs, C4, Well-Architected Framework |
| `sdd-inspect-infra` | Credenciais, kubectl ConfigMaps/Secrets, ambientes sandbox GDA |
| `sdd-migrate-kustomize-to-helm` | Migração de infra Kustomize → Helm |
| `sdd-generate-tests` | Geração de testes unitários para código existente |
| `sdd-test-integration-generator` | Projeto standalone de testes (Cucumber + Testcontainers ou Cypress) |

---

## Roadmap — Backlog Priorizado

### Prioridade Alta

#### ~~v2.5 — Kit como Produto: Workspace Centralizado~~ ✅ Concluído em 2026-06-22

**Itens de implementação:**
- [x] Criar `sdd-toolkit/workspace/` com estrutura por projeto
- [x] Criar `runtimes/copilot.yaml` e `runtimes/claude.yaml` (stubs para v3.0)
- [x] `install.sh` e `install.ps1` — instalador CLI independente de runtime
- [x] Refatorar `sdd-install-sdd-kit` como thin wrapper do script CLI
- [x] Adicionar Passo 0 de resolução de caminhos no `sdd-bootstrap` (ambos runtimes)
- [x] Adicionar Passo 0 em todos os 6 sub-agentes do pipeline
- [x] Implementar cascata de configuração para `sdd-gates.config.md` (projeto → kit → default)
- [x] Migrar `workspace/{project}/` como destino padrão de specs e session-states
- [x] Atualizar `sdd-workspace-sync` para ler do workspace centralizado (dual-path: v2.5 + legado)
- [x] Criar `.github/sdd.config.md` em `gcb-hr-api-gestao-meta` + migrar session-state ativa

---

#### N5 — Trigger Externo + Checkpoints Assíncronos
**O que é:** Hoje o pipeline começa com um humano digitando `/sdd-bootstrap --run`. Para N5 real, um evento externo (label no Jira, PR aberto, webhook) dispara o pipeline automaticamente. O humano só é chamado nos 3 checkpoints via notificação assíncrona.

**Dependência:** requer v2.5 concluída (workspace centralizado é pré-requisito para execução headless).

**Como implementar:**
- GitHub Action disparado por evento (`Ready for Dev` no Jira, label no PR)
- Action invoca Claude Code SDK em modo headless via Anthropic API
- Checkpoints humanos viram notificações: comentário no PR, Slack ou email
- Workspace em cloud storage (branch git ou blob) para estado persistente em CI

**Complexidade:** alta — decisão de onde o loop executa (Claude Code SDK em CI vs. Claude API com orquestrador dedicado) e protocolo de notificação assíncrona.

---

### Prioridade Média

#### ~~v3.0 — Agentes Runtime-Agnostic: Source Único + Compilação~~ ✅ Concluído em 2026-06-22
**Decisão tomada em:** 2026-06-22 (ver seção v3.0 acima para detalhamento completo)

**Itens de implementação:**
- [x] Criar `runtimes/copilot.yaml` e `runtimes/claude.yaml` (stubs criados em v2.5)
- [x] `install.sh`/`install.ps1` como CLI independente de runtime (criados em v2.5)
- [x] `sdd-install-sdd-kit.agent.md` como thin wrapper do script (implementado em v2.5)
- [x] Criar `agents/` como source canônico — 10 agentes do fluxo principal em `.md` sem frontmatter
- [x] Auditar agentes e adicionar marcadores `@all`, `@claude`, `@copilot` (sdd-bootstrap tem seções divergentes; demais são `@all` com frontmatter compilado por runtime)
- [x] Implementar compilador em `install.sh`/`install.ps1`: lê `agents/*.md`, filtra seções, injeta frontmatter do runtime alvo
- [x] Criar `dist/copilot/` e `dist/claude/` como destinos dos artefatos compilados
- [x] Adicionar suporte a novo runtime via `runtimes/cursor.yaml` como prova de conceito ← pendente (futuro)

**Complexidade:** média — o maior esforço foi auditar os agentes, marcar seções e garantir compatibilidade do compilador com PS 5.1 (encoding ASCII, Get-RelPath custom, List&lt;string&gt; em vez de StringBuilder).

---

#### v3.1 — Estrutura do Kit: `templates/` e limpeza de `.github/` _(implementado em 2026-06-22)_

**Itens de implementação:**
- [x] Criar `templates/` na raiz com subdiretórios: `instructions/`, `skills/`, `specs/types/`
- [x] Mover `.github/instructions/` → `templates/instructions/`
- [x] Mover `.github/skills/` → `templates/skills/`
- [x] Mover `.github/docs/specs/_template/types/` → `templates/specs/types/`
- [x] Mover `.github/agents/_template/session-state.md` → `templates/session-state.md`
- [x] Mover `.github/docs/project-context/decisions-log.md` → `templates/decisions-log.md`
- [x] Mover `.github/sdd-gates.config.md` → `templates/sdd-gates.config.md`
- [x] Atualizar `install.ps1` e `install.sh`: referências `sdd-gates.config.md`
- [x] Atualizar `agents/sdd-bootstrap.md`: referência `{sdd_kit}/.github/sdd-gates.config.md`
- [x] Atualizar `agents/sdd-create-spec.md`: referência `{sdd_kit}/.github/docs/specs/_template/types/`
- [x] Atualizar `agents/sdd-update-documentation.md`: referência `.github/docs/project-context/decisions-log.md`
- [x] Atualizar `agents/sdd-read-document.md`: referências `.github/skills/`
- [x] Recompilar `dist/` com os agentes atualizados
- [x] Deletar arquivos `_*` intermediários de `.github/images/`
- [x] Remover diretórios vazios: `.github/docs/`, `.github/agents/`

---

#### Evals em CI
**O que é:** Os 21 casos de eval existem mas precisam ser executados manualmente. Integrá-los em CI garante que mudanças nos agentes não regridem comportamentos validados.

**Como implementar:** GitHub Action que executa os evals via Claude API (LLM-as-judge) e falha o build se algum agente ficar abaixo do score mínimo definido na rubrica.

**Dependência:** requer Claude API key configurada como secret no repositório.

---

### Prioridade Baixa

#### Integração nativa com Jira
**O que é:** Criar spec automaticamente ao mover ticket para "In Dev", atualizar status do ticket conforme gates passam, notificar responsável nos checkpoints.

**Dependência:** requer N5 (trigger externo) e decisão sobre onde guardar token de API do Jira.

---

#### Evals expandidos (casos por agente especializado)
**O que é:** Os 21 casos atuais cobrem os 7 agentes do fluxo principal. Os 8 agentes especializados (`sdd-architect`, `sdd-investigate-bug`, etc.) ainda não têm evals formais.

**Esforço:** 3 casos × 8 agentes = 24 casos adicionais (72 arquivos).

---

## Matriz de Maturidade Atual

| Dimensão | Status | Próximo passo |
|----------|--------|---------------|
| Agentes definidos | ✅ 18 agentes com papéis claros | — |
| Estado persistente | ✅ session-state.md por demanda | — |
| Orquestração | ✅ sdd-bootstrap com loop e gates | Trigger externo (N5) |
| Checkpoints humanos | ✅ 3 explícitos no pipeline | — |
| Recuperação de falha | ✅ retry até 3x, escala ao humano | — |
| Integridade de gates | ✅ anti-reconcile + revalidação entre runtimes (v2.3) | — |
| G3 com build real | ✅ sdd-verify.sh/.ps1 padronizado (v2.4) | — |
| Paralelismo | ✅ subagents paralelos no Claude Code (v2.4) | Copilot nativo (N5) |
| Versionamento de agentes | ✅ semver no frontmatter + aviso no bootstrap (v2.4) | — |
| Evals dos agentes | ✅ 21 casos para 7 agentes principais (v2.4) | Evals em CI (v3.0) |
| Observabilidade agregada | ✅ PIPELINE-STATUS.md via workspace-sync (v2.4) | — |
| Multi-projeto por ticket | ✅ affected_projects + sub-plan por projeto (v2.4) | — |
| Templates por tipo | ✅ feature/bugfix/refactor/migration (v2.4) | — |
| Decision log | ✅ decisions-log.md por projeto, append automático (v2.4) | — |
| Kit independente do projeto | ✅ workspace centralizado, sdd.config.md (v2.5) | — |
| Install independente de runtime | ✅ install.sh/ps1 CLI — Claude, Copilot, Actions, terminal (v2.5) | — |
| Suporte multi-runtime | ✅ `agents/` source único + compilador (`install.sh`/`ps1`) + `dist/` (v3.0) | Novo runtime: `cursor.yaml` |
| Estrutura do kit | ✅ `templates/` na raiz; `.github/` apenas metadados; separação clara fonte/deploy (v3.1) | — |
| Trigger externo | ❌ ainda manual | GitHub Action + SDK headless (N5) |
| Integração Jira | ⚠️ parcial (métricas via workspace-sync) | Webhook bidirecional |

---

## Classificação de Maturidade

```
N0  Código determinístico
N1  Chamada LLM única
N2  Workflow LLM predefinido           ← ponto de partida do kit
N3  Workflow com tools e estado        ← versão 2.0
N4  Agent com loop e quality gates     ← versões 2.1 → v3.1 (atual)
N5  Multi-agent com trigger externo    ← próximo objetivo
```

**Status atual: N4 (v3.1).** Pipeline autônomo completo com source único por agente: `agents/*.md` com seções `@all/@claude/@copilot`, compilador em `install.sh`/`install.ps1`, artefatos em `dist/copilot/` e `dist/claude/`. Recursos deployáveis em `templates/` na raiz; `.github/` contém apenas metadados do kit. O humano é chamado em 3 checkpoints definidos e em falhas persistentes.

**Próximos passos:**
- **N5** — trigger externo: GitHub Action que chama `bash install.sh` + Claude Code SDK headless, checkpoints assíncronos via notificação. Requer v2.5 como base — ✅ pré-requisito atendido.
- **Evals em CI** — GitHub Action executando os 21 casos via Claude API (LLM-as-judge).
- **cursor.yaml** — novo runtime adapter como prova de conceito do modelo v3.0.
