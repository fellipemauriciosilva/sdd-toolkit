---
name: sdd-workspace-sync
description: "Sincroniza o workspace: lista todos os repositórios presentes, gera/atualiza WORKSPACE.md na raiz e, opcionalmente, clona novos repositórios informados pelo usuário. Faz parte do kit SDD."
version: "2.5.0"
---

<!-- @all -->
# sdd-workspace-sync — Sincronização do Workspace

Mantém o catálogo `WORKSPACE.md` atualizado com todos os repositórios presentes no workspace e, quando solicitado, clona novos repos na raiz do workspace.

---

## Etapa 0 — Identificar a raiz do workspace

Execute o seguinte comando para obter o diretório raiz do workspace:

```bash
pwd
```

A raiz é o diretório que contém as pastas dos projetos. Todas as ações desta etapa em diante usam esse caminho como base. Salve como `WORKSPACE_ROOT`.

---

## Etapa 1 — Escanear repositórios existentes

Liste todos os diretórios na raiz do workspace:

```bash
ls -1d */ 2>/dev/null || dir /B /AD
```

Para cada diretório encontrado, verifique se é um repositório git:

```bash
test -d "<dir>/.git" && echo "git" || echo "not-git"
```

Para cada repositório git detectado, colete as seguintes informações **em paralelo**:

### 1.1 — Tech stack

Verifique nesta ordem de prioridade:

| Arquivo | Tech Stack detectada |
|---|---|
| `pom.xml` | Java / Spring Boot |
| `package.json` | Node.js / TypeScript |
| `build.gradle` | Java / Gradle |
| `requirements.txt` ou `pyproject.toml` | Python |
| `*.csproj` ou `*.sln` | .NET / C# |
| `go.mod` | Go |
| Nenhum dos acima | Desconhecida |

Se `pom.xml` existir, extraia `<artifactId>` e a versão do Spring Boot (se houver).  
Se `package.json` existir, extraia `"name"` e `"version"`.

### 1.2 — SDD Kit instalado

Verifique se `.github/copilot-instructions.md` E `.github/AGENTS.md` existem no repositório.  
Se ambos existirem → **✅ instalado**. Caso contrário → **❌ não instalado**.

### 1.3 — Remote origin

```bash
git -C "<dir>" remote get-url origin 2>/dev/null || echo "sem remote"
```

---

## Etapa 2 — Gerar / Atualizar WORKSPACE.md

Gere ou sobrescreva o arquivo `WORKSPACE.md` na raiz `WORKSPACE_ROOT` com o seguinte formato:

```markdown
# Workspace Catalog

> Atualizado em: YYYY-MM-DD

## Repositórios

| Projeto | Tech Stack | SDD Kit | Remote |
|---------|-----------|---------|--------|
| gcb-hr-hub-example | Java / Spring Boot | ✅ instalado | https://github.com/casas-bahia/gcb-hr-hub-example |
| gcb-hr-hub-other   | Node.js / TypeScript | ❌ não instalado | https://github.com/casas-bahia/gcb-hr-hub-other |

## Estatísticas

- **Total de repositórios:** N
- **Com SDD Kit:** X
- **Sem SDD Kit:** Y
- **Sem remote configurado:** Z
```

Regras:
- Ordene a tabela alfabeticamente pelo nome do projeto.
- Se o remote for `sem remote`, exiba `—` na coluna Remote.
- Preserve a estrutura do arquivo a cada execução — nunca concatene, sempre sobrescreva.
- Use a data atual no campo `Atualizado em`.

Após gerar o arquivo, exiba o conteúdo completo ao usuário e informe quantos repositórios foram encontrados.

---

## Etapa 3 — Clonar novos repositórios (opcional)

Após apresentar o catálogo, pergunte ao usuário:

> Deseja clonar novos repositórios no workspace?
> Se sim, informe a lista de repositórios (um por linha ou separados por vírgula).
> Use o formato `nome-do-repo` ou `org/nome-do-repo`. Exemplos:
>
> ```
> gcb-hr-hub-example
> casas-bahia/gcb-hr-hub-other
> ```
>
> Deixe em branco para encerrar.

Se o usuário **não informar nenhum repositório**, encerre o agente com a mensagem: `WORKSPACE.md atualizado com sucesso.`

Se o usuário **informar repositórios**, execute as sub-etapas abaixo.

### 3.1 — Normalizar nomes

Para cada item da lista:
- Se estiver no formato `org/repo`, use como está.
- Se estiver apenas como `nome-do-repo`, prefixe com `casas-bahia/` → `casas-bahia/nome-do-repo`.

### 3.2 — Verificar se já existe localmente

Para cada repositório normalizado, verifique se o diretório `<nome-do-repo>/` já existe na raiz do workspace. Se existir, ignore e registre como "já presente".

### 3.3 — Clonar

Para cada repositório que **não existe localmente**, execute:

```bash
cd <WORKSPACE_ROOT>
git clone https://github.com/<org>/<repo>.git
```

Trate os seguintes casos:
- **Sucesso**: registre como "clonado com sucesso".
- **Erro de autenticação / repo não encontrado**: registre como "falha — sem acesso ou repositório não existe" e continue para o próximo.
- **Diretório já existe mas não é git**: registre como "conflito — diretório existente não é um repositório git".

### 3.4 — Relatório de clonagem

Após tentar clonar todos os repositórios solicitados, exiba um resumo:

```markdown
## Resultado da Clonagem

| Repositório | Status |
|-------------|--------|
| gcb-hr-hub-example | ✅ clonado com sucesso |
| gcb-hr-hub-other   | ⚠️ já presente no workspace |
| gcb-hr-hub-missing | ❌ falha — sem acesso ou não encontrado |
```

### 3.5 — Re-escanear e atualizar WORKSPACE.md

Após a clonagem, volte à **Etapa 1** e repita o scan completo para incluir os novos repositórios no catálogo. Sobrescreva `WORKSPACE.md` com o estado atualizado.

---

## Etapa 4 — Painel de Demandas em Progresso (SDD)

Para cada repositório com SDD Kit instalado, varra os session-states em **dois locais** (v2.5 e legado):

```
# v3.1+ — sdd_workspace externo (preferencial, quando definido no sdd.config.md)
{sdd_workspace}/<projeto>/specs/*/session-state.md

# v2.5 fallback — workspace no kit (sem sdd_workspace)
{sdd_kit_root}/workspace/<projeto>/specs/*/session-state.md

# legado (pré-v2.5) — dentro do projeto
<projeto>/.github/docs/specs/*/session-state.md
```

> Para descobrir os caminhos: leia `<projeto>/.github/sdd.config.md`; resolva `sdd_workspace:` (preferencial) ou `sdd_kit:` (fallback). Se o arquivo não existir, use somente o caminho legado.

Para cada `session-state.md` encontrado, extraia os campos:
- `ticket`
- `status`
- `last_agent`
- `last_runtime`
- `last_run`
- `next_agent`
- `blocked_on`

Adicione ao `WORKSPACE.md` a seção:

```markdown
## Demandas em Progresso (SDD)

> Atualizado em: YYYY-MM-DD

| Projeto | Ticket | Status | Último Agente | Último Runtime | Próximo Agente | Bloqueio |
|---------|--------|--------|--------------|----------------|----------------|---------|
| gcb-hr-hub-example | JT-1234 | implementing | sdd-implement-spec | github-copilot | sdd-review-code | — |
| gcb-hr-hub-other | JT-5678 | reviewed | sdd-review-code | claude-code | sdd-update-documentation | — |

### Demandas Concluídas (últimas 5)

| Projeto | Ticket | Concluído em |
|---------|--------|-------------|
| gcb-hr-hub-example | JT-1100 | 2026-06-15 |
```

Regras:
- Ordene por `last_run` decrescente (mais recente primeiro).
- Demandas com `status = done` vão para a seção "Concluídas" — exiba apenas as 5 mais recentes.
- Se nenhum `session-state.md` for encontrado em nenhum projeto, omita a seção.
- Se `blocked_on` for diferente de `—`, destaque a linha com `⚠️` no início do campo Bloqueio.

---

## Etapa 5 — Métricas de Sprint (somente sob comando explícito)

> **Esta etapa só é executada quando o usuário invoca explicitamente:**
> ```
> /metricas-sprint <PROJETO> <SPRINT_ID>
> ```
> Exemplo: `/metricas-sprint gcb-hr-jt-work-journey-back sprint-42`
>
> Não execute automaticamente durante a sincronização padrão.

### 5.1 — Coletar dados do sprint

Para o projeto e sprint informados, colete via Jira (se disponível) ou a partir dos `session-state.md` do workspace:

- **Tickets concluídos** no sprint (status = `done`)
- **Tickets em progresso** no sprint (status diferente de `done` e `blocked`)
- **Tickets bloqueados** (campo `blocked_on` diferente de `—`)
- **Story points** por ticket (se registrado no `task.md`)
- **Datas de início e fim** de cada ticket (`last_run` do primeiro agente ao `last_run` do `sdd-update-documentation`)

### 5.2 — Calcular métricas

| Métrica | Cálculo | Referência saudável |
|---------|---------|-------------------|
| **Velocity** | Story points entregues no sprint | Comparar com 3 sprints anteriores |
| **Throughput** | Número de tickets concluídos no sprint | Comparar com 3 sprints anteriores |
| **Cycle Time** | Média de dias entre início da implementação e conclusão | ≤ 3 dias para tickets simples |
| **WIP (Work in Progress)** | Tickets em progresso simultaneamente | ≤ capacidade do time |
| **Bug Rate** | Tickets do tipo Bug / total de tickets no sprint | < 20% |
| **Bloqueios ativos** | Contagem de tickets com `blocked_on ≠ —` | 0 (idealmente) |

**Alertas automáticos:**

| Condição | Alerta |
|----------|--------|
| Velocity caiu > 30% vs. sprint anterior | ⚠️ Queda de velocity — investigar impedimentos |
| Bug Rate > 30% | ⚠️ Alta taxa de bugs — revisar qualidade antes de acelerar |
| WIP > capacidade declarada do time | ⚠️ WIP excessivo — limitar entradas novas |
| Cycle Time > 5 dias para tickets simples | ⚠️ Tickets travados — verificar bloqueios |
| 2+ tickets com `blocked_on ≠ —` | ⚠️ Impedimentos ativos — escalar para PO/liderança |

### 5.3 — Saúde do time (Health Check)

| Dimensão | Indicadores observáveis | Status |
|----------|------------------------|--------|
| **Entrega** | Velocity estável ou crescente, Throughput consistente | ✅ / ⚠️ / ❌ |
| **Qualidade** | Bug Rate baixo, reviews sem achados Crítico | ✅ / ⚠️ / ❌ |
| **Colaboração** | Tickets sem bloqueio prolongado, handoffs rápidos entre agentes | ✅ / ⚠️ / ❌ |
| **Clareza** | Tasks com `task.md` preenchido antes da implementação | ✅ / ⚠️ / ❌ |

### 5.4 — Sugestão de capacidade para o próximo sprint

Com base no Throughput e Velocity dos últimos 3 sprints:

```
Throughput médio: <N> tickets/sprint
Velocity média: <N> pontos/sprint
Sugestão: comprometer <N ± 10%> pontos ou <N ± 1> tickets no próximo sprint
```

### 5.5 — Adicionar seção ao WORKSPACE.md

Adicione (ou substitua) a seção `## Últimas Métricas de Sprint` no `WORKSPACE.md`.

---

## Etapa 6 — Gerar PIPELINE-STATUS.md (dashboard de qualidade de gates)

> **Executada automaticamente ao final de toda sincronização padrão**, após a Etapa 4.

### 6.1 — Coletar dados de gates de todos os projetos

Para cada repositório com SDD Kit instalado, varre em todos os locais (v3.1+, v2.5 e legado — ver Etapa 4):
```
{sdd_workspace}/<projeto>/specs/*/session-state.md           # v3.1+ (sdd_workspace no sdd.config.md)
{sdd_kit_root}/workspace/<projeto>/specs/*/session-state.md  # v2.5 fallback
<projeto>/.github/docs/specs/*/session-state.md              # legado
```

Para cada `session-state.md`, extraia a tabela **Quality Gates** completa:
- `ticket`, `project`
- Por gate (G1–G6): `policy`, `status` (passed/failed/skipped/pending)
- `Agent History`: timestamps de início e fim por etapa (para calcular duração)
- `blocked_on`, `retries`, `awaiting_checkpoint`

### 6.2 — Calcular métricas agregadas

| Métrica | Cálculo |
|---------|---------|
| **Pass rate por gate** | (gates com status=passed) / (gates avaliados, excluindo skipped) × 100% |
| **Failure rate por gate** | (gates que falharam ao menos 1x) / total × 100% |
| **Demandas bloqueadas** | `blocked_on ≠ —` em qualquer demand |
| **Demandas em checkpoint** | `awaiting_checkpoint ≠ —` por mais de 2h (se timestamp disponível) |
| **Retries acumulados** | soma de `retries` de todas as demandas em progresso |

### 6.3 — Gerar PIPELINE-STATUS.md

Gere ou sobrescreva `.github/PIPELINE-STATUS.md` na raiz do workspace SDD Kit com:

```markdown
# Pipeline Status — Dashboard de Gates

> Atualizado em: YYYY-MM-DD HH:MM

## Resumo Executivo

| Métrica | Valor |
|---------|-------|
| Demandas ativas | N |
| Demandas concluídas (últimos 30 dias) | N |
| Demandas bloqueadas | N ⚠️ |
| Em checkpoint aguardando humano | N |
| Retries acumulados (em progresso) | N |

## Taxa de Passagem por Gate

| Gate | Descrição | Avaliados | Passed | Failed | Pass Rate |
|------|-----------|-----------|--------|--------|-----------|
| G1 | spec-complete | N | N | N | N% |
| G2 | plan-approved | N | N | N | N% |
| G3 | build-green | N | N | N | N% |
| G4 | tests-present | N | N | N | N% |
| G5 | review-clean | N | N | N | N% |
| G6 | pr-approved | N | N | N | N% |

> Gates com failure rate > 30% indicam gargalos recorrentes.

## Demandas Bloqueadas

| Projeto | Ticket | Bloqueio | Desde |
|---------|--------|----------|-------|
| gcb-example | JT-123 | ⚠️ build-failed G3 — JAVA_HOME errado | 2026-06-21 |

## Histórico de Gates por Demanda

| Projeto | Ticket | G1 | G2 | G3 | G4 | G5 | G6 | Status |
|---------|--------|----|----|----|----|----|----|--------|
| gcb-example | JT-789 | ✓ | ✓ | ✓ | ⊘ | ⊘ | ✓ | done |
| gcb-other | JT-101 | ✓ | ✓ | ✗ | — | — | — | in-progress |

Legenda: `✓` passed · `✗` failed · `⊘` skipped · `⸺` pending
```

Regras:
- Ordene demandas bloqueadas por data (mais antigas primeiro — maior urgência).
- Se não houver demandas bloqueadas ou em checkpoint, exiba `—` na seção correspondente.
- Sempre sobrescreva — nunca concatene.
- Se nenhum `session-state.md` for encontrado no workspace, exiba apenas o Resumo Executivo com valores zero.

---

## Regras gerais

- Nunca modifique código de produção nem arquivos de testes.
- Não clone repositórios sem confirmação explícita do usuário.
- Se `WORKSPACE.md` já existir, **sempre sobrescreva** — não concatene.
- Ao clonar, use sempre HTTPS (`https://github.com/...`), nunca SSH, para compatibilidade com ambientes corporativos.
- Não assuma a organização padrão em nenhum outro contexto além de `casas-bahia/` — se o usuário informar uma org diferente, use a informada.
<!-- @end -->
