---
name: "cypress-backend-integration"
description: "Testes de integração backend com Cypress para projetos Spring Boot dentro do gcb-hr-hub-automacao-cypress-back. Usa 4 Design Patterns: Feature Folder, API Object, Test Data Builder, Database Assertion. CommonJS obrigatório (Cypress 10). USE quando: gerar testes de integração para serviços REST Spring Boot que persistem em SQL Server."
---

# Skill — Cypress Backend Integration (Padrão Hub QA)

## Visão Geral

Esta skill define como implementar testes de integração de serviços **Spring Boot REST** dentro do repositório `gcb-hr-hub-automacao-cypress-back`, usando a infraestrutura já existente (SQL Server via Sequelize, tasks customizadas, dotenv).

> **Stack fixa:** Cypress 10.9.0 · CommonJS · Node 16+ · SQL Server via Sequelize + tedious · `faker-br` para massa

---

## Regra Fundamental — CommonJS OBRIGATÓRIO

O projeto `gcb-hr-hub-automacao-cypress-back` usa `"type": "commonjs"` implícito. Todo arquivo `.js` deve usar `require/module.exports`.

```js
// ✅ CORRETO
const faker = require('faker-br')
require('dotenv').config()
module.exports = MinhaClasse

// ❌ PROIBIDO — este projeto NÃO usa ESM
import faker from 'faker-br'
export default MinhaClasse
```

**Exceção:** specs `.cy.js` podem usar `require()` no topo, mas o Cypress também aceita `import` apenas dentro dos blocos de teste — prefira `require` para consistência.

---

## 4 Design Patterns Obrigatórios

### Pattern 1 — Feature Folder

Cada domínio de negócio do serviço testado tem sua própria spec. Uma spec por controller REST.

**Estrutura:**
```
cypress/e2e/<projeto-slug>/
  <dominio-1>.cy.js
  <dominio-2>.cy.js
  ...
```

**Convenção de `<projeto-slug>`:**
- Remover prefixo `gcb-hr-jt-` ou `gcb-hr-hub-`
- Exemplo: `gcb-hr-jt-work-journey-orchestrator` → `work-journey-orchestrator`

**Estrutura interna de cada spec:**
```js
context('<NomeServico> — <NomeDominio>', () => {
  describe('<MÉTODO> /<rota>', () => {
    it('[<MÉTODO> /<rota>] - <comportamento esperado>', () => { ... })
    it('[<MÉTODO> /<rota>] - <cenário negativo>', () => { ... })
  })
})
```

**Regras:**
- Um `context()` por arquivo — identifica o serviço e domínio
- Um `describe()` por endpoint (método + rota)
- Um `it()` por cenário (happy path + negativos)
- Nome do `it()` no formato: `[MÉTODO /rota] - descrição do comportamento`

---

### Pattern 2 — API Object

Encapsula todas as chamadas `cy.request()` de um domínio em um único objeto. Isola URL, método HTTP e headers da spec.

**Local:** `cypress/support/pages/<projeto-slug>/<Dominio>Api.js`

**Template:**
```js
// cypress/support/pages/work-journey-orchestrator/ProrrogacaoApi.js
require('dotenv').config()

const ProrrogacaoApi = {
  baseUrl: () => Cypress.env('WORK_JOURNEY_ORCHESTRATOR_URL'),

  processar: (body) =>
    cy.request({
      method: 'POST',
      url: `${ProrrogacaoApi.baseUrl()}/prorrogacao`,
      body,
      failOnStatusCode: false,
    }),
}

module.exports = { ProrrogacaoApi }
```

**Para endpoints sem body (disparo simples):**
```js
const EscalasApi = {
  baseUrl: () => Cypress.env('WORK_JOURNEY_ORCHESTRATOR_URL'),

  processarTodas: () =>
    cy.request({ method: 'POST', url: `${EscalasApi.baseUrl()}/escalas`, failOnStatusCode: false }),

  processarPorEmpresaMatricula: (empresa, matricula) =>
    cy.request({
      method: 'POST',
      url: `${EscalasApi.baseUrl()}/escalas/empresa/${empresa}/matricula/${matricula}`,
      failOnStatusCode: false,
    }),
}

module.exports = { EscalasApi }
```

**Regras:**
- Um arquivo por controller REST do serviço
- Sempre `failOnStatusCode: false` — a spec é responsável por verificar o status
- URL base via `Cypress.env('<PROJETO_SLUG_UPPER>_URL')` — nunca hardcoded
- `<PROJETO_SLUG_UPPER>` = slug com `-` → `_` e uppercase (ex: `WORK_JOURNEY_ORCHESTRATOR_URL`)
- Exportar como `module.exports = { NomeApi }`

---

### Pattern 3 — Test Data Builder (Fixture por Cenário)

Cada cenário tem seu próprio arquivo JSON de fixture. O nome do arquivo descreve o comportamento testado.

**Local:** `cypress/fixtures/<projeto-slug>/<dominio>/`

**Estrutura de exemplo:**
```
cypress/fixtures/work-journey-orchestrator/
  prorrogacao/
    payload_valido.json
    payload_gatilho_invalido.json
    payload_tipo_prorrogacao_invalido.json
    payload_empresa_ausente.json
    payload_matricula_ausente.json
    payload_competencia_formato_invalido.json
    payload_tempo_negativo.json
  ponto/
    payload_valido.json
    payload_empresa_ausente.json
    payload_data_marcacao_ausente.json
    payload_hora_marcacao_ausente.json
    payload_tipo_marcacao_ausente.json
  escalas/
    (sem fixtures — endpoints sem body)
  travas/
    (sem fixtures — endpoints sem body ou com path param)
```

**Carregamento na spec:**
```js
cy.fixture('work-journey-orchestrator/prorrogacao/payload_valido.json').then((body) => {
  ProrrogacaoApi.processar(body).then((res) => {
    expect(res.status).to.eq(200)
  })
})
```

**Regras:**
- JSON puro — nenhuma lógica nos arquivos de fixture
- Nomes em `snake_case` descritivos do cenário
- Dados fictícios realistas — nunca dados de produção
- Não reutilizar o mesmo fixture para cenários diferentes

---

### Pattern 4 — Database Assertion

Após acionar o endpoint, verificar o estado persistido no SQL Server para confirmar que a integração funcionou end-to-end.

**Tasks disponíveis no `cypress.config.js` (já existentes):**
```js
// SELECT: cy.task('sql.selectDB', [campoWhere, valorWhere, nomeTabela])
// INSERT: cy.task('sql.insertDB', [name, location, nomeTabela])
// UPDATE: cy.task('sql.updateDB', [campoWhere, valorWhere, campoSet, valorSet, nomeTabela])
// DELETE: cy.task('sql.deleteDB', [campoWhere, valorWhere, nomeTabela])
```

**Uso de Database Assertion:**
```js
// Verificar que controle de integração foi gravado
cy.task('sql.selectDB', ['nm_integracao', 'ESCALAS', 'tb_controle_integracoes_hub'])
  .then((rows) => {
    expect(rows.length).to.be.greaterThan(0)
    expect(rows[0].dataValues.qt_registros_processados).to.be.greaterThan(0)
  })

// Verificar ausência de log de erro (happy path)
cy.task('sql.selectDB', ['nm_campo', 'empresa', 'tb_log_erros_integracao'])
  .then((rows) => {
    expect(rows.length).to.eq(0)
  })
```

**Criação de Sequelize Model para tabela nova:**

Local: `cypress/fixtures/tabelas/<NomeDaTabela>.js`

```js
// cypress/fixtures/tabelas/tb_log_erros_integracao.js
const database = require('../db1/db')
const { DataTypes } = require('sequelize')

const TbLogErrosIntegracao = database.define(
  'tb_log_erros_integracao',
  {
    cd_empresa:    { type: DataTypes.INTEGER, primaryKey: true },
    cd_matricula:  { type: DataTypes.INTEGER, primaryKey: true },
    nm_dominio:    { type: DataTypes.STRING },
    nm_campo:      { type: DataTypes.STRING },
    cd_tipo_erro:  { type: DataTypes.STRING },
    ds_erro:       { type: DataTypes.STRING },
    cd_nivel_erro: { type: DataTypes.STRING },
  },
  {
    schema: 'hubrh',
    freezeTableName: true,
    timestamps: false,
    createdAt: false,
    updatedAt: false,
  }
)

database.sync()
module.exports = TbLogErrosIntegracao
```

**Regras:**
- Sempre usar `schema: 'hubrh'` para tabelas do hub
- Mapear apenas os campos usados nas assertions
- Reutilizar conexão `db1/db.js` — nunca criar nova conexão Sequelize
- Um arquivo de model por tabela
- Nome do arquivo = nome exato da tabela no banco

---

## Configuração de Ambiente

Adicionar a URL do serviço ao `cypress.env.json`:

```json
{
  "WORK_JOURNEY_ORCHESTRATOR_URL": "http://localhost:8080"
}
```

**Convenção de nome:**
- Slug do repositório sem prefixo `gcb-hr-jt-` ou `gcb-hr-hub-`
- Substituir `-` por `_` e UPPER_CASE
- Sufixar com `_URL`

---

## Estrutura de Saída Completa (por serviço)

```
gcb-hr-hub-automacao-cypress-back/
├── cypress/
│   ├── e2e/
│   │   └── <projeto-slug>/
│   │       ├── <dominio-1>.cy.js
│   │       └── <dominio-N>.cy.js
│   ├── fixtures/
│   │   ├── <projeto-slug>/
│   │   │   ├── <dominio-1>/
│   │   │   │   ├── payload_valido.json
│   │   │   │   └── payload_<cenario>.json
│   │   │   └── <dominio-N>/...
│   │   └── tabelas/
│   │       └── <NomeDaTabela>.js     ← apenas tabelas novas
│   └── support/
│       └── pages/
│           └── <projeto-slug>/
│               ├── <Dominio1>Api.js
│               └── <DominioN>Api.js
└── <projeto-testado>/
    └── .github/
        └── docs/
            └── testing/
                └── integration-tests.md   ← documentação gerada
```

---

## Template de Spec Completa

```js
// cypress/e2e/work-journey-orchestrator/prorrogacao.cy.js
const { ProrrogacaoApi } = require('../../support/pages/work-journey-orchestrator/ProrrogacaoApi')

context('Work Journey Orchestrator — Prorrogação', () => {

  describe('POST /prorrogacao', () => {

    it('[POST /prorrogacao] - Deve retornar 200 com payload válido', () => {
      cy.fixture('work-journey-orchestrator/prorrogacao/payload_valido.json').then((body) => {
        ProrrogacaoApi.processar(body).then((res) => {
          expect(res.status).to.eq(200)
        })
      })
    })

    it('[POST /prorrogacao] - Deve retornar 400 quando gatilho é inválido', () => {
      cy.fixture('work-journey-orchestrator/prorrogacao/payload_gatilho_invalido.json').then((body) => {
        ProrrogacaoApi.processar(body).then((res) => {
          expect(res.status).to.eq(400)
        })
      })
    })

    it('[POST /prorrogacao] - Deve retornar 400 quando empresa está ausente', () => {
      cy.fixture('work-journey-orchestrator/prorrogacao/payload_empresa_ausente.json').then((body) => {
        ProrrogacaoApi.processar(body).then((res) => {
          expect(res.status).to.eq(400)
        })
      })
    })

    it('[POST /prorrogacao] - Não deve gerar log de erro após processamento válido', () => {
      cy.fixture('work-journey-orchestrator/prorrogacao/payload_valido.json').then((body) => {
        ProrrogacaoApi.processar(body).then((res) => {
          expect(res.status).to.eq(200)
          cy.task('sql.selectDB', ['nm_dominio', 'PRORROGACAO', 'tb_log_erros_integracao'])
            .then((rows) => {
              expect(rows.length).to.eq(0)
            })
        })
      })
    })

  })
})
```

---

## Documentação Obrigatória

Após gerar os testes, criar (ou atualizar) o arquivo de documentação no projeto testado:

**Local:** `<projeto-testado>/.github/docs/testing/integration-tests.md`

**Conteúdo obrigatório:**
- Visão geral do escopo testado
- Tabela de endpoints cobertos com método, rota e cenários
- Pré-requisitos de ambiente (env vars, banco, serviço rodando)
- Como executar os testes
- Estrutura de arquivos gerados

---

## Checklist de Entrega

- [ ] Specs em `cypress/e2e/<projeto-slug>/` — uma por controller
- [ ] API Objects em `cypress/support/pages/<projeto-slug>/`
- [ ] Fixtures JSON em `cypress/fixtures/<projeto-slug>/` — um por cenário
- [ ] Sequelize Models em `cypress/fixtures/tabelas/` — apenas tabelas novas
- [ ] Env var adicionada ao `cypress.env.json`
- [ ] Documentação em `<projeto-testado>/.github/docs/testing/integration-tests.md`
