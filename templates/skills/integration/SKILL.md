---
name: integration
description: "Skill para desenvolvimento de fluxos de integração com IBM App Connect Enterprise (IBM ACE). Use quando a tarefa envolver message flows, ESQL, Java Compute Nodes, transformações de mensagem, roteamento, integração com MQ, HTTP, REST, SOAP, bancos de dados, filas, tópicos, políticas, BAR files ou qualquer artefato IBM ACE. Inclui padrões de TDD com JUnit e IBM Integration Test, estrutura de projeto, convenções de código e boas práticas de segurança."
---

# Integração com IBM App Connect Enterprise (ACE)

## Stack tecnológica

| Componente | Tecnologia |
|---|---|
| Plataforma | IBM App Connect Enterprise 12+ (ACE) |
| Linguagem de transformação | ESQL (preferencial) / Java Compute Node / Graphical Mapping |
| Linguagem auxiliar | Java 11+ (Java Compute Nodes, custom exits) |
| Protocolo de mensageria | IBM MQ (AMQP, MQ Protocol) |
| Protocolos de integração | HTTP/S, SOAP/WS, REST, MQ, FTP/SFTP, JDBC, File |
| Serialização | XML, JSON, DFDL (dados flat/binários), COPYBOOK |
| Testes unitários | JUnit 5 + IBM Integration Test Server |
| Testes de integração | JUnit 5 + Testcontainers (MQ) + WireMock (HTTP) |
| Cobertura | Flow Exerciser + JaCoCo (Java Compute Nodes) |
| Build | Maven (ace-maven-plugin) ou mqsicreatebar (CLI) |
| Versionamento | Git (BAR source, não BAR compilado) |
| Deploy | BAR file → Integration Server / Integration Node |
| Observabilidade | Activity Log, User Trace, IBM Instana / Prometheus |

---

## Estrutura de projeto

```
<integration-project>/
  <ApplicationName>/                    # Application (agrupa flows)
    <DominioFlow>.msgflow               # Message Flow principal
    <DominioFlow>_Error.msgflow         # Flow de tratamento de erro
    <DominioFlow>.esql                  # ESQL associado ao flow
    <DominioFlow>_Subflow.subflow       # Subflows reutilizáveis
    model/
      <Schema>.xsd                      # XML Schemas
      <Schema>.json                     # JSON Schemas
      <Copybook>.cpy                    # COBOL Copybooks (se integração mainframe)
    dfdl/
      <Format>.dfdl.xsd                 # DFDL schemas (dados flat/binários)
  <SharedLibrary>/                      # Shared Library (reuso entre apps)
    common/
      CommonError_Subflow.subflow       # Subflow de erro padrão
      CommonLogging_Subflow.subflow     # Subflow de logging padrão
      CommonRouting_Subflow.subflow     # Subflow de roteamento
    esql/
      CommonTransforms.esql             # Funções ESQL reutilizáveis
      CommonValidation.esql             # Validações comuns
    model/
      canonical/
        CanonicalOrder.xsd              # Modelo canônico de domínio
        CanonicalCustomer.xsd
      error/
        ErrorEnvelope.xsd               # Envelope padrão de erro
    java/
      src/main/java/com/<empresa>/ace/
        util/
          JsonHelper.java               # Utilitários Java
          CryptoHelper.java
  <PolicyProject>/                      # Políticas (UserDefined, MQ, HTTP)
    <policy>.policyxml
  <TestProject>/                        # Projeto de testes
    src/test/java/com/<empresa>/ace/
      flows/
        <DominioFlow>Test.java          # Testes unitários do flow
        <DominioFlow>IT.java            # Testes de integração
      fixtures/
        input/
          <caso>_request.xml
          <caso>_request.json
        expected/
          <caso>_response.xml
          <caso>_response.json
    src/test/resources/
      wiremock/
        mappings/                       # Stubs para backends HTTP
        __files/                        # Payloads de resposta
  pom.xml                              # Build Maven
  Jenkinsfile                           # (se aplicável — não criar, apenas referenciar)
  README.md
  CHANGELOG.md
```

---

## Scaffolding inicial

Ao iniciar um novo projeto, crie os seguintes arquivos **antes de qualquer código de produção ou teste**:

### `.gitignore`

```gitignore
target/
*.bar
.idea/
*.iml
.settings/
.project
.classpath
.env
.confluence-cache/
```

### `README.md`

Crie um `README.md` na raiz do projeto com, no mínimo:

- Nome e descrição do projeto de integração
- Pré-requisitos (IBM ACE Toolkit, Maven, JDK)
- Estrutura do projeto (Applications, Shared Libraries, Policies)
- Como buildar o BAR file (`mvn package` ou `mqsicreatebar`)
- Como deployar no Integration Server (`mqsideploy`)
- Como rodar os testes (`mvn test`)
- Filas MQ e tópicos utilizados
- Variáveis de ambiente e políticas necessárias (sem valores reais)

---

## TDD com JUnit 5 + IBM Integration Test

### Ciclo obrigatório

```
🔴 RED    → mvn test → deve FALHAR
🟢 GREEN  → implementar o mínimo no flow/ESQL → mvn test → deve PASSAR
🔵 REFACTOR → refatorar ESQL/flow → mvn test → deve continuar PASSANDO
```

### Teste unitário de ESQL / Compute Node

```java
// src/test/java/.../flows/OrderTransformFlowTest.java
import com.ibm.integration.test.v1.*;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.*;

class OrderTransformFlowTest {

    private static IntegrationServerHolder server;

    @BeforeAll
    static void setUp() throws Exception {
        server = IntegrationServerHolder.start("OrderApplication");
    }

    @AfterAll
    static void tearDown() throws Exception {
        server.stop();
    }

    @Test
    @DisplayName("deve transformar pedido do formato legado para canônico")
    void transform_whenValidLegacyOrder_returnsCanonicalOrder() throws Exception {
        // Arrange
        String inputMessage = TestFixtures.loadResource("fixtures/input/legacy_order_request.xml");
        String expectedOutput = TestFixtures.loadResource("fixtures/expected/canonical_order_response.xml");

        // Act
        NodeSpy spy = new NodeSpy("OrderTransformFlow", "TransformNode");
        SpyResult result = server.processMessage("OrderTransformFlow", inputMessage);

        // Assert
        assertThat(result.getOutputTerminal()).isEqualTo("Out");
        assertThat(result.getOutputMessageBody())
            .isXmlEqualTo(expectedOutput);
    }

    @Test
    @DisplayName("deve rotear para fila de erro quando pedido inválido")
    void transform_whenInvalidOrder_routesToErrorQueue() throws Exception {
        // Arrange
        String inputMessage = TestFixtures.loadResource("fixtures/input/invalid_order_request.xml");

        // Act
        SpyResult result = server.processMessage("OrderTransformFlow", inputMessage);

        // Assert
        assertThat(result.getOutputTerminal()).isEqualTo("Failure");
    }
}
```

### Teste de Java Compute Node

```java
// src/test/java/.../flows/OrderEnrichmentComputeTest.java
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import com.ibm.broker.plugin.MbElement;
import com.ibm.broker.plugin.MbMessage;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class OrderEnrichmentComputeTest {

    @Mock
    private CustomerApiClient customerApiClient;

    @Test
    @DisplayName("deve enriquecer pedido com dados do cliente")
    void evaluate_whenOrderHasCustomerId_enrichesWithCustomerData() {
        // Arrange
        var compute = new OrderEnrichmentCompute(customerApiClient);
        var customerId = "CUST-001";
        var customerData = new CustomerData("Alice", "alice@example.com", "SP");
        when(customerApiClient.getCustomer(customerId)).thenReturn(customerData);

        // Act
        var result = compute.enrich(customerId);

        // Assert
        assertThat(result.customerName()).isEqualTo("Alice");
        assertThat(result.customerState()).isEqualTo("SP");
        verify(customerApiClient).getCustomer(customerId);
    }
}
```

### Teste de integração com MQ (Testcontainers)

```java
// src/test/java/.../flows/OrderFlowMqIT.java
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.testcontainers.containers.GenericContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

import com.ibm.mq.jms.MQConnectionFactory;
import jakarta.jms.*;

import static org.assertj.core.api.Assertions.*;

@Testcontainers
class OrderFlowMqIT {

    @Container
    static GenericContainer<?> mqContainer = new GenericContainer<>("icr.io/ibm-messaging/mq:latest")
        .withEnv("LICENSE", "accept")
        .withEnv("MQ_QMGR_NAME", "QM1")
        .withEnv("MQ_APP_PASSWORD", "passw0rd")
        .withExposedPorts(1414);

    @Test
    @DisplayName("deve consumir mensagem da fila de entrada e publicar na fila de saída")
    void flow_whenMessageOnInputQueue_producesOnOutputQueue() throws Exception {
        // Arrange
        var factory = createConnectionFactory();
        String inputMessage = TestFixtures.loadResource("fixtures/input/order_request.xml");

        // Act — publica na fila de entrada
        try (var conn = factory.createConnection("app", "passw0rd");
             var session = conn.createSession(false, Session.AUTO_ACKNOWLEDGE)) {
            conn.start();
            var producer = session.createProducer(session.createQueue("ORDER.IN"));
            producer.send(session.createTextMessage(inputMessage));
        }

        // Assert — consome da fila de saída
        try (var conn = factory.createConnection("app", "passw0rd");
             var session = conn.createSession(false, Session.AUTO_ACKNOWLEDGE)) {
            conn.start();
            var consumer = session.createConsumer(session.createQueue("ORDER.OUT"));
            var response = (TextMessage) consumer.receive(10_000);

            assertThat(response).isNotNull();
            assertThat(response.getText()).contains("orderId");
        }
    }

    private MQConnectionFactory createConnectionFactory() throws Exception {
        var factory = new MQConnectionFactory();
        factory.setHostName(mqContainer.getHost());
        factory.setPort(mqContainer.getMappedPort(1414));
        factory.setQueueManager("QM1");
        factory.setChannel("DEV.APP.SVRCONN");
        factory.setTransportType(1); // TCP
        return factory;
    }
}
```

### Teste de integração com WireMock (backend HTTP)

```java
// src/test/java/.../flows/OrderApiCallFlowIT.java
import com.github.tomakehurst.wiremock.junit5.WireMockExtension;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.RegisterExtension;

import static com.github.tomakehurst.wiremock.client.WireMock.*;
import static com.github.tomakehurst.wiremock.core.WireMockConfiguration.wireMockConfig;
import static org.assertj.core.api.Assertions.*;

class OrderApiCallFlowIT {

    @RegisterExtension
    static WireMockExtension wireMock = WireMockExtension.newInstance()
        .options(wireMockConfig().dynamicPort())
        .build();

    @Test
    @DisplayName("deve chamar API de inventário e retornar estoque disponível")
    void flow_whenCallsInventoryApi_returnsStock() {
        // Arrange
        wireMock.stubFor(get(urlPathEqualTo("/api/inventory/SKU-001"))
            .willReturn(okJson("""
                {"sku": "SKU-001", "available": 42}
                """)));

        // Act
        var result = callFlowWithHttpBackend(wireMock.baseUrl(), "SKU-001");

        // Assert
        assertThat(result.available()).isEqualTo(42);
        wireMock.verify(getRequestedFor(urlPathEqualTo("/api/inventory/SKU-001")));
    }
}
```

### Comandos de teste e build

```bash
# rodar todos os testes
mvn test

# apenas testes unitários
mvn test -Dtest="**/*Test"

# apenas testes de integração
mvn test -Dtest="**/*IT"

# criar BAR file
mqsicreatebar -data <workspace> -b <barfile>.bar -a <ApplicationName> -l <SharedLibrary>

# criar BAR via Maven
mvn package

# deploy BAR no Integration Server
mqsideploy -i <integration-node> -e <integration-server> -a <barfile>.bar

# verificar flow com Flow Exerciser (Toolkit)
# → Abrir Toolkit → Drag test message → Verificar path percorrido

# rodar trace para debug
mqsichangetrace <integration-node> -e <integration-server> -u -t -b
mqsireadlog <integration-node> -e <integration-server> -u -o trace.xml
mqsiformatlog -i trace.xml -o trace_formatted.txt
```

---

## Convenções de código

### Message Flow — Estrutura padrão

Todo message flow deve seguir a estrutura:

```
MQ Input / HTTP Input
    ↓
[Validation Node]        → valida schema (XSD/JSON Schema)
    ↓
[Transform Node]         → ESQL Compute ou Mapping Node
    ↓
[Routing Node]           → Route to Operation / Filter
    ↓
[Enrich Node]            → (opcional) Java Compute para chamar API
    ↓
MQ Output / HTTP Reply
    ↓ (Failure/Catch)
[Error Handler Subflow]  → logging + publicar na DLQ
```

### ESQL — Compute Node

```sql
-- <ApplicationName>/<DominioFlow>.esql

CREATE COMPUTE MODULE OrderTransformFlow_Transform
    CREATE FUNCTION Main() RETURNS BOOLEAN
    BEGIN
        -- Declarar referências
        DECLARE inRef REFERENCE TO InputRoot.XMLNSC.Order;
        DECLARE outRef REFERENCE TO OutputRoot;

        -- Criar estrutura de saída
        CREATE LASTCHILD OF outRef DOMAIN 'XMLNSC';
        CREATE LASTCHILD OF outRef.XMLNSC NAME 'CanonicalOrder';
        SET outRef.XMLNSC.CanonicalOrder.orderId = inRef.id;
        SET outRef.XMLNSC.CanonicalOrder.customerName = inRef.customer.name;
        SET outRef.XMLNSC.CanonicalOrder.totalAmount = CAST(inRef.total AS DECIMAL);
        SET outRef.XMLNSC.CanonicalOrder.createdAt = CURRENT_TIMESTAMP;

        -- Copiar headers (MQ, HTTP, Properties)
        SET OutputRoot.Properties = InputRoot.Properties;
        SET OutputRoot.MQMD = InputRoot.MQMD;

        RETURN TRUE;
    END;
END MODULE;
```

### ESQL — Validação

```sql
CREATE COMPUTE MODULE OrderTransformFlow_Validate
    CREATE FUNCTION Main() RETURNS BOOLEAN
    BEGIN
        DECLARE inRef REFERENCE TO InputRoot.XMLNSC.Order;

        -- Validações de entrada
        IF inRef.id IS NULL OR inRef.id = '' THEN
            THROW USER EXCEPTION MESSAGE 2951
                VALUES ('Campo obrigatório ausente: Order.id');
        END IF;

        IF inRef.customer.name IS NULL THEN
            THROW USER EXCEPTION MESSAGE 2951
                VALUES ('Campo obrigatório ausente: Order.customer.name');
        END IF;

        IF CAST(inRef.total AS DECIMAL) <= 0 THEN
            THROW USER EXCEPTION MESSAGE 2951
                VALUES ('Order.total deve ser maior que zero');
        END IF;

        RETURN TRUE;
    END;
END MODULE;
```

### ESQL — Error Handler (Subflow reutilizável)

```sql
-- <SharedLibrary>/esql/CommonErrorHandler.esql

CREATE COMPUTE MODULE CommonErrorHandler_BuildErrorMessage
    CREATE FUNCTION Main() RETURNS BOOLEAN
    BEGIN
        DECLARE excRef REFERENCE TO InputExceptionList;

        -- Construir envelope de erro
        SET OutputRoot.XMLNSC.ErrorEnvelope.timestamp = CURRENT_TIMESTAMP;
        SET OutputRoot.XMLNSC.ErrorEnvelope.flowName =
            InputRoot.Properties.MessageFlowLabel;
        SET OutputRoot.XMLNSC.ErrorEnvelope.correlationId =
            CAST(InputRoot.MQMD.CorrelId AS CHARACTER);

        -- Extrair mensagem de erro da ExceptionList
        CALL navigateLastException(excRef);
        SET OutputRoot.XMLNSC.ErrorEnvelope.errorCode =
            CAST(excRef.Number AS CHARACTER);
        SET OutputRoot.XMLNSC.ErrorEnvelope.errorMessage =
            excRef.Text;

        -- Preservar mensagem original para reprocessamento
        SET OutputRoot.XMLNSC.ErrorEnvelope.originalPayload =
            CAST(InputRoot.BLOB.BLOB AS CHARACTER CCSID 1208);

        -- Copiar MQMD e setar fila de erro
        SET OutputRoot.MQMD = InputRoot.MQMD;

        RETURN TRUE;
    END;

    -- Navega até a última exceção na cadeia
    CREATE PROCEDURE navigateLastException(IN refExc REFERENCE)
    BEGIN
        WHILE refExc.Number IS NOT NULL DO
            IF LASTMOVE(refExc) THEN
                MOVE refExc LASTCHILD;
            ELSE
                RETURN;
            END IF;
        END WHILE;
    END;
END MODULE;
```

### ESQL — Logging padrão

```sql
-- <SharedLibrary>/esql/CommonLogging.esql

CREATE COMPUTE MODULE CommonLogging_Log
    CREATE FUNCTION Main() RETURNS BOOLEAN
    BEGIN
        DECLARE flowName CHARACTER InputRoot.Properties.MessageFlowLabel;
        DECLARE correlId CHARACTER COALESCE(
            InputRoot.MQMD.CorrelId,
            InputRoot.HTTPInputHeader."X-Correlation-ID",
            UUIDASCHAR
        );
        DECLARE msgTimestamp TIMESTAMP CURRENT_TIMESTAMP;

        -- Log estruturado via User Trace
        LOG EVENT SEVERITY 1 CATALOG 'BIP' MESSAGE 2951
            VALUES (
                'FLOW=' || flowName ||
                ' | CORR_ID=' || correlId ||
                ' | TIMESTAMP=' || CAST(msgTimestamp AS CHARACTER FORMAT 'yyyy-MM-dd HH:mm:ss.SSS')
            );

        -- Propagar Correlation ID no header
        SET OutputRoot.MQMD.CorrelId = CAST(correlId AS BLOB);

        RETURN TRUE;
    END;
END MODULE;
```

### Java Compute Node

```java
// <ApplicationName>/src/main/java/com/<empresa>/ace/compute/OrderEnrichmentCompute.java
import com.ibm.broker.javacompute.MbJavaComputeNode;
import com.ibm.broker.plugin.*;

public class OrderEnrichmentCompute extends MbJavaComputeNode {

    @Override
    public void evaluate(MbMessageAssembly inAssembly) throws MbException {
        MbOutputTerminal out = getOutputTerminal("out");
        MbOutputTerminal alt = getOutputTerminal("alternate");

        MbMessage inMessage = inAssembly.getMessage();
        MbMessage outMessage = new MbMessage(inMessage);
        MbMessageAssembly outAssembly = new MbMessageAssembly(inAssembly, outMessage);

        try {
            // Ler campo do input
            MbElement root = outMessage.getRootElement();
            MbElement body = root.getLastChild().getFirstChild();
            String customerId = (String) body
                .getFirstElementByPath("Order/customerId")
                .getValue();

            // Chamar API externa (via HTTPRequest node é preferível,
            // mas se lógica complexa, usar Java)
            // ...

            out.propagate(outAssembly);
        } catch (Exception e) {
            alt.propagate(outAssembly);
        } finally {
            outMessage.clearMessage();
        }
    }
}
```

### Policy (UserDefined)

```xml
<!-- <PolicyProject>/OrderServicePolicy.policyxml -->
<?xml version="1.0" encoding="UTF-8"?>
<policies>
    <policy policyType="UserDefined" policyName="OrderServicePolicy">
        <backendUrl>https://api.internal.example.com</backendUrl>
        <timeoutSeconds>30</timeoutSeconds>
        <maxRetries>3</maxRetries>
        <errorQueueName>ORDER.ERROR.DLQ</errorQueueName>
        <loggingLevel>INFO</loggingLevel>
    </policy>
</policies>
```

---

## Padrões Arquiteturais de Integração (IBM ACE)

### 1. Modelo Canônico

**Sempre usar.** Traduzir formatos de sistemas legados para um modelo canônico interno antes de rotear.

```
Sistema A (XML legado)  → [ACE: Transform A→Canônico]  → Modelo Canônico
Sistema B (JSON)        → [ACE: Transform B→Canônico]  → Modelo Canônico
Modelo Canônico         → [ACE: Transform Canônico→C]  → Sistema C (COBOL Copybook)
```

### 2. Dead Letter Queue (DLQ) / Error Queue

**Sempre configurar.** Mensagens que falharam vão para a fila de erro.

```
MQ Input → Flow → MQ Output
              ↓ (Failure / Catch)
         Error Handler Subflow
              ↓
         DLQ (ex: ORDER.ERROR.DLQ)
              ↓
         Alerta → Análise → Reprocessamento
```

| Componente | Convenção de nomenclatura |
|---|---|
| Fila de entrada | `<DOMINIO>.IN` (ex: `ORDER.IN`) |
| Fila de saída | `<DOMINIO>.OUT` (ex: `ORDER.OUT`) |
| Fila de erro / DLQ | `<DOMINIO>.ERROR.DLQ` (ex: `ORDER.ERROR.DLQ`) |
| Fila de retry | `<DOMINIO>.RETRY` (ex: `ORDER.RETRY`) |
| Tópico de evento | `<DOMINIO>/<ENTIDADE>/<EVENTO>` (ex: `ORDER/ORDER/CREATED`) |

### 3. Retry com Backoff

```
Mensagem falha:
  Tentativa 1: imediata
  Tentativa 2: requeue com delay 5s (via MQ message expiry + retry queue)
  Tentativa 3: requeue com delay 30s
  Após N tentativas: DLQ
```

Implementar via:
- **Retry counter no header MQRFH2** — incrementar a cada reprocessamento
- **Policy UserDefined** — configurar `maxRetries` e `backoffSeconds`
- **Subflow de retry** — verificar counter, aplicar delay, requeue ou DLQ

```sql
-- Verificar retry no ESQL
DECLARE retryCount INTEGER COALESCE(
    CAST(InputRoot.MQRFH2.usr.retryCount AS INTEGER), 0
);
DECLARE maxRetries INTEGER CAST(
    getUserDefinedPolicy('OrderServicePolicy', 'maxRetries') AS INTEGER
);

IF retryCount >= maxRetries THEN
    -- Enviar para DLQ
    PROPAGATE TO TERMINAL 'out1'; -- terminal ligado à DLQ
ELSE
    -- Incrementar e requeue
    SET OutputRoot.MQRFH2.usr.retryCount = retryCount + 1;
    PROPAGATE TO TERMINAL 'out'; -- terminal ligado à retry queue
END IF;
```

### 4. Idempotência

**Toda mensagem DEVE ser processada de forma idempotente.** MQ garante **at-least-once**.

| Estratégia | Implementação no ACE |
|---|---|
| **Message ID como chave** | Armazenar `MQMD.MsgId` em tabela de controle (JDBC Compute) |
| **Correlation ID de negócio** | Usar campo de negócio (orderId) como chave de idempotência |
| **Upsert no destino** | INSERT ON CONFLICT UPDATE na query JDBC |

```sql
-- Verificar duplicata via JDBC
DECLARE msgId CHARACTER CAST(InputRoot.MQMD.MsgId AS CHARACTER);
SET Environment.Variables.isDuplicate = THE(
    SELECT ITEM T.id FROM Database.PROCESSED_MESSAGES AS T
    WHERE T.message_id = msgId
);

IF Environment.Variables.isDuplicate IS NOT NULL THEN
    -- Duplicata — ACK e ignora
    RETURN FALSE;
END IF;

-- Processar + registrar
-- ... lógica de transformação ...

INSERT INTO Database.PROCESSED_MESSAGES (message_id, processed_at)
    VALUES (msgId, CURRENT_TIMESTAMP);
```

### 5. Correlation ID — Rastreabilidade

**Propagar sempre.** Todo fluxo deve manter o correlation ID do início ao fim.

```sql
-- No primeiro nó do flow
DECLARE correlId CHARACTER COALESCE(
    InputRoot.MQRFH2.usr.correlationId,
    InputRoot.HTTPInputHeader."X-Correlation-ID",
    UUIDASCHAR
);

-- Propagar no output
SET OutputRoot.MQRFH2.usr.correlationId = correlId;
SET OutputRoot.HTTPResponseHeader."X-Correlation-ID" = correlId;
```

### 6. Anti-Corruption Layer (ACL)

**Quando usar:** Integrar sistemas legados cujo formato (COBOL Copybook, flat file, SOAP antigo) não deve contaminar os serviços internos.

```
┌──────────────┐     ┌─────────────────────┐     ┌──────────────┐
│ Serviço      │ ──► │ ACE Flow (ACL)      │ ──► │ Sistema      │
│ Interno      │     │ Transform + Route   │     │ Legado       │
│ (JSON/REST)  │     │ Canônico↔Legado     │     │ (Copybook/MQ)│
└──────────────┘     └─────────────────────┘     └──────────────┘
```

---

## Topologias IBM MQ (para uso com ACE)

### Convenção de nomenclatura de filas

```
Filas de aplicação:
  <APP>.<DOMINIO>.IN            → ORDER.SVC.IN
  <APP>.<DOMINIO>.OUT           → ORDER.SVC.OUT
  <APP>.<DOMINIO>.ERROR.DLQ     → ORDER.SVC.ERROR.DLQ
  <APP>.<DOMINIO>.RETRY         → ORDER.SVC.RETRY

Tópicos:
  <DOMINIO>/<ENTIDADE>/<EVENTO> → ORDER/ORDER/CREATED

Dead Letter Queue do QM:
  SYSTEM.DEAD.LETTER.QUEUE      → DLQ global do Queue Manager

Filas de sistema ACE:
  SYSTEM.BROKER.*               → filas internas do broker (não alterar)
```

### Configuração de filas

| Parâmetro | Valor recomendado | Justificativa |
|---|---|---|
| `MAXDEPTH` | 5000–50000 | Baseado no throughput esperado |
| `MAXMSGL` | 4 MB (4194304) | Tamanho máximo da mensagem |
| `BOTHRESH` | 3–5 | Threshold de backout antes de DLQ |
| `BOQNAME` | `<FILA>.ERROR.DLQ` | Fila de backout |
| `DEFPSIST` | YES | Mensagens persistentes por padrão |
| `DEFBIND` | NOTFIXED | Para clusters MQ |

---

## Contratos de Mensagem

### Envelope padrão (XML)

```xml
<IntegrationMessage>
    <Header>
        <MessageId>550e8400-e29b-41d4-a716-446655440000</MessageId>
        <CorrelationId>corr-12345</CorrelationId>
        <Source>order-service</Source>
        <Type>com.empresa.order.created.v1</Type>
        <Timestamp>2026-03-26T10:30:00Z</Timestamp>
        <Version>1</Version>
    </Header>
    <Body>
        <Order>
            <orderId>12345</orderId>
            <customerId>678</customerId>
            <total>199.90</total>
        </Order>
    </Body>
</IntegrationMessage>
```

### Envelope padrão (JSON — para REST APIs)

```json
{
  "header": {
    "messageId": "550e8400-e29b-41d4-a716-446655440000",
    "correlationId": "corr-12345",
    "source": "order-service",
    "type": "com.empresa.order.created.v1",
    "timestamp": "2026-03-26T10:30:00Z",
    "version": 1
  },
  "body": {
    "orderId": 12345,
    "customerId": 678,
    "total": 199.90
  }
}
```

### Versionamento de contratos

| Estratégia | Quando usar |
|---|---|
| **Sufixo na versão do type** (`order.created.v1` → `order.created.v2`) | Breaking changes no payload |
| **Campos opcionais** (adicionar campos novos) | Non-breaking changes — preferir sempre |
| **XSD com versão** (`CanonicalOrder_v1.xsd`, `CanonicalOrder_v2.xsd`) | Contratos XML formais |

> **Regra:** Nunca remova campos de contratos existentes. Adicione campos novos como opcionais. Breaking changes exigem novo type versionado + período de convivência.

---

## Observabilidade

| Pilar | O que monitorar | Ferramentas |
|---|---|---|
| **Métricas** | Queue depth, mensagens processadas/s, tempo de processamento, erros/s | IBM Instana, Prometheus (via MQ Exporter), Grafana |
| **Logs** | Correlation ID, flow name, timestamps, error codes | Activity Log, User Trace, ELK Stack |
| **Traces** | Trace distribuído com propagação de Correlation ID | IBM Instana, OpenTelemetry (via ACE 12.0.7+) |
| **Alertas** | DLQ não-vazia, queue depth > threshold, flow em erro | Opsgenie, PagerDuty, Zabbix |

### Comandos de trace

```bash
# Habilitar user trace no integration server
mqsichangetrace <node> -e <server> -u -t -b

# Ler log
mqsireadlog <node> -e <server> -u -o trace.xml

# Formatar log legível
mqsiformatlog -i trace.xml -o trace.txt

# Verificar status do integration server
mqsilist <node>
mqsireportproperties <node> -e <server> -o AllMessageFlows -r
```

---

## Segurança (OWASP)

- **TLS obrigatório** em toda comunicação com MQ — configurar `SSLCIPH` nos canais SVRCONN.
- **Autenticação**: Channel Auth Records (CHLAUTH) + Connection Auth (CONNAUTH) no Queue Manager. Nunca usar canais sem autenticação.
- **Autorização**: OAM (Object Authority Manager) — princípio do menor privilégio por fila/tópico.
- **Dados sensíveis**: Nunca incluir PII, tokens ou senhas no payload. Se necessário, usar referência (ID) e o consumidor busca via API autenticada.
- **Credenciais no ACE**: Usar `mqsisetdbparms` para armazenar credenciais — **nunca** hardcoded no ESQL ou properties.
- **Validação de input**: Validar toda mensagem contra XSD/JSON Schema antes de processar — nunca confiar em dados de entrada.
- **SQL Injection no ESQL**: Usar `PASSTHRU` com parâmetros (`?`) em queries JDBC — **nunca** concatenar strings.
- **Dados em trânsito**: Criptografar mensagens sensíveis com AMS (Advanced Message Security) quando necessário.
- **Network isolation**: Queue Manager e Integration Server em rede interna — acessíveis apenas via canais autorizados.
- **Audit trail**: Habilitar event logging no Queue Manager para registrar conexões, autorizações e erros.

```sql
-- ✅ CORRETO — query parametrizada
PASSTHRU('SELECT name FROM customers WHERE id = ?', customerId);

-- ❌ ERRADO — vulnerável a SQL injection
PASSTHRU('SELECT name FROM customers WHERE id = ' || customerId);
```

---

## Boas práticas específicas IBM ACE

- **Shared Libraries**: Extrair subflows e ESQL reutilizáveis em Shared Libraries — nunca duplicar lógica entre Applications.
- **Subflows para cross-cutting**: Error handling, logging e retry devem ser subflows na Shared Library, não duplicados em cada flow.
- **Policies para configuração**: Toda configuração de ambiente (URLs, timeouts, nomes de fila) vai em UserDefined Policies — **nunca** hardcoded no ESQL.
- **XMLNSC parser**: Preferir `XMLNSC` sobre `XML` ou `MRM` — melhor performance e validação.
- **JSON parser**: Usar domínio `JSON` para parsing nativo. Evitar converter JSON→XML desnecessariamente.
- **DFDL para dados flat**: Usar DFDL schemas para parsear/serializar dados flat (posicional) ou binários — nunca parsear com substring manual no ESQL.
- **Flow Exerciser**: Usar para testes manuais rápidos durante desenvolvimento. Para testes automatizados, usar JUnit.
- **BAR versionado**: Versionar BAR source no Git. Nunca commitar BAR compilado — gerar no build (Maven/CLI).
- **Configuration-as-Code**: Em ACE 12+, usar `server.conf.yaml` para configuração do Integration Server como código.
- **Resource limits**: Configurar `maxInstances` nos flows para limitar threads concorrentes por flow — evitar starvation de recursos.

---

## Definition of Done (IBM ACE Integration)

- [ ] `.gitignore` configurado com entradas adequadas à stack
- [ ] `README.md` com instruções de setup, build, deploy e testes
- [ ] Todos os testes passam: `mvn test`
- [ ] Testes de integração com MQ (Testcontainers) passam: `mvn test -Dtest="**/*IT"`
- [ ] BAR file gerado sem erros: `mvn package` ou `mqsicreatebar`
- [ ] Flow verificado no Flow Exerciser (path principal + path de erro)
- [ ] Error Handler configurado em todo flow (Catch → DLQ)
- [ ] DLQ definida para toda fila de entrada
- [ ] Idempotência implementada em todo consumidor
- [ ] Correlation ID propagado do início ao fim
- [ ] Mensagens validadas contra XSD/JSON Schema
- [ ] Sem credenciais hardcoded — usar `mqsisetdbparms` e Policies
- [ ] Sem SQL injection — queries JDBC parametrizadas
- [ ] TLS habilitado nos canais MQ
- [ ] Contratos de mensagem versionados e documentados