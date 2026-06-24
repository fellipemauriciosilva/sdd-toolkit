---
name: "cypress-mocha-api-testing"
description: "Cypress 13+ para testes de API REST — cy.request(), AJV schema validation, multi-ambiente, builders de dados, performance SLA, teardown automático. USE quando: validar contratos API, criar testes backend, automação de serviços REST, validação de schema JSON, testes de performance de API."
---

# Skill Cypress + Mocha API Testing (Padrão QAOps v2.0)

## 📋 Visão Geral da Skill

Esta skill orienta a geração de **testes de API backend** usando **Cypress 15+ com Mocha**, seguindo padrões QAOps de nível corporativo. Prioriza **validação de contrato**, **isolamento de testes**, **testes de performance** e **suporte multi-ambiente** usando **ES Modules (ESM)** exclusivamente.

## 🎯 Princípios Fundamentais

### Filosofia API First
- **Contratos como Fonte da Verdade**: JSON Schemas definem exatamente as expectativas da API
- **Prioridade na Camada de Serviço**: Foco na validação de lógica de negócio na camada mais estável
- **Integração Precoce**: Testar contra APIs reais desde o primeiro dia
- **Documentação Viva**: Testes servem como documentação executável da API

### Pilares QAOps
1. **Determinístico**: Mesma entrada → Mesma saída em qualquer ambiente QA
2. **Isolado**: Testes criam e limpam seus próprios dados
3. **Rastreável**: Tags estruturadas, logs e relatórios JUnit
4. **Seguro**: Sem credenciais reais, dados sensíveis mascarados
5. **Eficiente**: Execução paralela, helpers reutilizáveis

## 🛠️ Stack Técnico

```
Cypress 15+ (ESM)
├─ Mocha test runner
├─ Chai assertions
├─ AJV JSON Schema validator
├─ @cypress/grep (filtragem por tags)
└─ JUnit reporter (integração CI/CD)
```

## 📁 Estrutura de Projeto Esperada

```
/cypress
  /api                    → Specs de teste organizados por domínio de negócio
    /healthcheck          → Testes de disponibilidade
    /users                → Testes de gestão de usuários
    /orders               → Testes de processamento de pedidos
  /support
    /api-helpers.js       → Validação de schema, builders, utilitários
    /commands.js          → Comandos customizados do Cypress
    /e2e.js               → Configuração global
  /fixtures               → Dados de teste estáticos (JSON)
  /config                 → Configurações por ambiente (dev.js, qa.js, stg.js)
/scripts                  → Scripts utilitários
/reports                  → Relatórios JUnit XML
cypress.config.js         → Configuração ESM principal
package.json              → Tipo ESM, engines Node 20+
```

## ✅ Padrões Obrigatórios

### 1️⃣ **Sintaxe ESM (SEMPRE)**

```javascript
// ✅ CORRETO
import { validateSchema } from '../../support/api-helpers.js'
export function myHelper() { }

// ❌ PROIBIDO
const { validateSchema } = require('./api-helpers')
module.exports = { myHelper }
```

### 2️⃣ **Estrutura de Teste (Padrão AAA)**

```javascript
describe('Domain API @tag1 @tag2', () => {
  let testResourceIds = []
  
  afterEach(() => {
    // Teardown: limpar recursos criados
    testResourceIds.forEach(id => {
      cy.request('DELETE', `/api/resource/${id}`)
    })
    testResourceIds = []
  })
  
  it('POST /resource - Deve criar recurso válido @smoke @contract', () => {
    // Arrange: Schema e dados de teste
    const resourceSchema = { /* JSON Schema */ }
    const testData = { name: 'qaops-test-resource' }
    
    // Act: Executar chamada à API
    cy.apiRequest('POST', '/api/resource', testData).then(response => {
      // Assert: Validar contrato e regras de negócio
      assertStatus(response, 201)
      validateSchema(response, resourceSchema)
      expect(response.body.name).to.include('qaops-test')
      
      testResourceIds.push(response.body.id)
      cy.task('log', `Recurso criado: ${response.body.id}`)
    })
  })
})
```

### 3️⃣ **Validação de Schema (OBRIGATÓRIA)**

```javascript
import { validateSchema, assertStatus } from '../../support/api-helpers.js'

const userSchema = {
  type: 'object',
  required: ['id', 'name', 'email'],
  properties: {
    id: { type: 'string' },
    name: { type: 'string', minLength: 3 },
    email: { type: 'string', format: 'email' }
  }
}

cy.apiRequest('GET', '/users/123').then(response => {
  assertStatus(response, 200)
  validateSchema(response, userSchema)
})
```

### 4️⃣ **Configuração Multi-Ambiente**

**Arquivo: `cypress/config/qa.js`**
```javascript
const dados = {
  baseApi: "https://api.qa.example.com",
  env: {
    ENVIRONMENT: "qa",
    API_TIMEOUT: 15000,
    ENABLE_CONTRACT_VALIDATION: true,
    PERFORMANCE_THRESHOLD: 2000
  }
}
export default dados
```

**Carregar dinamicamente no `cypress.config.js`:**
```javascript
const environment = process.env.ENVIRONMENT || 'qa'
const configModule = await import(`./cypress/config/${environment}.js`)
const dados = configModule.default

export default defineConfig({
  e2e: {
    baseUrl: dados.baseApi,
    env: { ...dados.env }
  }
})
```

### 5️⃣ **Comandos Customizados**

**Arquivo: `cypress/support/commands.js`**

```javascript
import { buildTestPayload } from './api-helpers.js'

/**
 * cy.apiRequest - Requisição API padronizada com logging e tracking de performance
 */
Cypress.Commands.add('apiRequest', (method, url, body = null, headers = {}) => {
  const startTime = Date.now()
  const baseApi = Cypress.config('baseUrl')
  const fullUrl = url.startsWith('http') ? url : `${baseApi}${url}`
  
  const options = {
    method,
    url: fullUrl,
    headers: { 'Content-Type': 'application/json', ...headers },
    timeout: Cypress.config('env')?.API_TIMEOUT || 15000,
    failOnStatusCode: false
  }
  
  if (body) options.body = body
  
  cy.task('log', `📤 ${method} ${fullUrl}`)
  
  return cy.request(options).then(response => {
    const responseTime = Date.now() - startTime
    response.responseTime = responseTime
    cy.task('log', `📥 ${method} ${url} - ${response.status} (${responseTime}ms)`)
    return response
  })
})

/**
 * cy.createTestData - Gerar dados sintéticos de teste
 */
Cypress.Commands.add('createTestData', (type, overrides = {}) => {
  const data = buildTestPayload(type, overrides)
  cy.task('log', `🔧 Dados de teste criados: ${type}`)
  return cy.wrap(data)
})

/**
 * cy.validatePerformance - Validação de SLA
 */
Cypress.Commands.add('validatePerformance', (requestFn, maxTime) => {
  const startTime = Date.now()
  return requestFn().then(response => {
    const responseTime = Date.now() - startTime
    expect(responseTime).to.be.lessThan(maxTime)
    cy.task('log', `⚡ Performance OK: ${responseTime}ms < ${maxTime}ms`)
    return response
  })
})
```

### 6️⃣ **Helpers de API**

**Arquivo: `cypress/support/api-helpers.js`**

```javascript
import Ajv from 'ajv'
import addFormats from 'ajv-formats'

export function validateSchema(response, schema) {
  const ajv = new Ajv({ allErrors: true, strict: false })
  addFormats(ajv)
  
  const validate = ajv.compile(schema)
  const valid = validate(response.body)
  
  if (!valid) {
    const errors = JSON.stringify(validate.errors, null, 2)
    cy.task('log', `❌ Schema validation failed: ${errors}`)
    throw new Error(`Schema validation failed: ${errors}`)
  }
  
  cy.task('log', '✅ Schema validation passed')
  return true
}

export function assertStatus(response, expectedCode) {
  expect(response.status).to.equal(expectedCode)
  cy.task('log', `✅ Status: ${expectedCode}`)
}

export function buildTestPayload(type, overrides = {}) {
  const timestamp = Date.now()
  const payloads = {
    user: {
      name: `qaops-test-user-${timestamp}`,
      email: `qaops-test-${timestamp}@example.com`
    },
    order: {
      customerId: `qaops-test-customer-${timestamp}`,
      items: [{ sku: 'TEST-SKU-001', quantity: 1 }]
    }
  }
  return { ...payloads[type], ...overrides }
}

export function maskSensitiveData(data) {
  if (!data) return ''
  const str = String(data)
  if (str.length <= 4) return '***'
  return str.substring(0, 2) + '***' + str.substring(str.length - 2)
}
```

## 🏷️ Estratégia de Tags

```javascript
describe('Users API @regressivo @users @contract', () => {
  it('GET /users/:id - Deve retornar usuário @smoke', () => {})
  it('POST /users - Deve criar usuário com dados válidos @negative', () => {})
  it('GET /users - Deve responder dentro do SLA @performance', () => {})
})
```

**Categorias de Tags:**
- `@smoke` - Testes de caminho crítico
- `@regressivo` - Suite completa de regressão
- `@contract` - Testes de validação de schema
- `@negative` - Testes de tratamento de erros
- `@performance` - Testes de validação de SLA
- `@domain` - Domínio de negócio (users, orders, payments)

**Execução:**
```bash
npm run cy:test:smoke        # Apenas testes @smoke
npm run cy:test:contract     # Apenas testes @contract
cypress run --env grepTags="@users+@smoke"  # Operação AND
```

## 🔒 Práticas de Segurança e Dados

### ✅ SEMPRE
- Usar dados sintéticos com prefixo `qaops-test-`
- Mascarar dados sensíveis em logs: `maskSensitiveData(cpf)`
- Armazenar secrets em `Cypress.env()`, não hardcoded
- Usar timestamps/UUIDs dinâmicos para evitar colisões
- Implementar teardown em `afterEach()` ou `after()`

### ❌ NUNCA
- CPF, emails, IDs de produção reais
- Credenciais hardcoded
- IDs fixos que quebram em execução paralela
- Testes que modificam estado compartilhado
- Pular validação de schema

## 📊 Integração de Testes de Performance

```javascript
it('GET /api/products - Deve atender SLA @performance', () => {
  const maxTime = Cypress.config('env')?.PERFORMANCE_THRESHOLD || 2000
  
  cy.validatePerformance(
    () => cy.apiRequest('GET', '/api/products'),
    maxTime
  ).then(response => {
    assertStatus(response, 200)
    expect(response.body.length).to.be.greaterThan(0)
  })
})
```

## 🔄 Padrão de Isolamento de Testes

```javascript
describe('Orders API @orders', () => {
  let testOrderIds = []
  
  afterEach(() => {
    // Limpeza automática
    testOrderIds.forEach(orderId => {
      cy.apiRequest('DELETE', `/api/orders/${orderId}`)
    })
    testOrderIds = []
  })
  
  it('POST /orders - Deve criar pedido', () => {
    cy.createTestData('order').then(orderData => {
      cy.apiRequest('POST', '/api/orders', orderData).then(response => {
        assertStatus(response, 201)
        testOrderIds.push(response.body.id)
      })
    })
  })
})
```

## 🚀 Integração CI/CD

**Configuração do Reporter JUnit:**

```javascript
// cypress.config.js
export default defineConfig({
  reporter: 'junit',
  reporterOptions: {
    mochaFile: 'reports/junit-functional-[hash].xml',
    toConsole: true,
    testCaseSwitchClassnameAndName: false,
    suiteTitleSeparatedBy: ' > ',
    useFullSuiteTitle: true
  }
})
```

**Scripts do Package:**
```json
{
  "scripts": {
    "cy:test": "cypress run --config video=false",
    "cy:test:api": "cypress run --spec 'cypress/api/**/*.cy.js'",
    "cy:test:smoke": "cypress run --env grepTags=@smoke",
    "cy:test:parallel": "cypress run --parallel --record --key <key>"
  }
}
```

## 🧪 Complete Test Example

```javascript
/**
 * Users API Tests
 * 
 * @epic Backend API Testing
 * @feature User Management
 * @domain Users
 */

import { validateSchema, assertStatus } from '../../support/api-helpers.js'

describe('Users API @regressivo @users @contract', () => {
  let createdUserIds = []
  
  afterEach(() => {
    createdUserIds.forEach(userId => {
      cy.apiRequest('DELETE', `/api/users/${userId}`)
    })
    createdUserIds = []
  })
  
  const userSchema = {
    type: 'object',
    required: ['id', 'name', 'email', 'createdAt'],
    properties: {
      id: { type: 'string', format: 'uuid' },
      name: { type: 'string', minLength: 3 },
      email: { type: 'string', format: 'email' },
      createdAt: { type: 'string', format: 'date-time' }
    }
  }
  
  it('POST /users - Deve criar usuário com dados válidos @smoke', () => {
    // Arrange
    cy.createTestData('user', { name: 'John Doe' }).then(userData => {
      // Act
      cy.apiRequest('POST', '/api/users', userData).then(response => {
        // Assert
        assertStatus(response, 201)
        validateSchema(response, userSchema)
        
        expect(response.body.email).to.include('qaops-test')
        expect(response.body.name).to.equal('John Doe')
        
        createdUserIds.push(response.body.id)
        cy.task('log', `✅ Usuário criado: ${response.body.id}`)
      })
    })
  })
  
  it('GET /users/:id - Deve retornar detalhes do usuário @smoke', () => {
    // Given: Usuário existe
    cy.createTestData('user').then(userData => {
      cy.apiRequest('POST', '/api/users', userData).then(createResponse => {
        const userId = createResponse.body.id
        createdUserIds.push(userId)
        
        // When: Requisita detalhes do usuário
        cy.apiRequest('GET', `/api/users/${userId}`).then(response => {
          // Then: Deve retornar dados corretos
          assertStatus(response, 200)
          validateSchema(response, userSchema)
          expect(response.body.id).to.equal(userId)
        })
      })
    })
  })
  
  it('POST /users - Deve rejeitar email inválido @negative', () => {
    // Arrange: Dados inválidos
    const invalidData = {
      name: 'qaops-test-user',
      email: 'invalid-email'
    }
    
    // Act
    cy.apiRequest('POST', '/api/users', invalidData).then(response => {
      // Assert: Deve retornar erro de validação
      assertStatus(response, 400)
      expect(response.body.message).to.include('email')
    })
  })
  
  it('GET /users - Deve atender SLA de performance @performance', () => {
    const maxTime = Cypress.config('env')?.PERFORMANCE_THRESHOLD || 2000
    
    cy.validatePerformance(
      () => cy.apiRequest('GET', '/api/users'),
      maxTime
    ).then(response => {
      assertStatus(response, 200)
      expect(response.body).to.be.an('array')
    })
  })
})
```

## 🔧 Guia de Solução de Problemas

### Problema: "Cannot use import statement outside a module"
**Solução:** Garanta que `package.json` tenha `"type": "module"` e Node.js 20+

### Problema: Validação de schema sempre falha
**Solução:** Verifique strictness do schema. Use `{ strict: false }` na config do AJV

### Problema: Testes falham em execução paralela
**Solução:** Garanta dados únicos de teste (timestamps/UUIDs) e teardown adequado

### Problema: Testes de performance instáveis
**Solução:** Use helper `cy.validatePerformance()`, verifique condições de rede

### Problema: Configuração de ambiente não carrega
**Solução:** Verifique que `process.env.ENVIRONMENT` está definido e arquivo existe em `/config`

## 📚 Referência Rápida

### Imports Essenciais
```javascript
import { validateSchema, assertStatus, buildTestPayload } from '../../support/api-helpers.js'
```

### Template de Estrutura de Teste
```javascript
describe('API @tags', () => {
  let cleanup = []
  afterEach(() => { /* cleanup */ })
  
  it('ACTION - Should EXPECTED @tags', () => {
    // Arrange: Schema + Data
    // Act: API Call
    // Assert: Status + Schema + Business Rules
  })
})
```

### Comandos Comuns
```javascript
cy.apiRequest(method, url, body)
cy.createTestData(type, overrides)
cy.validatePerformance(fn, maxTime)
```

### Padrões de Tags
```
@smoke @regressivo @contract @negative @performance
@domain (users, orders, products)
```

## 🎯 Quando Usar Esta Skill

### ✅ Usar Quando:
- Criar novos specs de teste de API
- Implementar validação de contrato
- Construir geradores de dados de teste
- Configurar ambientes múltiplos
- Adicionar validação de performance
- Debugar falhas em testes de API
- Migrar do Postman para Cypress
- Implementar padrões de isolamento de testes

### ❌ Não Usar Quando:
- Escrever testes de UI/E2E com navegador
- Criar testes unitários
- Implementar testes de carga
- Fazer exploração manual de APIs

## 📋 Checklist para Novos Testes de API

- [ ] Imports ESM com extensões `.js`
- [ ] JSON Schema definido inline ou importado
- [ ] Dados de teste usam prefixo `qaops-test-`
- [ ] Teardown `afterEach()` implementado
- [ ] `validateSchema()` chamado nas respostas
- [ ] `assertStatus()` valida códigos de status
- [ ] Tags estruturadas aplicadas (`@smoke`, `@contract`)
- [ ] `cy.task('log', message)` para rastreabilidade
- [ ] Threshold de performance validado se aplicável
- [ ] Sem IDs hardcoded ou dados reais
- [ ] Padrão AAA (Arrange-Act-Assert) seguido

## 🚦 Automação de Workflow

1. **Ler** arquivos de teste existentes para entender padrões
2. **Gerar** novos specs de teste usando templates
3. **Validar** definições de schema contra docs da API
4. **Implementar** teardown para recursos criados
5. **Adicionar** testes de performance para endpoints críticos
6. **Taguear** apropriadamente para execução seletiva
7. **Verificar** que testes rodam isolados (parallel safe)

---

**Versão da Skill:** 1.0
**Última Atualização:** 30/04/2026  
**Compatibilidade:** Cypress 15+, Node.js 20+, ESM apenas