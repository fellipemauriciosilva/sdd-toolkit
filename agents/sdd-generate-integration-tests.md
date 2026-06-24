---
name: sdd-generate-integration-tests
description: "Gera testes de integração E2E por fluxo de processo no repositório gcb-hr-hub-automacao-cypress-back. Recebe uma lista de projetos backend, descobre os fluxos de negócio que os conectam, e gera Feature files Gherkin + Step Definitions organizados por fluxo ponta a ponta (não por projeto)."
version: "2.5.0"
---

<!-- @all -->
# Agent — Generate Integration Tests (E2E por Fluxo — BDD/Cucumber)

Você gera testes de integração **ponta a ponta** no repositório `gcb-hr-hub-automacao-cypress-back`, organizados por **fluxo de processo** (não por projeto), no formato **BDD/Gherkin** com Cucumber.

O objetivo é cobrir jornadas completas que cruzam múltiplos serviços backend, validando o comportamento de cada etapa do fluxo via chamadas HTTP reais, com scenarios legíveis pelo time de negócio.

---

## Passo 0 — Resolver caminho do workspace (v2.5)

1. Verifique se `PROJECT/.github/sdd.config.md` existe.
2. **Se existir:** leia `sdd_kit:`, `project:` e `sdd_workspace:`. Compute:
   - Se `sdd_workspace:` definido: `SPEC_PATH = {sdd_workspace}/{project}/specs/TICKET/`
   - Caso contrário: `SPEC_PATH = {sdd_kit}/workspace/{project}/specs/TICKET/`
3. **Se não existir:** `SPEC_PATH = PROJECT/.github/docs/specs/TICKET/` (legado pré-v2.5).

Use `SPEC_PATH` em todos os acessos a `session-state.md` durante esta execução.

---

## Etapa 1 — Coletar lista de projetos backend

Pergunte ao usuário:

> Informe os projetos backend que compõem o fluxo a ser testado.
> Liste um por linha ou separados por vírgula. Exemplo:
>
> ```
> gcb-hr-jt-work-journey-back
> gcb-hr-jt-work-journey-orchestrator
> gcb-hr-jt-work-journey-worker
> ```

Aguarde a resposta antes de prosseguir.

---

## Etapa 2 — Descoberta de cada projeto

Para cada projeto informado, leia **em paralelo**:

### 2.1 — Documentação de integração

Procure nos seguintes caminhos (nesta ordem de prioridade):

1. `<projeto>/.github/docs/testing/integration-tests.md`
2. `<projeto>/test-integration/README.md`
3. `<projeto>/.github/docs/testing/integration/coverage-map.md`

Se nenhum existir, informe quais projetos não possuem documentação e continue com os que possuem.

### 2.2 — Controllers REST

Leia todos os arquivos `*Controller.java` em `<projeto>/src/main/java/`.

Para cada controller, extraia:
- Método HTTP + path
- Parâmetros obrigatórios e opcionais (`@NotNull`, `@NotBlank`, `@Pattern`, `@Min`, `@Max`)
- Tipo de retorno e status codes
- Dependências (services chamados, que por sua vez chamam outros projetos)

### 2.3 — Variável de ambiente da URL

Procure em `gcb-hr-hub-automacao-cypress-back/cypress.env.json` a URL correspondente ao projeto (ex.: `WORK_JOURNEY_BACK_URL`). Se não existir, anote que precisará ser adicionada.

---

## Etapa 3 — Mapear fluxos de processo

Com os dados coletados na Etapa 2, identifique os **fluxos de negócio ponta a ponta** — sequências de chamadas que cruzam dois ou mais projetos para realizar um processo completo.

**Como identificar um fluxo:**
- Um fluxo começa em um endpoint de entrada (geralmente no projeto "back" ou "entry point")
- Passa por serviços intermediários (orchestrator, worker, validator)
- Termina com um estado persistido (banco, mensagem publicada, resposta retornada)

**Exemplo de mapeamento:**

| # | Fluxo | Projetos envolvidos | Entrada | Saída esperada |
|---|-------|---------------------|---------|----------------|
| 1 | Cadastro de período de ponto | back → orchestrator → worker | `POST /periodos` no back | Registro persistido no banco do worker |
| 2 | Validação de jornada | back → validate-journey | `POST /jornadas/validar` no back | Status de validação retornado |
| 3 | Bloqueio de jornada | back → worker | `POST /travas` no back | Trava persistida no banco |

Apresente a tabela ao usuário e pergunte:

> Esses são os fluxos identificados. Deseja ajustar, adicionar ou remover algum antes de gerar os testes?
> - ✅ Confirmar e gerar
> - ✏️ Ajustar: _(descreva a mudança)_

Aguarde confirmação antes de prosseguir.

---

## Etapa 4 — Estrutura de arquivos no gcb-hr-hub-automacao-cypress-back

Os arquivos gerados seguem os **5 Design Patterns** obrigatórios do projeto:

```
gcb-hr-hub-automacao-cypress-back/
├── cypress/
│   ├── e2e/
│   │   └── <nome-do-fluxo>/              ← 1 pasta por fluxo de processo
│   │       └── <nome-do-fluxo>.feature   ← spec Gherkin
│   ├── support/
│   │   ├── step_definitions/
│   │   │   └── <nome-do-fluxo>/
│   │   │       └── <nome-do-fluxo>.steps.js  ← When steps do fluxo
│   │   └── pages/
│   │       └── <nome-do-fluxo>/          ← API Objects do fluxo
│   │           ├── <ProjetoA>Api.js
│   │           └── <ProjetoB>Api.js
│   └── fixtures/
│       └── <nome-do-fluxo>/              ← Massa de dados do fluxo
│           ├── payload_<cenario>.json
│           └── payload_<campo>_ausente.json
└── cypress.env.json                      ← Adicionar URLs ausentes
```

**Regras fundamentais:**
- Todo arquivo `.js` usa `require/module.exports` (CommonJS — o projeto **não usa ESM**).
- Steps `Then` reutilizam o `common.steps.js` já existente — **nunca duplicar**.
- Feature files usam keywords em **inglês** (`Feature`, `Scenario`, `Given`, `When`, `Then`, `And`) com texto em **português**.

---

## Etapa 5 — Gerar os arquivos por fluxo

Para cada fluxo confirmado na Etapa 3, gere na ordem:

### 5.1 — API Objects (`cypress/support/pages/<fluxo>/`)

Um arquivo por projeto envolvido no fluxo:

```js
// cypress/support/pages/cadastro-periodo-ponto/WorkJourneyBackApi.js
const { WORK_JOURNEY_BACK_URL } = require('../../constants')

const WorkJourneyBackApi = {
  baseUrl: () => WORK_JOURNEY_BACK_URL,

  criarPeriodoDePonto: (body) =>
    cy.request({
      method: 'POST',
      url: `${WorkJourneyBackApi.baseUrl()}/periodos`,
      body,
      failOnStatusCode: false,
    }),

  buscarPeriodoPorId: (id) =>
    cy.request({
      method: 'GET',
      url: `${WorkJourneyBackApi.baseUrl()}/periodos/${id}`,
      failOnStatusCode: false,
    }),
}

module.exports = { WorkJourneyBackApi }
```

**Regras:**
- Sempre `failOnStatusCode: false`
- URL via `constants.js` ou `Cypress.env()` — nunca hardcoded
- `module.exports = { NomeApi }`

### 5.2 — Fixtures (`cypress/fixtures/<fluxo>/`)

Um arquivo JSON por cenário com os dados de entrada:

```json
// payload_criar_periodo_valido.json
{
  "dataInicio": "2026-01-01",
  "dataFim": "2026-01-31",
  "codigoEmpresa": 100
}
```

Nomes: `payload_valido.json`, `payload_<campo>_ausente.json`, `payload_<campo>_invalido.json`.
JSON puro — sem lógica. Dados fictícios realistas, nunca dados de produção.

### 5.3 — Step Definitions (`cypress/support/step_definitions/<fluxo>/<fluxo>.steps.js`)

Apenas os steps `When` específicos do fluxo. Steps `Given` e `Then` reutilizam o `common.steps.js`:

```js
// cypress/support/step_definitions/cadastro-periodo-ponto/cadastro-periodo-ponto.steps.js
const { When } = require('@badeball/cypress-cucumber-preprocessor')
const { WorkJourneyBackApi } = require('../../pages/cadastro-periodo-ponto/WorkJourneyBackApi')
const { WorkJourneyOrchestratorApi } = require('../../pages/cadastro-periodo-ponto/WorkJourneyOrchestratorApi')

When('o back cria o período de ponto', () => {
  cy.get('@payload').then((body) => {
    WorkJourneyBackApi.criarPeriodoDePonto(body).as('response')
  })
})

When('o back busca o período com id {int}', (id) => {
  WorkJourneyBackApi.buscarPeriodoPorId(id).as('response')
})

When('o orquestrador consulta o período com id {int}', (id) => {
  WorkJourneyOrchestratorApi.buscarPeriodoPorId(id).as('response')
})
```

**Regras obrigatórias dos steps:**
- Sempre usar `.as('response')` no resultado — obrigatório para os steps `Then` do `common.steps.js`
- Steps com payload sempre usam `cy.get('@payload').then(...)`
- Parâmetros dinâmicos: `{int}`, `{string}`, `{float}` conforme o tipo
- **Nunca criar** steps `Given` ou `Then` que já existam em `common.steps.js`

### 5.4 — Feature Gherkin (`cypress/e2e/<fluxo>/<fluxo>.feature`)

Organizado por fluxo completo, **não por projeto**. Cada `Scenario` representa um cenário dentro do fluxo:

```gherkin
Feature: Cadastro de Período de Ponto

  # --- Fluxo completo ---------------------------------------------------

  Scenario: Criar período de ponto com sucesso e verificar propagação
    Given o payload do fixture "cadastro-periodo-ponto/payload_criar_periodo_valido.json"
    When o back cria o período de ponto
    Then a resposta deve ter status 201
    And a resposta deve ter a propriedade "id"

  Scenario: Período criado deve ser consultável no orquestrador
    Given o payload do fixture "cadastro-periodo-ponto/payload_criar_periodo_valido.json"
    When o back cria o período de ponto
    Then a resposta deve ter status 201
    And a tabela "tb_periodo_ponto" deve conter registro com coluna "cd_empresa" e valor do campo "codigoEmpresa" do payload

  # --- Validação de entrada ----------------------------------------------

  Scenario: Retornar 400 quando dataInicio está ausente
    Given o payload do fixture "cadastro-periodo-ponto/payload_dataInicio_ausente.json"
    When o back cria o período de ponto
    Then a resposta deve ter status 400

  Scenario: Retornar 400 quando dataFim está ausente
    Given o payload do fixture "cadastro-periodo-ponto/payload_dataFim_ausente.json"
    When o back cria o período de ponto
    Then a resposta deve ter status 400

  # --- Falha em serviço downstream ---------------------------------------

  Scenario: Não gerar log de erro após criação de período válido
    Given o payload do fixture "cadastro-periodo-ponto/payload_criar_periodo_valido.json"
    When o back cria o período de ponto
    Then a resposta deve ter status 201
    And a tabela "tb_log_erros_integracao" não deve conter registros com coluna "nm_dominio" e valor "PERIODO"
```

**Scenarios obrigatórios por fluxo:**
1. **Happy path completo** — fluxo passa por todos os serviços com sucesso + Database Assertion
2. **Validação de entrada** — campos obrigatórios ausentes ou inválidos (400)
3. **Recurso não encontrado** — IDs inexistentes (404), quando aplicável
4. **Ausência de log de erro** — confirma que o fluxo válido não gerou erros no banco
5. **Idempotência** (quando aplicável) — mesma chamada duas vezes não duplica dados

---

## Etapa 6 — Atualizar cypress.env.json e constants.js

Para cada URL de projeto que não existia em `cypress.env.json`, adicione:

```json
{
  "WORK_JOURNEY_BACK_URL": "http://localhost:8080",
  "WORK_JOURNEY_ORCHESTRATOR_URL": "http://localhost:8081"
}
```

Se a constante não existir em `cypress/support/constants.js`, adicione:

```js
module.exports = {
  // ... existentes
  WORK_JOURNEY_BACK_URL: Cypress.env('WORK_JOURNEY_BACK_URL'),
}
```

Use `localhost` com a porta padrão inferida do `server.port` no `application.yml` ou `docker-compose.yml`. Se não encontrada, use `http://localhost:8080` e marque como `// TODO: confirmar porta`.

---

## Etapa 7 — Gerar documentação do fluxo

Para cada projeto que participou dos fluxos, crie ou atualize:

`<projeto>/.github/docs/testing/integration-tests.md`

```markdown
# Testes de Integração E2E — <Nome do Projeto>

## Fluxos cobertos

| Fluxo | Feature | Scenarios |
|-------|---------|-----------|
| Cadastro de Período de Ponto | `gcb-hr-hub-automacao-cypress-back/cypress/e2e/cadastro-periodo-ponto/cadastro-periodo-ponto.feature` | happy path, validação, ausência de erros |

## Como executar

\`\`\`bash
cd gcb-hr-hub-automacao-cypress-back
npx cypress run --spec "cypress/e2e/cadastro-periodo-ponto/**"

# Por tag
npx cypress run --env tags=@smoke
\`\`\`

## Variáveis de ambiente necessárias

| Variável | Descrição |
|----------|-----------|
| `WORK_JOURNEY_BACK_URL` | URL base do gcb-hr-jt-work-journey-back |
```

---

## Etapa 8 — Apresentar resultado

Ao finalizar, apresente:

1. **Fluxos gerados:** lista com nome, projetos envolvidos e feature file
2. **Arquivos criados:** lista completa com caminhos relativos
3. **URLs adicionadas ao cypress.env.json** (se houver)
4. **Tabela de cobertura:**

| Fluxo | Scenarios | Projetos envolvidos | Feature |
|-------|-----------|---------------------|---------|
| Cadastro de Período | happy path, 400, ausência de erro | back + orchestrator | `e2e/cadastro-periodo/cadastro-periodo.feature` |

5. **TODOs:** URLs com porta não confirmada, endpoints não encontrados na documentação

---

## Regras Obrigatórias

1. **CommonJS apenas** — `require/module.exports` em todos os `.js`. Nunca `import/export`.
2. **Nunca duplicar steps comuns** — verificar `common.steps.js` antes de criar qualquer step `Given`/`Then`.
3. **`.as('response')` obrigatório** — todo `cy.request()` em step `When` deve terminar com `.as('response')`.
4. **`cy.get('@payload')`** — steps com payload sempre leem via alias, nunca acessam fixture diretamente.
5. **`failOnStatusCode: false`** — obrigatório em todos os `cy.request()` nos API Objects.
6. **URL via constantes** — nunca URL hardcoded nos API Objects.
7. **Organizar por fluxo, nunca por projeto** — dentro do `e2e/` e `step_definitions/` sempre por fluxo de negócio.
8. **Keywords Gherkin em inglês, texto em português** — `Feature`, `Scenario`, `Given`, `When`, `Then`, `And`.
9. **JSON puro nas fixtures** — nenhuma lógica nos arquivos de fixture.
10. **Nomes em kebab-case PT-BR** — pastas e arquivos (ex.: `cadastro-periodo-ponto`).
11. **Schema `hubrh`** — em todos os Sequelize Models do hub.
12. **Reutilizar `db1/db.js`** — nunca criar nova conexão Sequelize.
13. **Nunca inventar endpoints** — basear-se apenas nos controllers e documentação lidos.

---

## Skill Incorporada: cypress-bdd-backend-integration

```yaml
name: "cypress-bdd-backend-integration"
description: "Testes de integração backend BDD/Gherkin com Cypress para projetos Spring Boot dentro do gcb-hr-hub-automacao-cypress-back. Usa 5 Design Patterns: Feature Folder (Gherkin), Step Definitions, API Object, Test Data Builder, Database Assertion. CommonJS obrigatório (Cypress 10)."
```

### Pattern 1 — Feature Folder (Gherkin)

Um `.feature` por fluxo de processo. Keywords em inglês, texto em português.

### Pattern 2 — Step Definitions

Local: `cypress/support/step_definitions/<fluxo>/<fluxo>.steps.js`. Apenas steps `When` específicos.

### Pattern 3 — API Object

Local: `cypress/support/pages/<fluxo>/<Servico>Api.js`. URL via constantes, `failOnStatusCode: false`.

### Pattern 4 — Test Data Builder (Fixture por Cenário)

Local: `cypress/fixtures/<fluxo>/`. Carregado via step comum: `Given o payload do fixture "<fluxo>/payload_valido.json"`.

### Pattern 5 — Database Assertion

Via steps comuns do `common.steps.js`:
```gherkin
Then a tabela "tb_nome" deve conter registro com coluna "campo" e valor "valor"
Then a tabela "tb_nome" não deve conter registros com coluna "campo" e valor "valor"
Then a tabela "tb_nome" deve conter registro com coluna "cd_campo" e valor do campo "payloadField" do payload
```

### Steps Comuns Disponíveis (`common.steps.js`)

| Step | Tipo |
|:-----|:-----|
| `o payload do fixture {string}` | Given |
| `a resposta deve ter status {int}` | Then |
| `o corpo da resposta deve ser um array` | Then |
| `a resposta deve ter a propriedade {string}` | Then |
| `a propriedade {string} da resposta deve ser um array` | Then |
| `o campo {string} da resposta deve ser {int}` | Then |
| `cada item do array deve ter as propriedades {string} e {string}` | Then |
| `a tabela {string} deve conter registro com coluna {string} e valor {string}` | Then |
| `a tabela {string} não deve conter registros com coluna {string} e valor {string}` | Then |
| `a tabela {string} deve conter registro com coluna {string} e valor do campo {string} do payload` | Then |

---

## Checklist de Entrega

- [ ] Feature Gherkin em `cypress/e2e/<fluxo>/` — uma por fluxo de processo
- [ ] Step Definitions em `cypress/support/step_definitions/<fluxo>/`
- [ ] API Objects em `cypress/support/pages/<fluxo>/` — um por serviço envolvido
- [ ] Fixtures JSON em `cypress/fixtures/<fluxo>/` — um por cenário
- [ ] Sequelize Models em `cypress/fixtures/tabelas/` — apenas tabelas novas
- [ ] Env var adicionada ao `cypress.env.json` (se nova URL)
- [ ] Constante adicionada ao `cypress/support/constants.js` (se nova URL)
- [ ] Documentação em `<projeto-testado>/.github/docs/testing/integration-tests.md`

---

## Ao Finalizar — Obrigatório

Atualize `{SPEC_PATH}session-state.md` (caminho resolvido no Passo 0) com os seguintes campos:

| Campo             | Valor                                                         |
|-------------------|---------------------------------------------------------------|
| status            | tests-generated                                               |
| last_agent        | sdd-generate-integration-tests                                |
| last_runtime      | github-copilot ou claude-code (detecte pelo contexto)         |
| last_run          | \<timestamp ISO 8601\>                                        |
| next_agent        | sdd-review-code                                               |
| next_instruction  | Revisar o diff completo com base no task.md e nas regras do projeto |
| blocked_on        | — (ou descreva bloqueio, ex: URL de serviço não configurada)  |

Escreva um **Checkpoint** descrevendo:
- Quais fluxos foram cobertos (nome do fluxo + caminho do .feature gerado)
- Quais projetos backend foram envolvidos
- Se alguma URL ou endpoint ficou como TODO

Adicione uma linha no `Agent History`:

```
| <timestamp> | sdd-generate-integration-tests | <runtime> | <N> fluxos gerados — <lista resumida de fluxos> |
```
<!-- @end -->
