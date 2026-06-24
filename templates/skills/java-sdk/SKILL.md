---
name: java-sdk
description: Skill para desenvolvimento de bibliotecas, SDKs e pacotes Java puros (sem framework web). Use quando a tarefa envolver criação de SDKs, clients de API, utilitários, módulos reutilizáveis ou qualquer artefato JAR distribuível. Inclui padrões de TDD com JUnit 5 e Mockito, estrutura de projeto modular, convenções de código, versionamento semântico e boas práticas de segurança.
---

# Java SDK (Biblioteca / Pacote)

## Stack tecnológica

| Componente | Tecnologia |
|---|---|
| Linguagem | Java 17+ |
| Build | Maven (preferencial) ou Gradle Kotlin DSL |
| Testes unitários | JUnit 5 + Mockito + AssertJ |
| Testes de integração | JUnit 5 + Testcontainers (quando aplicável) |
| Mocking HTTP | WireMock |
| Cobertura | JaCoCo (mínimo 80%) |
| Documentação | Javadoc |
| Linting | Checkstyle + SpotBugs + PMD |
| Versionamento | SemVer (Semantic Versioning) |
| Publicação | Maven Central / Nexus interno |
| HTTP client (se aplicável) | java.net.http.HttpClient (nativo) ou OkHttp |
| Serialização | Jackson ou Gson |
| Logging | SLF4J (API) — **sem** implementação (consumidor escolhe) |

---

## Estrutura de projeto

### Módulo único

```
<sdk-name>/
  src/
    main/java/com/<empresa>/<sdk>/
      client/                       # Ponto de entrada principal do SDK
        <Sdk>Client.java
        <Sdk>ClientBuilder.java
      config/
        <Sdk>Config.java            # Configuração imutável
      model/                        # DTOs e modelos públicos
        <Dominio>.java
        <Dominio>Request.java
        <Dominio>Response.java
      exception/                    # Exceções do SDK
        <Sdk>Exception.java
        <Sdk>AuthException.java
        <Sdk>NotFoundException.java
      internal/                     # Classes internas (não públicas)
        http/
          HttpClientAdapter.java
          RequestBuilder.java
        serialization/
          JsonMapper.java
        retry/
          RetryPolicy.java
        validation/
          Preconditions.java
      spi/                          # Service Provider Interfaces (extensibilidade)
        <Sdk>Interceptor.java
        <Sdk>Serializer.java
    main/resources/
      META-INF/
        MANIFEST.MF
    test/java/com/<empresa>/<sdk>/
      client/
        <Sdk>ClientTest.java
        <Sdk>ClientBuilderTest.java
      model/
        <Dominio>Test.java
      internal/
        http/
          HttpClientAdapterTest.java
        retry/
          RetryPolicyTest.java
      integration/
        <Sdk>ClientIT.java          # Testes com WireMock
      testutil/
        TestFixtures.java           # Builders e fixtures compartilhados
    test/resources/
      wiremock/
        __files/                    # Payloads de resposta
          users-response.json
        mappings/                   # Stubs WireMock
          get-users.json
  pom.xml (ou build.gradle.kts)
  README.md
  CHANGELOG.md
```

### Multi-módulo (SDKs maiores)

```
<sdk-name>/
  <sdk>-core/                       # Modelos, exceções, interfaces
    src/main/java/.../
    pom.xml
  <sdk>-http/                       # Client HTTP padrão
    src/main/java/.../
    pom.xml
  <sdk>-okhttp/                     # Client HTTP alternativo (OkHttp)
    src/main/java/.../
    pom.xml
  <sdk>-testing/                    # Utilitários de teste para consumidores
    src/main/java/.../
    pom.xml
  pom.xml                           # Parent POM
```

---

## Scaffolding inicial

Ao iniciar um novo projeto, crie os seguintes arquivos **antes de qualquer código de produção ou teste**:

### `.gitignore`

```gitignore
target/
build/
.gradle/
*.class
*.jar
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

- Nome e descrição do SDK
- Pré-requisitos (JDK mínimo)
- Como adicionar a dependência (Maven/Gradle)
- Exemplo de uso básico (inicialização + chamada)
- Como rodar os testes (`mvn test`)
- Como buildar e instalar localmente (`mvn install`)
- Versionamento (SemVer) e changelog

---

## TDD com JUnit 5 + Mockito

### Ciclo obrigatório

```
🔴 RED    → mvn test → deve FALHAR
🟢 GREEN  → implementar o mínimo → mvn test → deve PASSAR
🔵 REFACTOR → refatorar → mvn test → deve continuar PASSANDO
```

### Teste do Client (Arrange-Act-Assert)

```java
// src/test/java/.../client/UserClientTest.java
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class UserClientTest {

    @Mock
    private HttpClientAdapter httpClient;

    private UserClient sut;

    @BeforeEach
    void setUp() {
        sut = new UserClient(httpClient);
    }

    @Test
    @DisplayName("deve retornar usuário quando API responde 200")
    void getUser_whenApiReturns200_returnsUser() {
        // Arrange
        var json = """
            {"id": 1, "name": "Alice", "email": "alice@example.com"}
            """;
        when(httpClient.get("/users/1")).thenReturn(new HttpResponse(200, json));

        // Act
        var result = sut.getUser(1L);

        // Assert
        assertThat(result.name()).isEqualTo("Alice");
        verify(httpClient).get("/users/1");
    }

    @Test
    @DisplayName("deve lançar NotFoundException quando API responde 404")
    void getUser_whenApiReturns404_throwsNotFoundException() {
        // Arrange
        when(httpClient.get("/users/99")).thenReturn(new HttpResponse(404, ""));

        // Act / Assert
        assertThatThrownBy(() -> sut.getUser(99L))
            .isInstanceOf(SdkNotFoundException.class)
            .hasMessageContaining("99");
    }

    @Test
    @DisplayName("deve lançar SdkException quando API responde 500")
    void getUser_whenApiReturns500_throwsSdkException() {
        // Arrange
        when(httpClient.get("/users/1")).thenReturn(new HttpResponse(500, "Internal Server Error"));

        // Act / Assert
        assertThatThrownBy(() -> sut.getUser(1L))
            .isInstanceOf(SdkException.class);
    }
}
```

### Teste do Builder

```java
// src/test/java/.../client/SdkClientBuilderTest.java
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.*;

class SdkClientBuilderTest {

    @Test
    @DisplayName("deve criar client com configuração válida")
    void build_whenValidConfig_returnsClient() {
        // Act
        var client = SdkClient.builder()
            .baseUrl("https://api.example.com")
            .apiKey("test-key")
            .build();

        // Assert
        assertThat(client).isNotNull();
    }

    @Test
    @DisplayName("deve lançar exceção quando baseUrl não informada")
    void build_whenMissingBaseUrl_throwsIllegalArgumentException() {
        // Act / Assert
        assertThatThrownBy(() ->
            SdkClient.builder()
                .apiKey("test-key")
                .build()
        ).isInstanceOf(IllegalArgumentException.class)
            .hasMessageContaining("baseUrl");
    }

    @Test
    @DisplayName("deve aplicar timeout padrão quando não configurado")
    void build_whenNoTimeout_usesDefault() {
        // Act
        var client = SdkClient.builder()
            .baseUrl("https://api.example.com")
            .apiKey("test-key")
            .build();

        // Assert
        assertThat(client.getConfig().timeout()).isEqualTo(Duration.ofSeconds(30));
    }
}
```

### Teste com WireMock (integração)

```java
// src/test/java/.../integration/SdkClientIT.java
import com.github.tomakehurst.wiremock.junit5.WireMockExtension;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.RegisterExtension;

import static com.github.tomakehurst.wiremock.client.WireMock.*;
import static com.github.tomakehurst.wiremock.core.WireMockConfiguration.wireMockConfig;
import static org.assertj.core.api.Assertions.*;

class SdkClientIT {

    @RegisterExtension
    static WireMockExtension wireMock = WireMockExtension.newInstance()
        .options(wireMockConfig().dynamicPort())
        .build();

    @Test
    @DisplayName("deve buscar usuário via HTTP real com WireMock")
    void getUser_withWireMock_returnsUser() {
        // Arrange
        wireMock.stubFor(get(urlPathEqualTo("/users/1"))
            .willReturn(okJson("""
                {"id": 1, "name": "Alice", "email": "alice@example.com"}
                """)));

        var client = SdkClient.builder()
            .baseUrl(wireMock.baseUrl())
            .apiKey("test-key")
            .build();

        // Act
        var user = client.users().getUser(1L);

        // Assert
        assertThat(user.name()).isEqualTo("Alice");
        wireMock.verify(getRequestedFor(urlPathEqualTo("/users/1"))
            .withHeader("Authorization", equalTo("Bearer test-key")));
    }

    @Test
    @DisplayName("deve fazer retry em erro 503")
    void getUser_when503_retriesThenSucceeds() {
        // Arrange
        wireMock.stubFor(get(urlPathEqualTo("/users/1"))
            .inScenario("retry")
            .whenScenarioStateIs("Started")
            .willReturn(serviceUnavailable())
            .willSetStateTo("second-attempt"));

        wireMock.stubFor(get(urlPathEqualTo("/users/1"))
            .inScenario("retry")
            .whenScenarioStateIs("second-attempt")
            .willReturn(okJson("""
                {"id": 1, "name": "Alice", "email": "alice@example.com"}
                """)));

        var client = SdkClient.builder()
            .baseUrl(wireMock.baseUrl())
            .apiKey("test-key")
            .retryPolicy(RetryPolicy.withMaxRetries(2))
            .build();

        // Act
        var user = client.users().getUser(1L);

        // Assert
        assertThat(user.name()).isEqualTo("Alice");
        wireMock.verify(2, getRequestedFor(urlPathEqualTo("/users/1")));
    }
}
```

### Teste de RetryPolicy

```java
// src/test/java/.../internal/retry/RetryPolicyTest.java
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.*;

class RetryPolicyTest {

    @Test
    @DisplayName("deve permitir retry quando status é 503")
    void shouldRetry_when503_returnsTrue() {
        var sut = RetryPolicy.withMaxRetries(3);
        assertThat(sut.shouldRetry(503, 1)).isTrue();
    }

    @Test
    @DisplayName("não deve fazer retry quando tentativas esgotadas")
    void shouldRetry_whenMaxRetriesReached_returnsFalse() {
        var sut = RetryPolicy.withMaxRetries(2);
        assertThat(sut.shouldRetry(503, 3)).isFalse();
    }

    @Test
    @DisplayName("não deve fazer retry em erro 4xx")
    void shouldRetry_when4xx_returnsFalse() {
        var sut = RetryPolicy.withMaxRetries(3);
        assertThat(sut.shouldRetry(400, 1)).isFalse();
    }
}
```

### Comandos de teste

```bash
# rodar todos os testes
mvn test

# apenas testes unitários
mvn test -Dtest="**/*Test"

# apenas testes de integração
mvn test -Dtest="**/*IT"

# com relatório de cobertura JaCoCo
mvn verify

# verificar compatibilidade de API (se configurado)
mvn revapi:check

# gerar Javadoc
mvn javadoc:javadoc

# instalar localmente
mvn install

# publicar no Nexus
mvn deploy

# Gradle equivalentes
./gradlew test
./gradlew jacocoTestReport
./gradlew publishToMavenLocal
```

---

## Convenções de código

### Client principal (ponto de entrada)

```java
// src/main/java/.../client/SdkClient.java

/**
 * Ponto de entrada principal do SDK.
 * Criado via {@link SdkClientBuilder}.
 *
 * <pre>{@code
 * var client = SdkClient.builder()
 *     .baseUrl("https://api.example.com")
 *     .apiKey("sua-chave")
 *     .build();
 *
 * var user = client.users().getUser(1L);
 * }</pre>
 */
public final class SdkClient implements AutoCloseable {

    private final SdkConfig config;
    private final HttpClientAdapter httpClient;
    private final UserClient userClient;

    SdkClient(SdkConfig config, HttpClientAdapter httpClient) {
        this.config = config;
        this.httpClient = httpClient;
        this.userClient = new UserClient(httpClient);
    }

    public static SdkClientBuilder builder() {
        return new SdkClientBuilder();
    }

    public UserClient users() {
        return userClient;
    }

    public SdkConfig getConfig() {
        return config;
    }

    @Override
    public void close() {
        httpClient.close();
    }
}
```

### Builder (configuração fluente)

```java
// src/main/java/.../client/SdkClientBuilder.java
import java.time.Duration;

public final class SdkClientBuilder {

    private String baseUrl;
    private String apiKey;
    private Duration timeout = Duration.ofSeconds(30);
    private RetryPolicy retryPolicy = RetryPolicy.noRetry();

    SdkClientBuilder() {}

    public SdkClientBuilder baseUrl(String baseUrl) {
        this.baseUrl = baseUrl;
        return this;
    }

    public SdkClientBuilder apiKey(String apiKey) {
        this.apiKey = apiKey;
        return this;
    }

    public SdkClientBuilder timeout(Duration timeout) {
        this.timeout = timeout;
        return this;
    }

    public SdkClientBuilder retryPolicy(RetryPolicy retryPolicy) {
        this.retryPolicy = retryPolicy;
        return this;
    }

    public SdkClient build() {
        Preconditions.requireNonEmpty(baseUrl, "baseUrl");
        Preconditions.requireNonEmpty(apiKey, "apiKey");

        var config = new SdkConfig(baseUrl, apiKey, timeout, retryPolicy);
        var httpClient = new HttpClientAdapter(config);
        return new SdkClient(config, httpClient);
    }
}
```

### Configuração imutável

```java
// src/main/java/.../config/SdkConfig.java
import java.time.Duration;

public record SdkConfig(
    String baseUrl,
    String apiKey,
    Duration timeout,
    RetryPolicy retryPolicy
) {
    public SdkConfig {
        if (baseUrl == null || baseUrl.isBlank()) {
            throw new IllegalArgumentException("baseUrl é obrigatória");
        }
        if (apiKey == null || apiKey.isBlank()) {
            throw new IllegalArgumentException("apiKey é obrigatória");
        }
    }
}
```

### Modelos públicos (DTOs imutáveis)

```java
// src/main/java/.../model/User.java

public record User(
    long id,
    String name,
    String email
) {}

// src/main/java/.../model/UserRequest.java

public record UserRequest(
    String name,
    String email
) {
    public UserRequest {
        if (name == null || name.isBlank()) {
            throw new IllegalArgumentException("name é obrigatório");
        }
    }
}
```

### Hierarquia de exceções

```java
// src/main/java/.../exception/SdkException.java

/**
 * Exceção base do SDK. Todas as exceções específicas estendem esta.
 */
public class SdkException extends RuntimeException {

    private final int statusCode;

    public SdkException(String message, int statusCode) {
        super(message);
        this.statusCode = statusCode;
    }

    public SdkException(String message, Throwable cause) {
        super(message, cause);
        this.statusCode = 0;
    }

    public int getStatusCode() { return statusCode; }
}

// src/main/java/.../exception/SdkNotFoundException.java
public class SdkNotFoundException extends SdkException {
    public SdkNotFoundException(String resource, Object id) {
        super(resource + " não encontrado: " + id, 404);
    }
}

// src/main/java/.../exception/SdkAuthException.java
public class SdkAuthException extends SdkException {
    public SdkAuthException(String message) {
        super(message, 401);
    }
}
```

### HTTP Client Adapter (internal)

```java
// src/main/java/.../internal/http/HttpClientAdapter.java
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;

final class HttpClientAdapter implements AutoCloseable {

    private final HttpClient httpClient;
    private final SdkConfig config;
    private final JsonMapper jsonMapper;

    HttpClientAdapter(SdkConfig config) {
        this.config = config;
        this.jsonMapper = new JsonMapper();
        this.httpClient = HttpClient.newBuilder()
            .connectTimeout(config.timeout())
            .build();
    }

    HttpResponse get(String path) {
        var request = HttpRequest.newBuilder()
            .uri(URI.create(config.baseUrl() + path))
            .header("Authorization", "Bearer " + config.apiKey())
            .header("Content-Type", "application/json")
            .GET()
            .build();

        return execute(request);
    }

    HttpResponse post(String path, Object body) {
        var json = jsonMapper.toJson(body);
        var request = HttpRequest.newBuilder()
            .uri(URI.create(config.baseUrl() + path))
            .header("Authorization", "Bearer " + config.apiKey())
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(json))
            .build();

        return execute(request);
    }

    private HttpResponse execute(HttpRequest request) {
        // Implementação com retry policy
        // ...
    }

    @Override
    public void close() {
        // cleanup se necessário
    }
}
```

### Resource client por domínio

```java
// src/main/java/.../client/UserClient.java

public final class UserClient {

    private final HttpClientAdapter httpClient;
    private final JsonMapper jsonMapper = new JsonMapper();

    UserClient(HttpClientAdapter httpClient) {
        this.httpClient = httpClient;
    }

    public User getUser(long id) {
        var response = httpClient.get("/users/" + id);
        return switch (response.statusCode()) {
            case 200 -> jsonMapper.fromJson(response.body(), User.class);
            case 404 -> throw new SdkNotFoundException("User", id);
            default -> throw new SdkException("Erro ao buscar usuário", response.statusCode());
        };
    }

    public List<User> listUsers() {
        var response = httpClient.get("/users");
        return switch (response.statusCode()) {
            case 200 -> jsonMapper.fromJsonList(response.body(), User.class);
            default -> throw new SdkException("Erro ao listar usuários", response.statusCode());
        };
    }

    public User createUser(UserRequest request) {
        var response = httpClient.post("/users", request);
        return switch (response.statusCode()) {
            case 201 -> jsonMapper.fromJson(response.body(), User.class);
            default -> throw new SdkException("Erro ao criar usuário", response.statusCode());
        };
    }
}
```

### SPI (extensibilidade)

```java
// src/main/java/.../spi/SdkInterceptor.java

/**
 * Interceptador para requests e responses do SDK.
 * Consumidores podem implementar para logging, métricas, etc.
 */
public interface SdkInterceptor {
    void beforeRequest(RequestContext context);
    void afterResponse(ResponseContext context);
}
```

---

## Design de API pública do SDK

### Princípios

- **API pública mínima**: Exponha apenas o necessário. Classes em `internal/` devem ser package-private.
- **Imutabilidade**: Configurações e modelos são imutáveis (records ou classes com campos final).
- **Builder pattern**: Para objetos com múltiplos parâmetros opcionais (client, config, requests complexos).
- **Fluent API**: Métodos encadeáveis retornam `this` quando faz sentido.
- **Fail-fast**: Valide parâmetros no ponto de entrada — `Preconditions.requireNonEmpty()` no builder, não no uso posterior.
- **AutoCloseable**: Client principal implementa `AutoCloseable` para gerenciar recursos HTTP.
- **Sem dependências transitivas pesadas**: Minimize dependências. Prefira `java.net.http.HttpClient` nativo. Se usar Jackson/OkHttp, declare como `optional` no POM.

### Versionamento (SemVer)

| Mudança | Versão | Exemplo |
|---|---|---|
| Correção sem quebra de API | PATCH | 1.0.0 → 1.0.1 |
| Nova funcionalidade sem quebra | MINOR | 1.0.1 → 1.1.0 |
| Quebra de API pública | MAJOR | 1.1.0 → 2.0.0 |

### Javadoc obrigatório

Toda classe e método **público** deve ter Javadoc:

```java
/**
 * Busca um usuário pelo ID.
 *
 * @param id identificador do usuário
 * @return o usuário encontrado
 * @throws SdkNotFoundException se o usuário não existir
 * @throws SdkException em caso de erro de comunicação
 */
public User getUser(long id) { ... }
```

---

## Segurança (OWASP)

- **Nunca** logue ou exponha credenciais (API keys, tokens) em mensagens de exceção, logs ou `toString()`.
- Credenciais devem ser passadas via builder — **nunca** hardcoded ou lidas de arquivo dentro do SDK.
- Valide URLs base contra SSRF — aceite apenas HTTPS em produção. Se HTTP for necessário (dev), exija flag explícita (`allowInsecure(true)`).
- Sanitize dados do usuário antes de interpolá-los em URLs — use encoding adequado para path e query parameters.
- Timeouts obrigatórios em toda comunicação HTTP — **nunca** permita timeout infinito (padrão deve ser ≤ 30s).
- Valide respostas da API — não confie cegamente em payloads JSON. Trate campos nulos, tipos inesperados.
- Use TLS 1.2+ como mínimo — configure `HttpClient` para rejeitar protocolos inseguros.
- Evite desserialização de tipos arbitrários — use tipos explícitos em `fromJson()`.
- Não inclua dependências vulneráveis — rode `mvn dependency-check:check` (OWASP Dependency-Check) regularmente.

---

## Particularidades de SDKs Java

- **Module system (JPMS)**: Considere adicionar `module-info.java` para projetos em Java 17+. Exporte apenas pacotes públicos (`exports com.empresa.sdk.client`, `exports com.empresa.sdk.model`).
- **Backward compatibility**: Nunca remova/renomeie métodos públicos sem versão MAJOR. Use `@Deprecated(forRemoval = true)` antes de remover.
- **Thread safety**: Documente se o client é thread-safe. Prefira clientes stateless e imutáveis que são naturalmente thread-safe.
- **Logging**: Use SLF4J como facade — **nunca** inclua implementação (Logback, Log4j). Consumidor escolhe.
- **Testes para consumidores**: Considere publicar um módulo `<sdk>-testing` com mocks/stubs prontos para quem usa o SDK.
- **README.md**: Inclua exemplos de uso, requisitos mínimos (Java version, dependências), guia de contribuição e changelog.
- **POM mínimo**: Declare apenas dependências essenciais. Use `<optional>true</optional>` para dependências que o consumidor pode não precisar.

---

## Definition of Done (Java SDK)

- [ ] `.gitignore` configurado com entradas adequadas à stack
- [ ] Todos os testes passam: `mvn test`
- [ ] Testes de integração com WireMock passam: `mvn test -Dtest="**/*IT"`
- [ ] Cobertura ≥ 80%: `mvn verify` (JaCoCo)
- [ ] Sem warnings de build: `mvn compile -Werror`
- [ ] Javadoc gerado sem erros: `mvn javadoc:javadoc`
- [ ] Javadoc em toda API pública
- [ ] Sem secrets no código
- [ ] Versionamento SemVer atualizado em `pom.xml`
- [ ] README.md com exemplos de uso atualizados
- [ ] CHANGELOG.md atualizado
- [ ] Sem dependências vulneráveis: `mvn dependency-check:check`