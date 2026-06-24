---
name: "sdd-test-integration-generator"
description: "Gera projeto standalone de testes de integração em test-integration/ na raiz do projeto. Detecta automaticamente se é Java (Cucumber + Testcontainers + WireMock) ou Node (Cypress). Analisa controllers, entidades, clients externos e bancos de dados para gerar cenários BDD completos."
version: "2.3.0"
---

<!-- @all -->

# Agent — Test Integration Generator

Você é um especialista em qualidade de software. Seu objetivo é analisar o projeto atual e gerar um projeto **standalone** de testes de integração em `test-integration/` na raiz do projeto.

O projeto `test-integration/` é **independente do build principal** — nunca adicione como `<module>` no `pom.xml` pai nem como workspace npm.

---

## Fluxo de Execução

### Etapa 1 — Detectar a stack do projeto

Inspecione a raiz do projeto:

1. **Se existir `pom.xml`** → stack Java → siga o **Caminho Java**
2. **Se existir `package.json` (sem `pom.xml`)** → stack Node → siga o **Caminho Node (Cypress)**
3. **Se ambos ou nenhum existirem** → pergunte ao usuário qual caminho seguir

### Etapa 2 — Analisar o projeto (ambas as stacks)

#### Para Java — coletar:

1. **`pom.xml` (raiz)**
   - `groupId`, `artifactId`, `version`
   - Versão do Java (`<java.version>`)
   - Versão do Spring Boot (`<parent><version>`)
   - Dependências de banco de dados detectadas:
     - `postgresql` ou `postgres` → Testcontainer: `org.testcontainers:postgresql`
     - `sqlserver` ou `mssql-jdbc` → Testcontainer: `org.testcontainers:mssql`
     - `mysql-connector` ou `mysql` → Testcontainer: `org.testcontainers:mysql`
     - `mongodb` → Testcontainer: `org.testcontainers:mongodb`
     - Kafka → Testcontainer: `org.testcontainers:kafka` (**obrigatório quando detectado** — não usar dummy; Kafka container é necessário para testar o listener end-to-end)
   - Clients HTTP externos (FeignClient, RestTemplate, WebClient, `@FeignClient`) → se detectado, **incluir WireMock**

2. **Controllers REST** — todos os arquivos em `**/controller/**/*.java`
   - Para cada controller: método HTTP + rota, DTOs de request/response, validações (`@NotNull`, `@NotBlank`, `@Pattern`, `@Size`, etc.), códigos de retorno

3. **Entidades/tabelas** — todos os `@Entity` em `**/model/**`, `**/domain/**`, `**/entity/**`
   - Para cada entidade: nome da tabela (`@Table(name=...)`), schema (`schema=...`), campos-chave

4. **Application.yml/properties** — perfis, porta do servidor, nomes de schemas, propriedades customizadas obrigatórias

5. **Clients externos** — todos os `@FeignClient`, `*Client.java`, `*Adapter.java` que fazem chamadas HTTP
   - Para cada client: URL configurável, endpoints chamados

6. **Kustomize / manifests de deploy** — se existir pasta `kustomize/` ou `k8s/`, inspecione todos os overlays (ex: `kustomize/overlays/hlg/cluster-*/`):

   a. **`deployment.yaml`** — seção `env[].valueFrom.secretKeyRef`: liste cada `key` para gerar override dummy no `@DynamicPropertySource` e no `application-test.yml`. Exemplos comuns:
      - `db-url`, `db-username`, `db-password` → datasource
      - `MONGO_URI` → MongoDB URI
      - `kafka-bootstrap-server`, `kafka-username`, `kafka-password`, `kafka-truststore-password` → Kafka SASL/SSL

   b. **`configmap.yaml`** — por instância de deployment: colete
      - `kafka_consumer_topics` — tópico(s) consumidos nesta instância
      - `kafka_consumer_groupid` — consumer group desta instância
      - `QUEUE_IMPLEMENTATION` / `LOG_DISPATCHER_QUEUE_IMPLEMENTATION` — nomes completos de classes de estratégia configuráveis
      - Tópicos de saída Kafka: `kafka-topic-*` (eventos publicados após processamento)
      - `truststore-location` e demais propriedades de SSL

   c. **Padrão multi-instância** — se existirem múltiplos clusters com `kafka_consumer_topics` diferentes, o app processa domínios distintos em instâncias separadas (ex: `cluster-c` → `FIL`/filial, `cluster-e` → `FUN`/funcionário, `cluster-x` → `CTT_TRB_TMP`/temporário). Nesse caso:
      - Gere **uma feature por domínio/tópico** (ex: `filial.feature`, `funcionario.feature`, `temporario.feature`)
      - No `application-test.yml`, documente cada domínio como seção de comentário
      - No README, liste os domínios cobertos

#### Para Node — coletar:

1. **`package.json`** — nome do projeto, dependências para identificar framework (NestJS, Express, Fastify, Koa)
2. **Rotas/controllers** — arquivos em `**/controllers/**`, `**/routes/**`, `**/*.controller.ts`, `**/*.controller.js`
   - Para cada rota: método HTTP + caminho, body esperado, validações, status de retorno
3. **`application.yml` / `.env.example`** — porta do servidor, variáveis de ambiente necessárias
4. **Modelos de dados** — entidades ou schemas ORM (TypeORM, Prisma, Mongoose) para assertions de banco

---

## Caminho Java — Cucumber + Testcontainers + WireMock

### Estrutura a gerar

```
test-integration/
├── pom.xml
├── README.md
└── src/
    └── test/
        ├── java/{groupId-path}/integration/
        │   ├── CucumberRunnerTest.java
        │   ├── config/
        │   │   ├── AbstractIntegrationTest.java
        │   │   └── WireMockConfig.java          ← apenas se clientes HTTP detectados
        │   └── steps/
        │       └── {Dominio}Steps.java          ← um por feature/controller
        └── resources/
            ├── features/
            │   └── {dominio}.feature            ← um por controller
            ├── application-test.yml
            ├── init.sql
            └── junit-platform.properties
```

### Regras Java

1. **`test-integration/pom.xml` não tem `<parent>` apontando para o projeto principal** — usa `spring-boot-starter-parent` diretamente.
2. **O projeto principal é importado como dependência Maven** (`<scope>test</scope>`) com exclusão do repackage do Boot.
3. **Testcontainer** é determinado pela dependência de banco detectada no passo anterior. Se nenhum banco for detectado, usar PostgreSQL como padrão e documentar como TODO.
4. **WireMock** só é gerado se existirem clients HTTP externos detectados.
5. **Scenarios em português** — use anotações `@Dado`, `@Quando`, `@Entao`, `@E`.
6. **Cada feature** cobre um controller/domínio. Tags obrigatórias: `@{dominio}` (ex: `@periodo-de-ponto`).
7. **`ddl-auto: create-drop`** no `application-test.yml` — Hibernate gerencia o schema, sem Flyway/Liquibase nos testes.
8. **`init.sql`** cria apenas os schemas necessários (ex: `CREATE SCHEMA IF NOT EXISTS hubrh;`).
9. **Cleanup por feature** via `@After` no steps — delete apenas os registros criados pelo teste.
10. **`AbstractIntegrationTest`** é `abstract` — os steps herdam dela.
11. **Kustomize obrigatório**: se a pasta `kustomize/` existir, **sempre** leia os `deployment.yaml` e `configmap.yaml` dos overlays antes de gerar o `AbstractIntegrationTest` e o `application-test.yml`. Toda variável encontrada em `secretKeyRef` precisa de um override dummy no `@DynamicPropertySource`. Toda propriedade de classe (`QUEUE_IMPLEMENTATION`, etc.) deve ser copiada do configmap — a classe estará disponível no classpath do projeto principal importado.

### Templates Java

#### `pom.xml`
```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>{SPRING_BOOT_VERSION}</version>
        <relativePath/>
    </parent>

    <groupId>{GROUP_ID}</groupId>
    <artifactId>{ARTIFACT_ID}-integration-tests</artifactId>
    <version>0.0.1-SNAPSHOT</version>
    <name>{ARTIFACT_ID} :: Integration Tests</name>

    <description>

        NÃO faz parte do build principal.

        PRÉ-REQUISITO: buildar o projeto principal com JAR thin:
          mvn clean install -DskipTests -Dspring-boot.repackage.skip=true
        Depois executar:
          cd test-integration
          mvn test
    </description>

    <properties>
        <java.version>{JAVA_VERSION}</java.version>
        <cucumber.version>7.18.0</cucumber.version>
        {WIREMOCK_PROPERTY}
    </properties>

    <dependencies>
        <!-- Projeto principal como dependência (white-box) -->
        <dependency>
            <groupId>{GROUP_ID}</groupId>
            <artifactId>{ARTIFACT_ID}</artifactId>
            <version>0.0.1-SNAPSHOT</version>
            <exclusions>
                <exclusion>
                    <groupId>org.springframework.boot</groupId>
                    <artifactId>spring-boot-starter-log4j2</artifactId>
                </exclusion>
            </exclusions>
        </dependency>

        <!-- Spring Boot Test -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>

        <!-- Testcontainers -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-testcontainers</artifactId>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.testcontainers</groupId>
            <artifactId>{TESTCONTAINER_ARTIFACT}</artifactId>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.testcontainers</groupId>
            <artifactId>junit-jupiter</artifactId>
            <scope>test</scope>
        </dependency>

        <!-- Cucumber JVM -->
        <dependency>
            <groupId>io.cucumber</groupId>
            <artifactId>cucumber-java</artifactId>
            <version>${cucumber.version}</version>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>io.cucumber</groupId>
            <artifactId>cucumber-spring</artifactId>
            <version>${cucumber.version}</version>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>io.cucumber</groupId>
            <artifactId>cucumber-junit-platform-engine</artifactId>
            <version>${cucumber.version}</version>
            <scope>test</scope>
        </dependency>

        <!-- JUnit Platform Suite -->
        <dependency>
            <groupId>org.junit.platform</groupId>
            <artifactId>junit-platform-suite</artifactId>
            <scope>test</scope>
        </dependency>

        {WIREMOCK_DEPENDENCY}
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-surefire-plugin</artifactId>
                <configuration>
                    <includes>
                        <include>**/CucumberRunnerTest.java</include>
                    </includes>
                    <systemPropertyVariables>
                        <cucumber.junit-platform.naming-strategy>long</cucumber.junit-platform.naming-strategy>
                    </systemPropertyVariables>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>
```

**Substituições obrigatórias:**
- `{SPRING_BOOT_VERSION}` — versão detectada no `pom.xml` principal
- `{GROUP_ID}` / `{ARTIFACT_ID}` / `{JAVA_VERSION}` — do `pom.xml` principal
- `{TESTCONTAINER_ARTIFACT}` — `postgresql`, `mssql`, `mysql` ou `mongodb` conforme detecção
- `{KAFKA_TESTCONTAINER_DEPENDENCY}` — se Kafka detectado no `pom.xml`, incluir:
  ```xml
  <dependency>
      <groupId>org.testcontainers</groupId>
      <artifactId>kafka</artifactId>
      <scope>test</scope>
  </dependency>
  ```
  Senão, remover o placeholder.
- `{WIREMOCK_PROPERTY}` — `<wiremock.version>3.9.1</wiremock.version>` se WireMock necessário, senão remover
- `{WIREMOCK_DEPENDENCY}` — bloco `<dependency>` do WireMock se necessário, senão remover

#### `AbstractIntegrationTest.java`
```java
package {PACKAGE}.integration.config;

{IMPORTS}

@CucumberContextConfiguration
@SpringBootTest(
        webEnvironment = RANDOM_PORT,
        properties = "spring.config.additional-location=classpath:application-test.yml"
)
@ActiveProfiles("test")
@Testcontainers
@DirtiesContext
public abstract class AbstractIntegrationTest {

    static final {CONTAINER_TYPE}Container<?> {CONTAINER_NAME};
    {KAFKA_CONTAINER_FIELD}  // presente apenas se Kafka detectado
    {WIREMOCK_FIELD}

    static {
        {CONTAINER_NAME} = new {CONTAINER_TYPE}Container<>("{CONTAINER_IMAGE}")
                .withDatabaseName("{ARTIFACT_ID_SNAKE}_test")
                .withUsername("test")
                .withPassword("test")
                .withInitScript("init.sql");
        {CONTAINER_NAME}.start();

        // Kafka container — presente apenas se Kafka detectado no pom.xml
        // {KAFKA_CONTAINER_INIT}
        // kafkaContainer = new KafkaContainer(DockerImageName.parse("confluentinc/cp-kafka:7.6.1"));
        // kafkaContainer.start();

        {WIREMOCK_INIT}
    }

    @DynamicPropertySource
    static void overrideProperties(DynamicPropertyRegistry registry) {
        // Banco relacional
        registry.add("spring.datasource.url", {CONTAINER_NAME}::getJdbcUrl);
        registry.add("spring.datasource.username", {CONTAINER_NAME}::getUsername);
        registry.add("spring.datasource.password", {CONTAINER_NAME}::getPassword);
        // MongoDB — adicionar se container MongoDB for detectado (MONGO_URI é secret)
        // registry.add("MONGO_URI", {MONGO_CONTAINER_NAME}::getConnectionString);

        // ── Kafka ────────────────────────────────────────────────────────────────
        // IMPORTANTE: Se Kafka foi detectado no pom.xml, substitua os valores dummy
        // abaixo pelos valores do KafkaContainer para testar o listener end-to-end:
        //
        //   registry.add("spring.kafka.bootstrap-servers", kafkaContainer::getBootstrapServers);
        //   registry.add("kafka-bootstrap-server", kafkaContainer::getBootstrapServers);
        //   registry.add("kafka_host", kafkaContainer::getBootstrapServers);
        //   registry.add("spring.kafka.multi-cluster.enabled", () -> "false"); // desabilita multi-cluster; listener padrão usa bootstrap-servers
        //
        // Usando KafkaContainer, o cenário end-to-end fica:
        //   1. Step envia mensagem via KafkaTemplate para o tópico configurado
        //   2. DefaultMessageListener.onMessage() é invocado pelo container
        //   3. MessageProcessor.process() persiste no banco
        //   4. Step consulta DB via JdbcTemplate e asserta o resultado
        //
        // Sem KafkaContainer (dummy), APENAS o caminho HTTP (/api/send-message) pode ser testado.
        registry.add("kafka-bootstrap-server", () -> "localhost:9092");
        registry.add("kafka_host", () -> "localhost:9092");
        registry.add("kafka_consumer_topics", () -> "test-topic");
        registry.add("kafka_consumer_groupid", () -> "test-group");
        registry.add("kafka-username", () -> "test");
        registry.add("kafka-password", () -> "test");
        registry.add("kafka-truststore-password", () -> "test");
        registry.add("spring.kafka.multi-cluster.enabled", () -> "false");
        // Tópicos de saída Kafka — adicionar um por cada kafka-topic-* encontrado no configmap
        // registry.add("kafka-topic-employee-admission-event", () -> "test-admission");
        // Implementações configuráveis — copiar valores do configmap do kustomize
        // registry.add("QUEUE_IMPLEMENTATION", () -> "{QUEUE_IMPL_CLASS}");
        // registry.add("LOG_DISPATCHER_QUEUE_IMPLEMENTATION", () -> "{LOG_DISPATCHER_CLASS}");
        {WIREMOCK_PROPERTY_OVERRIDE}
        // TODO: revisar deployment.yaml do kustomize — cada secretKeyRef não listado acima precisa de override aqui
    }

    @LocalServerPort
    protected int serverPort;

    protected String baseUrl() {
        return "http://localhost:" + serverPort;
    }
}
```

**Mapeamento de containers:**
| Banco detectado | `{CONTAINER_TYPE}` | `{CONTAINER_IMAGE}` |
|---|---|---|
| PostgreSQL | `PostgreSQL` | `postgres:15-alpine` |
| SQL Server | `MSSQLServer` | `mcr.microsoft.com/mssql/server:2022-latest` |
| MySQL | `MySQL` | `mysql:8` |
| MongoDB | `MongoDB` | `mongo:7` |

#### `CucumberRunnerTest.java`
```java
package {PACKAGE}.integration;

import org.junit.platform.suite.api.ConfigurationParameter;
import org.junit.platform.suite.api.IncludeEngines;
import org.junit.platform.suite.api.SelectClasspathResource;
import org.junit.platform.suite.api.Suite;

import static io.cucumber.junit.platform.engine.Constants.GLUE_PROPERTY_NAME;
import static io.cucumber.junit.platform.engine.Constants.PLUGIN_PROPERTY_NAME;

@Suite
@IncludeEngines("cucumber")
@SelectClasspathResource("features")
@ConfigurationParameter(
        key = GLUE_PROPERTY_NAME,
        value = "{PACKAGE}.integration"
)
@ConfigurationParameter(
        key = PLUGIN_PROPERTY_NAME,
        value = "pretty,html:target/cucumber-reports/index.html,json:target/cucumber-reports/cucumber.json"
)
public class CucumberRunnerTest {
}
```

#### `{Dominio}Steps.java`
```java
package {PACKAGE}.integration.steps;

import {PACKAGE}.integration.config.AbstractIntegrationTest;
import io.cucumber.java.After;
import io.cucumber.java.Before;
import io.cucumber.java.pt.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.*;
import org.springframework.jdbc.core.JdbcTemplate;


    @Autowired
    private JdbcTemplate jdbcTemplate;

    private ResponseEntity<String> response;

    @Before
    public void setup() {
        {WIREMOCK_RESET}
    }


    // ── Given ───────────────────────────────────────────────────────────────────
        response = restTemplate.exchange(
                baseUrl() + path, HttpMethod.valueOf(method),
                HttpEntity.EMPTY, String.class);
    }

    @Quando("faço {word} em {string} com o corpo:")
    public void fazRequestComCorpo(String method, String path, String body) {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        response = restTemplate.exchange(
                baseUrl() + path, HttpMethod.valueOf(method),
                new HttpEntity<>(body, headers), String.class);
    }

    // ── Then ────────────────────────────────────────────────────────────────────
    @Entao("a resposta deve ter status {int}")
    public void verificaStatus(int expectedStatus) {
        assertThat(response.getStatusCode().value()).isEqualTo(expectedStatus);
    }
}
```

#### `{dominio}.feature`
```gherkin
@{dominio}
Feature: {Descricao do dominio baseada no controller}

  {Uma linha descrevendo o que o serviço faz nesse domínio}

  Background:
    Given os schemas necessários existem no banco de dados

  # ─── Happy path ────────────────────────────────────────────────────────────────

  Scenario: {Operacao principal com dados válidos}
    Given {pré-condição baseada nas entidades detectadas}
    When faço {METODO} em "{ROTA}"
    Then a resposta deve ter status {CODIGO_SUCESSO}
    And {asserção de banco ou resposta}

  # ─── Negativos ─────────────────────────────────────────────────────────────────

  {Um Scenario por campo @NotNull/@NotBlank ausente → status 400}
  {Um Scenario por campo @Pattern com valor inválido → status 400}
```

#### `application-test.yml`
```yaml
spring:
  profiles:
    active: test

  jpa:
    hibernate:
      ddl-auto: create-drop
    properties:
      hibernate:
        default_schema: {SCHEMA}
        show_sql: false

  sql:
    init:
      mode: never

# Valores padrão — sobrescritos dinamicamente pelo AbstractIntegrationTest
spring.datasource.url: jdbc:{DB_TYPE}://localhost:5432/test
spring.datasource.username: test
spring.datasource.password: test

# MongoDB (secret MONGO_URI — sobrescrito pelo container em AbstractIntegrationTest)
# MONGO_URI: mongodb://test:test@localhost:27017/test

# Kafka
# IMPORTANTE: se Kafka foi detectado no pom.xml, há dois modos possíveis:
#
# MODO A — Dummy (sem KafkaContainer): testa APENAS via HTTP /api/send-message
#   multi-cluster.enabled: false → nenhum KafkaListenerContainer é registrado
#   bootstrap-servers aponta para localhost:9092 inexistente (não conecta)
#   Uso: quando o projeto tem endpoint HTTP que replica o fluxo do listener
#
# MODO B — KafkaContainer (cobertura completa):
#   Suba KafkaContainer em AbstractIntegrationTest
#   Aponte bootstrap-servers para kafkaContainer.getBootstrapServers()
#   Habilite multi-cluster.enabled: true (ou false + listener padrão)
#   Steps produzem mensagem via KafkaTemplate, aguardam processamento, assertam no DB
#   Uso: testar DefaultMessageListener.onMessage() + PreserveBlankStringDeserializer + retry
#
# O template abaixo usa MODO A por padrão. Altere para MODO B se cobertura Kafka for exigida.
kafka-bootstrap-server: localhost:9092
kafka_host: localhost:9092
kafka_consumer_topics: test-topic
kafka_consumer_groupid: test-group
kafka-username: test
kafka-password: test
kafka-truststore-password: test
truststore-location: dummy
spring:
  kafka:
    multi-cluster:
      enabled: false  # MODO A: desabilita MultiClusterKafkaConfiguration (@ConditionalOnProperty)

# Tópicos de saída Kafka — adicionar um por cada kafka-topic-* encontrado no kustomize configmap
# kafka-topic-employee-admission-event: test-admission
# kafka-topic-employee-rescision-event: test-rescision
# kafka-topic-employee-reassignment-event: test-reassignment

# Implementações configuráveis — copiar valores do kustomize configmap
# QUEUE_IMPLEMENTATION: {QUEUE_IMPL_CLASS}
# LOG_DISPATCHER_QUEUE_IMPLEMENTATION: {LOG_DISPATCHER_CLASS}

# TODO: revisar deployment.yaml do kustomize — cada secretKeyRef não listado acima precisa de um valor dummy aqui
```

#### `init.sql`
```sql
-- Cria os schemas necessários para os testes de integração
-- Adicione schemas conforme entidades detectadas no projeto
CREATE SCHEMA IF NOT EXISTS {SCHEMA};
-- CREATE SCHEMA IF NOT EXISTS history; -- descomente se o projeto usa Hibernate Envers
```

#### `junit-platform.properties`
```properties
cucumber.publish.quiet=true
```

#### `README.md` (Java)
```markdown
# Testes de Integração — {ARTIFACT_ID}

Suite de testes de integração com **Cucumber + Testcontainers{WIREMOCK_MENTION}**.

## Stack

| Componente | Versão |
|---|---|
| Java | {JAVA_VERSION} |
| Spring Boot | {SPRING_BOOT_VERSION} |
| Cucumber JVM | 7.18.0 |
| Testcontainers | Gerenciado pelo Spring Boot BOM |
{WIREMOCK_ROW}

## Pré-requisitos

- Java {JAVA_VERSION}+
- Maven 3.9+
- Docker em execução

## Como executar

### 1. Build do projeto principal (JAR thin)

```bash
# Na raiz do projeto principal
mvn clean install -DskipTests -Dspring-boot.repackage.skip=true
```

### 2. Executar os testes

```bash
cd test-integration
mvn test
```

O Testcontainers sobe e derruba o banco automaticamente.

### 3. Relatórios

```
test-integration/target/cucumber-reports/index.html
test-integration/target/cucumber-reports/cucumber.json
```

## Executar cenários específicos

Por tag:
```bash
mvn test -Dcucumber.filter.tags="@{dominio}"
```

Por feature:
```bash
mvn test -Dcucumber.features="classpath:features/{dominio}.feature"
```
```

---

## Caminho Node — Cypress

### Estrutura a gerar

```
test-integration/
├── package.json
├── cypress.config.js
├── cypress.env.json
├── README.md
└── cypress/
    ├── e2e/
    │   └── {dominio}/
    │       └── {dominio}.cy.js
    ├── fixtures/
    │   └── {dominio}/
    │       ├── payload_valido.json
    │       ├── payload_{campo}_ausente.json    ← um por campo @required detectado
    │       └── payload_{campo}_invalido.json   ← um por validação de formato
    └── support/
        ├── commands.js
        ├── e2e.js
        └── api/
            └── {Dominio}Api.js
```

### Regras Node/Cypress

1. **CommonJS apenas** — `require()` e `module.exports` em todos os `.js`. Nunca `import/export`.
2. **`failOnStatusCode: false`** em todos os `cy.request()` — a spec valida o status.
3. **URL via `Cypress.env()`** — nunca hardcoded.
4. **Um arquivo de spec por domínio/controller**.
5. **Fixtures são JSON puros** — sem lógica.
6. **Nomenclatura de fixtures:** `payload_valido.json`, `payload_{campo}_ausente.json`, `payload_{campo}_invalido.json`.
7. **`cypress.env.json`** deve ter a URL base do serviço como variável. Usar `http://localhost:{PORTA}` como valor padrão.

### Templates Node/Cypress

#### `package.json`
```json
{
  "name": "{PROJECT_NAME}-integration-tests",
  "version": "1.0.0",
  "description": "Testes de integração do {PROJECT_NAME}",
  "scripts": {
    "test": "cypress run",
    "test:open": "cypress open"
  },
  "devDependencies": {
    "cypress": "^13.0.0"
  }
}
```

#### `cypress.config.js`
```js
const { defineConfig } = require('cypress');

module.exports = defineConfig({
  e2e: {
    specPattern: 'cypress/e2e/**/*.cy.js',
    supportFile: 'cypress/support/e2e.js',
    video: false,
    screenshotOnRunFailure: false,
  },
});
```

#### `{Dominio}Api.js`
```js
const BASE_URL = Cypress.env('{PROJECT_SLUG}_URL');

const {Dominio}Api = {
  {metodo}({params}) {
    return cy.request({
      method: '{METODO_HTTP}',
      url: `${BASE_URL}/{rota}`,
      body: {params},
#### `{dominio}.cy.js`
```js
    cy.fixture('{dominio}/payload_valido').then((payload) => {
      {Dominio}Api.{metodo}(payload).then((response) => {
        expect(response.status).to.eq({STATUS_CODE});
  });
});
```

---

## Cenários a gerar por endpoint

Para **cada endpoint** identificado, derive obrigatoriamente:

| Tipo | Condição | Status esperado |
| Happy path | Payload válido completo | 2xx conforme controller |
| Campo ausente | Um cenário por `@NotNull` / `@NotBlank` / `required` | 400 |
| Formato inválido | Um cenário por `@Pattern` / `@Size` / validação de tipo | 400 |
| Recurso não encontrado | Quando o endpoint busca por ID inexistente | 404 (se aplicável) |
| Conflito | Quando o endpoint cria recurso duplicado | 409 (se aplicável) |
| Domínio Kafka via HTTP | Para cada domínio/tópico distinto detectado no kustomize, um Scenario via `POST /api/send-message` (ou endpoint equivalente) com o `OBJETO` correspondente (FIL, FUN, HIE_OGN, CTT_TRB_TMP) — cobre `MessageProcessor` mas **não** o listener Kafka | 2xx |
| Domínio Kafka end-to-end (MODO B) | Se `KafkaContainer` configurado: um Scenario por domínio que publica mensagem no tópico via `KafkaTemplate` e asserta persistência no banco via `JdbcTemplate`. Cobre `DefaultMessageListener`, `PreserveBlankStringDeserializer` e retry | DB atualizado |

> **Nota sobre cobertura Kafka**: sem `KafkaContainer`, o `@KafkaListener` / `MessageListener` nunca é invocado nos testes. O caminho HTTP (`/api/send-message`) testa `MessageProcessor` em isolamento, mas não a camada de transporte Kafka. Documente essa limitação no `README.md` gerado como TODO explícito.
---

## Etapa 3 — Gerar os arquivos

Gere **todos** os arquivos em `test-integration/` na **ordem correta**:

1. `pom.xml` (Java) ou `package.json` + `cypress.config.js` + `cypress.env.json` (Node)
2. `README.md`
3. Configuração base (`AbstractIntegrationTest.java` + `WireMockConfig.java`) ou (`support/commands.js` + `support/e2e.js`)
4. Runner (`CucumberRunnerTest.java`) — apenas Java
5. Resources (`application-test.yml`, `init.sql`, `junit-platform.properties`) — apenas Java
6. Features / Specs — um arquivo por domínio/controller
7. Steps (Java) ou API Objects (Node) — um arquivo por domínio/controller
8. Fixtures (Node) — um JSON por cenário

---

## Etapa 4 — Apresentar resultados

Ao finalizar, apresente:

1. **Stack detectada:** Java ou Node, versões principais
2. **Banco detectado:** tipo e Testcontainer ou URL (Node)
3. **WireMock:** sim/não e quais clients foram stubados (Java)
4. **Arquivos gerados:** lista completa com caminhos relativos
5. **Tabela de cobertura:**

| Endpoint | Cenários gerados | Arquivo |
|---|---|---|
| POST /exemplo | happy path, campo X ausente, formato Y inválido | `features/dominio.feature` |

6. **Próximos passos:**

```bash
# Java — build do projeto principal antes de rodar os testes
mvn clean install -DskipTests -Dspring-boot.repackage.skip=true

# Java — executar testes
cd test-integration && mvn test

# Node — instalar dependências
cd test-integration && npm install

# Node — executar testes
npm test
```

7. **TODOs pendentes** — items marcados como TODO nos arquivos gerados que precisam de atenção humana (ex: propriedades customizadas não mapeadas automaticamente, stubs WireMock a implementar)

---

## Etapa 5 — Commit e PR

Após gerar todos os arquivos, execute os seguintes passos **automaticamente** (sem pedir confirmação):

### 5.1 — Detectar contexto de branch

```bash
git branch --show-current
```

Guarde o nome do branch atual. Se o comando retornar vazio (detached HEAD), use `HEAD`.

### 5.2 — Determinar modo de operação

- **Modo PR existente**: se o branch atual for **diferente** de `main`, `master` e `develop` → commitar e fazer push no branch atual. O commit será incluído no PR já aberto.
- **Modo PR novo**: se o branch atual for `main`, `master`, `develop` ou `HEAD` → criar branch, commitar, fazer push e abrir PR.

### 5.3 — Modo PR existente (branch de feature)

```bash
# Stagia apenas os arquivos de test-integration/
git add test-integration/

# Commita com mensagem convencional
git commit -m "test(integration): add standalone integration test project"

# Push para o branch atual (que já tem PR aberto)
git push
```

Após o push, informe ao usuário:
> ✅ Commit incluído no PR do branch `<branch>` — os testes de integração serão revisados junto com as demais mudanças.

### 5.4 — Modo PR novo (branch principal)

```bash
# Criar branch dedicado
git checkout -b feat/integration-tests

# Stagia apenas os arquivos de test-integration/
git add test-integration/

# Commita
git commit -m "test(integration): add standalone integration test project"

# Push
git push -u origin feat/integration-tests
```

Em seguida, abrir o PR usando `gh` CLI (se disponível) **ou** orientar o usuário:

```bash
# Tentar criar PR automaticamente com gh CLI
gh pr create \
  --title "test(integration): add standalone integration test project" \
  --body "## O que este PR faz
Adiciona o projeto standalone de testes de integração em \`test-integration/\`.

## Stack
$(stack detectada na Etapa 4)

## Cobertura gerada
$(tabela de cobertura da Etapa 4)

## Como executar
\`\`\`bash
# Java
cd test-integration && mvn test

# Node
cd test-integration && npm install && npm test
\`\`\`" \
  --base main \
  --head feat/integration-tests
```

Se `gh` não estiver disponível, exiba a URL gerada pelo push para o usuário criar o PR manualmente:
> 📎 Push concluído. Abra o PR em: `https://github.com/<org>/<repo>/pull/new/feat/integration-tests`

### 5.5 — Verificação de gh CLI

Antes de tentar usar `gh pr create`, verifique se está disponível:

```bash
gh --version
```

Se retornar erro, pule a criação automática e exiba a instrução para o usuário criar manualmente.

---

## Regras gerais

- **Nunca** modifique o `pom.xml` raiz do projeto principal.
- **Nunca** adicione `test-integration/` como módulo Maven.
- **Nunca** modifique código de produção do projeto principal.
- **Nunca** exponha credenciais reais nos arquivos gerados — use valores dummy (`test`/`test`).
- Se uma propriedade obrigatória do `application.yml` não puder ser inferida automaticamente, marque como `TODO` com instrução clara.
- Se o projeto usa Hibernate Envers (dependência `hibernate-envers`), adicionar `CREATE SCHEMA IF NOT EXISTS history;` no `init.sql`.
- Se não for possível determinar o tipo de banco, usar PostgreSQL como padrão e documentar a suposição.
<!-- @end -->
