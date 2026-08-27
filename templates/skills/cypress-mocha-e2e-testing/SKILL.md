---
name: "cypress-mocha-e2e-testing"
description: "Cypress 13+ com Mocha para testes E2E de Front-End Web — Custom Commands, fixtures por domínio, multi-ambiente, cy.visit(), cy.intercept(). USE quando: criar testes de interface web, validar jornadas de usuário, testar fluxos completos UI, configurar ambientes QA/DEV/PROD, ou gerar specs E2E Web."
---

# Cypress Mocha E2E Testing — Example Organization

Padrões e boas práticas para automação de testes **E2E de Front-End Web** com Cypress 13+ e Mocha.

---

## ✅ Objetivos

- Acelerar criação de testes E2E de interface web
- Garantir uniformidade de estrutura e código
- Reduzir código boilerplate
- Aumentar cobertura e qualidade de testes automatizados

---

## 📂 Estrutura Padrão de Projeto

**Organização por domínio** (login, dashboard, checkout, etc.):

```
/cypress
  ├── /e2e
  │     ├── /ui
  │     │     ├── /login
  │     │     │     ├── login.spec.js
  │     │     │     ├── recuperar-senha.spec.js
  │     │     ├── /dashboard
  │     │     │     ├── dashboard.spec.js
  │     │     ├── /checkout
  │     │     │     ├── carrinho.spec.js
  │     │     │     ├── pagamento.spec.js
  ├── /fixtures
  │     ├── /login
  │     │     ├── usuarios.json
  │     │     ├── credenciais.json
  │     ├── /dashboard
  │     │     ├── dadosDashboard.json
  │     ├── /checkout
  │     │     ├── produtos.json
  │     │     ├── enderecos.json
  ├── /support
  │     ├── /commands
  │     │     ├── loginCommands.js
  │     │     ├── dashboardCommands.js
  │     │     ├── checkoutCommands.js
  │     ├── /utils
  │     │     ├── dateHelper.js
  │     │     ├── priceFormatter.js
  │     └── e2e.js
  ├── /config
  │     ├── qa.js
  │     ├── dev.js
  │     └── prod.js
  ├── cypress.config.js
```

---

## 🌍 Configuração Multi-Ambiente

Suporte a múltiplos ambientes (QA, DEV, PROD) via arquivos de configuração separados.

### `config/qa.js`
```javascript
module.exports = {
  baseUrl: "https://qa.example.com",
  baseApi: "https://api-qa.example.com",
  viewportHeight: 768,
  viewportWidth: 1440,
  defaultCommandTimeout: 10000,
  requestTimeout: 15000
}
```

### `config/dev.js`
```javascript
module.exports = {
  baseUrl: "https://dev.example.com",
  baseApi: "https://api-dev.example.com",
  viewportHeight: 768,
  viewportWidth: 1440
}
```

### `config/prod.js`
```javascript
module.exports = {
  baseUrl: "https://www.example.com",
  baseApi: "https://api.example.com",
  viewportHeight: 768,
  viewportWidth: 1440
}
```

### `cypress.config.js` (raiz)
```javascript
const { defineConfig } = require('cypress');

// Determina qual config carregar via env var
const environment = process.env.CYPRESS_ENV || 'qa';
const envConfig = require(`./cypress/config/${environment}.js`);

module.exports = defineConfig({
  e2e: {
    ...envConfig,
    setupNodeEvents(on, config) {
      // implementar node event listeners
    },
  },
});
```

### Executar com ambiente específico
```bash
# QA (padrão)
npx cypress run

# DEV
CYPRESS_ENV=dev npx cypress run

# PROD
CYPRESS_ENV=prod npx cypress run
```

---

## 🧩 Regras de Nomeação

| Tipo | Padrão | Exemplos |
|------|--------|----------|
| **Pastas/Arquivos** | `snake-case` | `login.spec.js`, `recuperar-senha.spec.js` |
| **Custom Commands** | `camelCase` | `fillLoginForm`, `navigateToHome`, `selectProduct` |
| **Variáveis/Constantes** | `camelCase` | `userEmail`, `productName`, `cartTotal` |
| **Fixtures** | `camelCase` | `usuarios.json`, `dadosDashboard.json` |

---

## 🛠️ Estrutura de Teste com Mocha

Cypress usa **Mocha** como framework padrão: `describe`, `it`, `beforeEach`, `afterEach`.

### Template Padrão
```javascript
describe('Login', () => {
  beforeEach(() => {
    cy.navigateToHome();
  });

  it('Deve realizar login com sucesso', () => {
    cy.fillLoginForm('usuario@teste.com', '123456');
    cy.get('button[type="submit"]').click();

    cy.url().should('include', '/dashboard');
    cy.get('.welcome-message').should('contain', 'Bem-vindo');
  });

  it('Deve exibir mensagem de erro com senha inválida', () => {
    cy.fillLoginForm('usuario@teste.com', 'senhaerrada');
    cy.get('button[type="submit"]').click();

    cy.get('.error-message').should('contain', 'Senha inválida');
  });

  it('Deve validar que botão de submit está desabilitado com campos vazios', () => {
    cy.get('button[type="submit"]').should('be.disabled');
  });
});
```

---

## ⚡ Custom Commands (Actions Commands)

**Sempre criar ações frequentes como Custom Commands** para evitar repetição e facilitar manutenção.

### Exemplo: `/support/commands/loginCommands.js`
```javascript
Cypress.Commands.add('fillLoginForm', (email, senha) => {
  cy.get('#email').type(email);
  cy.get('#senha').type(senha, { log: false }); // log: false para não expor senha
});

Cypress.Commands.add('navigateToHome', () => {
  cy.visit('/login');
});

Cypress.Commands.add('doLogin', (email, senha) => {
  cy.fillLoginForm(email, senha);
  cy.get('button[type="submit"]').click();
});
```

### Exemplo: `/support/commands/dashboardCommands.js`
```javascript
Cypress.Commands.add('verifyDashboardElements', () => {
  cy.get('.sidebar').should('be.visible');
  cy.get('.header-user-name').should('exist');
  cy.get('.notifications').should('exist');
});

Cypress.Commands.add('navigateToDashboard', () => {
  cy.visit('/dashboard');
  cy.verifyDashboardElements();
});
```

### Exemplo: `/support/commands/checkoutCommands.js`
```javascript
Cypress.Commands.add('addProductToCart', (productId) => {
  cy.get(`[data-product-id="${productId}"]`).click();
  cy.get('.add-to-cart-button').click();
  cy.get('.cart-notification').should('contain', 'Produto adicionado');
});

Cypress.Commands.add('fillShippingAddress', (address) => {
  cy.get('#cep').type(address.cep);
  cy.get('#rua').type(address.rua);
  cy.get('#numero').type(address.numero);
  cy.get('#cidade').type(address.cidade);
});

Cypress.Commands.add('selectPaymentMethod', (method) => {
  cy.get(`input[value="${method}"]`).check();
});
```

### Registrar Custom Commands

No arquivo `/support/e2e.js`, importar todos os arquivos de commands:

```javascript
import './commands/loginCommands';
import './commands/dashboardCommands';
import './commands/checkoutCommands';
```

✅ **Vantagens de Custom Commands**:
- Reduz duplicação de código
- Facilita manutenção centralizada
- Testes mais limpos e focados em validação
- Reutilização em múltiplos specs

---

## 📚 Fixtures: Massa de Dados Centralizada

**NÃO hardcode dados de teste nos specs**. Use fixtures para centralizar e reutilizar.

### Exemplo: `/fixtures/login/usuarios.json`
```json
[
  {
    "nome": "Ana Souza",
    "email": "ana.souza@teste.com",
    "senha": "senha123"
  },
  {
    "nome": "Bruno Lima",
    "email": "bruno.lima@teste.com",
    "senha": "senha456"
  }
]
```

### Exemplo: `/fixtures/checkout/produtos.json`
```json
[
  {
    "id": "prod-001",
    "nome": "Notebook Dell",
    "preco": 2999.90,
    "estoque": 10
  },
  {
    "id": "prod-002",
    "nome": "Mouse Logitech",
    "preco": 89.90,
    "estoque": 50
  }
]
```

### Uso no Teste
```javascript
describe('Login com Fixture', () => {
  beforeEach(() => {
    cy.fixture('login/usuarios').as('usuariosFixture');
  });

  it('Deve realizar login com primeiro usuário da fixture', function () {
    const usuario = this.usuariosFixture[0];
    
    cy.navigateToHome();
    cy.fillLoginForm(usuario.email, usuario.senha);
    cy.get('button[type="submit"]').click();

    cy.get('.welcome-message').should('contain', usuario.nome);
  });
});
```

### Benefícios de Fixtures
- Centralização de massa de dados
- Fácil manutenção (um único local)
- Reutilização em múltiplos testes
- Separação de dados e lógica de teste

---

## 🎯 Interceptação de Requisições: cy.intercept()

Use `cy.intercept()` para:
- Aguardar requisições antes de validar UI
- Mockar respostas de API
- Validar payloads enviados

### Exemplo: Aguardar Requisição Real
```javascript
describe('Dashboard', () => {
  it('Deve carregar dados do dashboard', () => {
    cy.intercept('GET', '/api/dashboard/stats').as('getDashboardStats');
    
    cy.navigateToDashboard();
    
    cy.wait('@getDashboardStats').then((interception) => {
      expect(interception.response.statusCode).to.eq(200);
      expect(interception.response.body).to.have.property('totalVendas');
    });
    
    cy.get('.total-vendas').should('be.visible');
  });
});
```

### Exemplo: Mockar Resposta de API
```javascript
describe('Dashboard com Mock', () => {
  it('Deve exibir dados mockados quando API não estiver disponível', () => {
    cy.intercept('GET', '/api/dashboard/stats', {
      statusCode: 200,
      body: {
        totalVendas: 12500,
        totalClientes: 340,
        ticketMedio: 125.50
      }
    }).as('mockDashboard');
    
    cy.navigateToDashboard();
    cy.wait('@mockDashboard');
    
    cy.get('.total-vendas').should('contain', '12500');
    cy.get('.total-clientes').should('contain', '340');
  });
});
```

---

## 📊 Exemplo Completo: Fluxo de Checkout

```javascript
describe('Checkout - Fluxo Completo', () => {
  beforeEach(() => {
    cy.fixture('checkout/produtos').as('produtosFixture');
    cy.fixture('checkout/enderecos').as('enderecosFixture');
  });

  it('Deve realizar compra completa com sucesso', function () {
    const produto = this.produtosFixture[0];
    const endereco = this.enderecosFixture[0];

    // Interceptar chamada de finalização
    cy.intercept('POST', '/api/checkout/finalizar').as('finalizarCompra');

    // Etapa 1: Adicionar produto ao carrinho
    cy.visit('/produtos');
    cy.addProductToCart(produto.id);

    // Etapa 2: Ir para checkout
    cy.get('.cart-icon').click();
    cy.get('.btn-checkout').click();

    // Etapa 3: Preencher endereço
    cy.fillShippingAddress(endereco);

    // Etapa 4: Selecionar forma de pagamento
    cy.selectPaymentMethod('cartao');

    // Etapa 5: Finalizar compra
    cy.get('.btn-finalizar').click();

    // Validação
    cy.wait('@finalizarCompra').then((interception) => {
      expect(interception.response.statusCode).to.eq(201);
      expect(interception.response.body).to.have.property('pedidoId');
    });

    cy.url().should('include', '/pedido-confirmado');
    cy.get('.confirmation-message').should('contain', 'Pedido realizado com sucesso');
  });

  it('Deve exibir erro quando estoque insuficiente', function () {
    const produto = this.produtosFixture[1];

    cy.intercept('POST', '/api/checkout/finalizar', {
      statusCode: 400,
      body: {
        erro: 'Estoque insuficiente'
      }
    }).as('erroEstoque');

    cy.visit('/produtos');
    cy.addProductToCart(produto.id);
    cy.get('.cart-icon').click();
    cy.get('.btn-checkout').click();
    cy.get('.btn-finalizar').click();

    cy.wait('@erroEstoque');
    cy.get('.error-message').should('contain', 'Estoque insuficiente');
  });
});
```

---

## 📚 Organização por Domínio

**Sempre organize testes, fixtures, commands e utils por contexto de negócio**:

```
/cypress
  ├── /e2e/ui
  │     ├── /login          # Domínio: autenticação
  │     ├── /dashboard      # Domínio: painel
  │     └── /checkout       # Domínio: vendas
  ├── /fixtures
  │     ├── /login
  │     ├── /dashboard
  │     └── /checkout
  ├── /support/commands
  │     ├── loginCommands.js
  │     ├── dashboardCommands.js
  │     └── checkoutCommands.js
```

**Benefícios**:
- Facilita manutenção conforme projeto cresce
- Melhora legibilidade e navegação
- Reduz acoplamento entre domínios

---

## 🧩 Exportação e Importação de Utilitários

Modularize funções utilitárias em arquivos separados.

### Exemplo: `/support/utils/dateHelper.js`
```javascript
export function formatDate(date) {
  return new Intl.DateTimeFormat('pt-BR').format(date);
}

export function addDays(date, days) {
  const result = new Date(date);
  result.setDate(result.setDate() + days);
  return result;
}
```

### Uso no Teste
```javascript
import { formatDate, addDays } from '../../support/utils/dateHelper';

describe('Filtro de Datas', () => {
  it('Deve filtrar vendas por data futura', () => {
    const dataFutura = addDays(new Date(), 7);
    cy.log(`Data futura: ${formatDate(dataFutura)}`);
    
    cy.get('#data-inicio').type(formatDate(dataFutura));
    cy.get('.btn-filtrar').click();
  });
});
```

---

## 📝 Boas Práticas Gerais

### ✅ FAZER
- Usar **assertions claras e específicas**
- Usar **Custom Commands** para ações repetitivas
- Usar **cy.intercept()** + **cy.wait()** para aguardar requisições (não usar `cy.wait(5000)`)
- Organizar testes por **domínio de negócio**
- Usar **fixtures** para massa de dados
- Testes devem ser **independentes** (não dependem de execução anterior)
- Usar **data-testid** para seletores quando possível

### ❌ EVITAR
- Waits fixos (`cy.wait(5000)`) — usar waits dinâmicos (`cy.intercept`, `cy.wait('@alias')`)
- Hardcode de dados de teste no spec
- Seletores CSS frágeis (ex: `.btn.primary.large`) — preferir `[data-testid="submit-button"]`
- Testes longos (mais de 10 ações) — quebrar em cenários menores
- Dependência entre testes — cada teste deve rodar isoladamente

---

## 🎯 Estrutura de Assertions

### Validações de UI
```javascript
// Visibilidade
cy.get('.elemento').should('be.visible');
cy.get('.elemento').should('not.exist');

// Conteúdo de texto
cy.get('.mensagem').should('contain', 'Sucesso');
cy.get('.titulo').should('have.text', 'Dashboard');

// Atributos
cy.get('button').should('be.disabled');
cy.get('input').should('have.value', 'teste@email.com');
cy.get('a').should('have.attr', 'href', '/logout');

// Estado
cy.get('input[type="checkbox"]').should('be.checked');
cy.get('.dropdown').should('have.class', 'active');
```

### Validações de URL
```javascript
cy.url().should('include', '/dashboard');
cy.url().should('eq', 'https://qa.example.com/login');
```

### Validações de Requisições
```javascript
cy.wait('@getUser').its('response.statusCode').should('eq', 200);
cy.wait('@createOrder').its('response.body').should('have.property', 'orderId');
```

---

## 📊 Tags e Categorização

Use tags (via nome do teste ou plugins) para categorizar e executar seletivamente:

```javascript
describe('Login @smoke @critical', () => {
  it('Deve realizar login com sucesso @happy-path', () => {
    // teste
  });

  it('Deve validar senha incorreta @negative', () => {
    // teste
  });
});
```

Executar por tag (requer plugin como `cypress-grep`):
```bash
npx cypress run --env grep="@smoke"
npx cypress run --env grep="@critical"
```

---

## 🚀 Exemplo de Spec Completo

**Arquivo:** `/cypress/e2e/ui/login/login.spec.js`

```javascript
describe('Login @smoke @critical', () => {
  beforeEach(() => {
    cy.fixture('login/usuarios').as('usuarios');
    cy.navigateToHome();
  });

  it('Deve realizar login com sucesso @happy-path', function () {
    const usuario = this.usuarios[0];

    cy.fillLoginForm(usuario.email, usuario.senha);
    cy.get('button[type="submit"]').click();

    cy.url().should('include', '/dashboard');
    cy.get('.welcome-message').should('contain', usuario.nome);
  });

  it('Deve exibir erro com senha inválida @negative', function () {
    const usuario = this.usuarios[0];

    cy.fillLoginForm(usuario.email, 'senhaErrada');
    cy.get('button[type="submit"]').click();

    cy.get('.error-message').should('contain', 'Senha inválida');
    cy.url().should('include', '/login');
  });

  it('Deve validar botão desabilitado com campos vazios @edge-case', () => {
    cy.get('button[type="submit"]').should('be.disabled');
  });

  it('Deve exibir erro com email inválido @negative', () => {
    cy.fillLoginForm('emailinvalido', '123456');
    cy.get('button[type="submit"]').click();

    cy.get('.error-message').should('contain', 'Email inválido');
  });
});
```

---

## 🎯 Quando Usar Esta Skill

✅ **USE quando**:
- Criar testes de interface web (jornadas do usuário)
- Validar fluxos E2E completos (UI + API + Backend)
- Configurar ambientes QA/DEV/PROD
- Implementar Custom Commands reutilizáveis
- Organizar fixtures por domínio
- Interceptar e mockar requisições

❌ **NÃO USE quando**:
- Testes de API puro (sem UI) → usar `cypress-api-testing`
- Testes de contrato/schema de API → usar `cypress-api-testing`
- Testes BDD com Cucumber → usar `cypress-cucumber-bdd` (se existir)

---

## 📖 Referências

- [Cypress Docs](https://docs.cypress.io)
- [Cypress Best Practices](https://docs.cypress.io/guides/references/best-practices)
- [Mocha Documentation](https://mochajs.org/)
- Padrões Example Organization Tech (este documento)