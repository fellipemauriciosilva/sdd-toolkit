---
name: "zephyr-scale"
description: "Zephyr Scale (Jira) — Gestão de casos de teste, ciclos, planos, CSV import/export, campos customizados, rastreabilidade. USE quando: criar casos de teste Zephyr, gerar CSV para importação, configurar campos customizados (Bandeira, Canal, Automação), ou gerar cenários BDD via Rovo."
---

# Zephyr Scale — Gestão de Testes Enterprise (Padrão QAOps)

Padrões e boas práticas para **gestão de testes** com Zephyr Scale no contexto do Grupo Example Organization, incluindo padronização de campos, geração de CSV e governança de qualidade.

---

## ✅ Objetivos

- Padronizar gestão de casos de teste, ciclos e planos
- Garantir rastreabilidade entre Jira e testes automatizados
- Facilitar geração de indicadores e dashboards de governança
- Acelerar criação de cenários via IA (Rovo)

---

## 🎯 Princípios QAOps

1. **Rastreabilidade Total**: Todo teste vinculado a uma issue Jira
2. **Padronização de Campos**: Campos customizados consistentes (Bandeira, Canal, Automação)
3. **CSV Seguro**: Sem aspas duplas, separação por vírgula, texto sanitizado
4. **Governança Visual**: Dashboards de cobertura e qualidade

---

## 📋 Padronização de Campos

### Campos Obrigatórios para Padronização

Para garantir integração com **Dashboard de Governança de Testes**, os seguintes campos **DEVEM** ser padronizados:

| Entidade | Campos Obrigatórios |
|----------|---------------------|
| **Caso de Teste** | Status, Prioridade, Rótulos, Bandeira, Canal, Automação |
| **Ciclo de Teste** | Status, Bandeira, Canal, Ambiente, Framework, Execução Assistida, URL |
| **Plano de Teste** | Status, Rótulos |

---

## 🧪 Caso de Teste — Campos Customizados

### 1️⃣ Status

**Valores Permitidos:**
- `Manual`
- `Automatizado`

**Uso:**
```yaml
Status: Manual  # ou Automatizado
```

---

### 2️⃣ Prioridade

**Valores Permitidos:**
- `High`
- `Normal`
- `Low`

**Uso:**
```yaml
Prioridade: High
```

---

### 3️⃣ Rótulos (Labels)

**Padrões Recomendados:**

| Categoria | Exemplos |
|-----------|----------|
| **Funcionalidade** | `endereco`, `login`, `checkout` |
| **Tipo de Teste** | `@regressivo`, `@smoke` |
| **Origem IA** | `LOG_IA` (para testes criados/automatizados via Rovo) |

**Uso:**
```yaml
Rótulos: @login, @smoke, LOG_IA
```

---

### 4️⃣ Bandeira

**Valores Permitidos:**
- `Example Organization`
- `Example Brand A`
- `Extra`
- `Corp`

**Criação do Campo Customizado:**

1. Ir em **Configuration** → **Custom Fields** → **Test Cases**
2. Nome: `Bandeira`
3. Tipo: `Select List (Multi Choice)`
4. Adicionar opções: Example Organization, Example Brand A, Extra, Corp

**Uso:**
```yaml
Bandeira: Example Organization, Example Brand A
```

---

### 5️⃣ Canal

**Valores Permitidos:**
- `Web`
- `MSite`
- `App iOS`
- `App Android`
- `API`
- `Legado`

**Criação do Campo Customizado:**

1. Ir em **Configuration** → **Custom Fields** → **Test Cases**
2. Nome: `Canal`
3. Tipo: `Select List (Single Choice)`
4. Adicionar opções: Web, MSite, App iOS, App Android, API, Legado

**Uso:**
```yaml
Canal: Web
```

---

### 6️⃣ Automação

**Valores Permitidos:**
- `Não aplicável`
- `Candidato à automação`
- `Em desenvolvimento`
- `Automatizado`
- `Obsoleto`

**Criação do Campo Customizado:**

1. Ir em **Configuration** → **Custom Fields** → **Test Cases**
2. Nome: `Automação`
3. Tipo: `Select List (Single Choice)`
4. Adicionar opções conforme lista acima

**Uso:**
```yaml
Automação: Automatizado
```

---

## 🔄 Ciclo de Teste — Campos Customizados

### 1️⃣ Status

**Valores Permitidos:**
- `Não Executado`
- `Em Progresso`
- `Concluído`

---

### 2️⃣ Bandeira, Canal

**Mesmos valores de Caso de Teste** (ver seção anterior)

---

### 3️⃣ Ambiente

**Valores Permitidos:**
- `Prd` (Produção)
- `Sit` (Homologação)
- `Dev` (Desenvolvimento)

**Criação:**
1. **Configuration** → **Custom Fields** → **Test Cycles**
2. Nome: `Ambiente`
3. Tipo: `Select List (Single Choice)`

---

### 4️⃣ Framework

**Valores Permitidos:**
- `Cypress`
- `WebdriverIO`
- `Ruby`
- `Robot Framework`
- `K6-Browser`

**Criação:**
1. **Configuration** → **Custom Fields** → **Test Cycles**
2. Nome: `Framework`
3. Tipo: `Select List (Single Choice)`

**Uso:**
```yaml
Framework: Cypress
```

---

### 5️⃣ Execução Assistida

**Valores Permitidos:**
- `Automação em manutenção`
- `Execução assistida`
- `Execução manual`
- `Execução automática`

**Criação:**
1. **Configuration** → **Custom Fields** → **Test Cycles**
2. Nome: `Execução Assistida`
3. Tipo: `Select List (Single Choice)`

---

### 6️⃣ URL

**Tipo:** Texto (Linha Simples)

**Uso:** URL de uma execução (run) do GitHub Actions

**Criação:**
1. **Configuration** → **Custom Fields** → **Test Cycles**
2. Nome: `Url`
3. Tipo: `Text Field (Single Line)`

---

## 📊 Plano de Teste — Campos Customizados

### 1️⃣ Status

**Valores Permitidos:**
- `Approved` (Aprovado pelo time)
- `Deprecated` (Obsoleto, não mais utilizado)
- `Draft` (Rascunho, não aprovado)

---

### 2️⃣ Rótulos

**Mesmos padrões de Caso de Teste** (funcionalidade, tipo de teste)

---

## 📥 Formato CSV para Importação

### Regras Críticas

**✅ SEMPRE:**
- **Sem aspas duplas** em nenhum campo
- **Separação por vírgula** (`,`) apenas
- **Sanitizar texto** (remover vírgulas, quebras de linha, caracteres especiais do conteúdo)
- **Codificação UTF-8**

**❌ NUNCA:**
- Usar aspas duplas (`"`) para delimitar campos
- Incluir vírgulas no conteúdo dos campos
- Quebras de linha dentro de campos

---

### Template CSV para Caso de Teste

```csv
Nome,Objetivo,Precondição,Status,Prioridade,Rótulos,Bandeira,Canal,Script de Teste (BDD)
Validar login com usuário válido,Verificar que usuário consegue fazer login,Usuário cadastrado,Manual,Normal,@login @smoke,Example Organization,Web,Given que o usuário está na página de login When preenche email e senha válidos And clica em Entrar Then deve ser redirecionado para o dashboard
Validar login com senha inválida,Verificar mensagem de erro com credenciais inválidas,Usuário cadastrado,Manual,Normal,@login @negative,Example Organization,Web,Given que o usuário está na página de login When preenche email válido e senha inválida And clica em Entrar Then deve exibir mensagem Senha inválida
```

---

### Campos do CSV

| Campo | Tipo | Obrigatório | Exemplo |
|-------|------|-------------|---------|
| **Nome** | Texto | ✅ | `Validar login com usuário válido` |
| **Objetivo** | Texto | ✅ | `Verificar que usuário consegue fazer login` |
| **Precondição** | Texto | ❌ | `Usuário cadastrado` |
| **Status** | Lista | ✅ | `Manual` ou `Automatizado` |
| **Prioridade** | Lista | ✅ | `High`, `Normal`, `Low` |
| **Rótulos** | Texto | ✅ | `@login @smoke` (separado por espaço) |
| **Bandeira** | Lista | ✅ | `Example Organization` |
| **Canal** | Lista | ✅ | `Web` |
| **Script de Teste (BDD)** | Texto | ✅ | BDD com `Given/When/Then` |

---

## 🤖 Geração de Cenários com IA (Rovo)

### Prompt Padrão para Rovo

**Contexto:** Gerar cenários de teste a partir de histórias do Jira seguindo padrões QAOps.

```
Você é um especialista sênior em Qualidade de Software com foco em validação ponta a ponta.

A criação desses cenários da história [INSERIR ID DA HISTÓRIA] devem conter os seguintes campos:

Nome:
Objetivo:
Precondição:
Status: Manual
Prioridade: High, Normal ou Low
Rótulos: LOG_IA
Bandeira: Example Organization, Example Brand A, Extra ou Corp
Canal: Web, MSite, App iOS, App Android, API ou Legado
Script de Teste (BDD)

Escreva o início do nome do cenário de testes no modelo de "Validar"

Escrever o BDD no campo Script de Teste (BDD), com as palavras Given/When/Then em inglês.

Gere APENAS um arquivo .csv para importação no Zephyr Scale:
- Sem aspas duplas em nenhum campo
- Campos separados apenas por vírgula
- Sem vírgulas no conteúdo dos campos
- Codificação UTF-8
- Pronto para download e importação direta
```

---

### Exemplo de Saída do Rovo

**Arquivo CSV pronto para importação no Zephyr Scale:**

```csv
Nome,Objetivo,Precondição,Status,Prioridade,Rótulos,Bandeira,Canal,Script de Teste (BDD)
Validar cadastro de endereço válido,Verificar que o sistema permite cadastro de endereço completo,Usuário logado,Manual,Normal,LOG_IA @endereco @smoke,Example Organization,Web,Given que o usuário está na página de endereços When preenche todos os campos obrigatórios And clica em Salvar Then o endereço deve ser cadastrado com sucesso
Validar cadastro com CEP inválido,Verificar mensagem de erro com CEP inexistente,Usuário logado,Manual,High,LOG_IA @endereco @negative,Example Organization,Web,Given que o usuário está na página de endereços When preenche um CEP inválido And clica em Buscar Then deve exibir mensagem CEP não encontrado
Validar edição de endereço existente,Verificar que usuário pode editar endereço salvo,Usuário com endereço cadastrado,Manual,Low,LOG_IA @endereco,Example Organization,Web,Given que o usuário está na lista de endereços When clica em Editar And altera campos And clica em Salvar Then as alterações devem ser persistidas
```

---

##  Dashboard de Governança de Testes

**Link:** Dashboard de Governança de Testes (interno)

**Indicadores Disponíveis:**

| Indicador | Fonte |
|-----------|-------|
| **Cobertura de Testes** | Casos vinculados a issues |
| **Taxa de Automação** | Campo `Automação` |
| **Distribuição por Bandeira** | Campo `Bandeira` |
| **Distribuição por Canal** | Campo `Canal` |
| **Status de Execução** | Ciclos de teste |
| **Tendência de Qualidade** | Histórico de execuções |

**Pré-requisito:** Campos customizados padronizados conforme esta skill.

---

## 🚦 Fluxo de Trabalho Sugerido

```
1. Criar/manter casos de teste na biblioteca
   ↓
2. Criar planos de teste para estratégia de teste
   ↓
3. Criar ciclos de teste para planejar execução
   ↓
4. Desenvolver requisitos/funcionalidade
   ↓
5. Executar ciclos de teste para validar
   ↓
6. Acompanhar cobertura, progresso e qualidade
```

---

## 📝 Boas Práticas Gerais

### ✅ FAZER

- **Sempre preencher campos customizados** (Bandeira, Canal, Automação)
- **Vincular casos a issues Jira** para rastreabilidade
- **Usar rótulos padronizados** (@smoke, @regression, @funcionalidade)
- **Gerar CSV sem aspas duplas** para importação
- **Criar cenários com BDD** (Given/When/Then)
- **Marcar LOG_IA** quando usar Rovo para gerar cenários
- **Atualizar campo Automação** conforme evolução (Candidato → Em desenvolvimento → Automatizado)
- **Usar Status de Plano** (Approved para oficiais, Draft para em construção)

### ❌ EVITAR

- CSV com aspas duplas ou vírgulas no conteúdo
- Casos sem vínculo com issues
- Campos customizados vazios (dificulta governança)
- Rótulos não padronizados
- BDD em português (usar inglês: Given/When/Then)
- Planos sem Status definido
- Ciclos sem Framework/Ambiente preenchidos

---

## 🧩 Exemplos Práticos

### Exemplo 1: Caso de Teste Manual

```yaml
Nome: Validar login com usuário válido
Objetivo: Verificar que o sistema permite login com credenciais corretas
Precondição: Usuário cadastrado no sistema
Status: Manual
Prioridade: High
Rótulos: @login, @smoke
Bandeira: Example Organization
Canal: Web
Automação: Candidato à automação

Script de Teste (BDD):
Given que o usuário está na página de login
When preenche email "teste@example.com" e senha válida
And clica no botão "Entrar"
Then deve ser redirecionado para a página inicial
And deve exibir mensagem "Bem-vindo(a)"
```

---

### Exemplo 2: Caso de Teste Automatizado

```yaml
Nome: Validar criação de pedido via API
Objetivo: Verificar que a API cria pedido com dados válidos
Precondição: API disponível, token de autenticação válido
Status: Automatizado
Prioridade: Normal
Rótulos: @api, @pedido, @regression
Bandeira: Example Organization, Example Brand A
Canal: API
Automação: Automatizado

Script de Teste (BDD):
Given que possuo um token de autenticação válido
When envio POST /api/pedidos com payload válido
Then o status code deve ser 201
And o response deve conter o ID do pedido
And o pedido deve ser persistido no banco de dados
```

---

### Exemplo 3: CSV Completo (3 Cenários)

```csv
Nome,Objetivo,Precondição,Status,Prioridade,Rótulos,Bandeira,Canal,Script de Teste (BDD)
Validar busca de produto por nome,Verificar que busca retorna produtos corretos,Produtos cadastrados,Manual,Normal,@busca @smoke,Example Organization,Web,Given que o usuário está na página inicial When digita Geladeira na busca And clica em Buscar Then deve exibir lista de geladeiras
Validar filtro por preço,Verificar que filtro de preço funciona corretamente,Lista de produtos exibida,Manual,Low,@busca @filtro,Example Organization,Web,Given que o usuário está na página de resultados When aplica filtro de preço entre R$1000 e R$2000 Then deve exibir apenas produtos nessa faixa
Validar ordenação por preço crescente,Verificar que ordenação funciona,Lista de produtos exibida,Manual,Low,@busca @ordenacao,Example Organization,Web,Given que o usuário está na página de resultados When seleciona ordenação Menor Preço Then produtos devem aparecer do mais barato ao mais caro
```

---

## 🎯 Quando Usar Esta Skill

### ✅ USE quando:

- Criar casos de teste no Zephyr Scale
- Gerar CSV para importação em lote
- Configurar campos customizados (Bandeira, Canal, Automação)
- Gerar cenários via Rovo (IA)
- Configurar ciclos de teste com Framework
- Criar planos de teste para releases
- Consultar padrões de governança QAOps

### ❌ NÃO USE quando:

- Criar testes automatizados (use `cypress-mocha-api-testing`, `cypress-mocha-e2e-testing`, etc.)
- Executar testes (use frameworks de automação)
- Analisar código de testes (use skills específicas de frameworks)

---

## 📚 Referências

- **Workshop Zephyr Scale**: Vídeos internos (Teams/Drive)
- **Boas Práticas QAOps**: Documentação interna Confluence
- **Critérios de Aceitação**: QA.Critérios de Aceitação - BDD - Gherkin

---

**Última Atualização:** 02/05/2026  
**Compatibilidade:** Zephyr Scale (Jira), todos os frameworks QAOps