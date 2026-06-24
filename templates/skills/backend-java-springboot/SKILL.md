---
name: backend-java-springboot
description: Skill para desenvolvimento backend com Java e Spring Boot. Use quando a tarefa envolver APIs REST, serviços, lógica de negócio, integração ou banco de dados usando Java com Spring Boot. Inclui padrões de TDD com JUnit 5 e Mockito, estrutura de projeto, convenções de código e boas práticas de segurança.
---

# Backend Java (Spring Boot)

## Stack tecnológica

| Componente | Tecnologia |
|---|---|
| Linguagem | Java 21+ |
| Framework web | Spring Boot 3.x |
| ORM | Spring Data JPA + Hibernate |
| Migrações | Flyway |
| Testes unitários | JUnit 5 + Mockito + AssertJ |
| Testes de integração | Spring Boot Test + Testcontainers |
| Cobertura | JaCoCo (mínimo 80%) |
| Build | Maven ou Gradle |
| Linting | Checkstyle + SpotBugs |

---

## Estrutura de projeto

```
src/
  main/java/com/<empresa>/<projeto>/
    api/                    # Controllers REST
      <dominio>/
        <Dominio>Controller.java
        dto/
          <Dominio>Request.java
          <Dominio>Response.java
    application/            # Casos de uso (Services)
      <dominio>/
        <Dominio>Service.java
    domain/                 # Entidades e regras puras
      <dominio>/
        <Dominio>.java
        <Dominio>Repository.java  # interface
    infrastructure/         # Implementações concretas
      persistence/
        <Dominio>JpaRepository.java
        <Dominio>RepositoryImpl.java
      config/
  resources/
    application.yml
    db/migration/           # scripts Flyway
      V1__create_<tabela>.sql
tests/
  main/java/.../
    unit/
      application/<dominio>/<Dominio>ServiceTest.java
    integration/
      api/<dominio>/<Dominio>ControllerIT.java
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
*.war
.idea/
*.iml
.settings/
.project
.classpath
application-local.yml
.env
.confluence-cache/
```

### `README.md`

Crie um `README.md` na raiz do projeto com, no mínimo:

- Nome e descrição do projeto
- Pré-requisitos (JDK, Maven/Gradle)
- Como instalar dependências (`./mvnw dependency:resolve` ou `./gradlew dependencies`)
- Como rodar o projeto localmente (`./mvnw spring-boot:run`)
- Como rodar os testes (`./mvnw test`)
- Como aplicar migrations Flyway (`./mvnw flyway:migrate`)
- Variáveis de ambiente necessárias (sem valores reais)

---

## TDD com JUnit 5 + Mockito

### Ciclo obrigatório

```
🔴 RED    → ./mvnw test → deve FALHAR
🟢 GREEN  → implementar o mínimo → ./mvnw test → deve PASSAR
🔵 REFACTOR → refatorar → ./mvnw test → deve continuar PASSANDO
```

### Teste unitário (padrão Arrange-Act-Assert)

```java
// src/test/java/.../unit/application/users/UserServiceTest.java
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class UserServiceTest {

    @Mock
    private UserRepository userRepository;

    @InjectMocks
    private UserService sut;

    @Test
    @DisplayName("deve retornar usuário quando encontrado")
    void findById_whenUserExists_returnsUser() {
        // Arrange
        var user = new User(1L, "Alice");
        when(userRepository.findById(1L)).thenReturn(Optional.of(user));

        // Act
        var result = sut.findById(1L);

        // Assert
        assertThat(result.name()).isEqualTo("Alice");
        verify(userRepository).findById(1L);
    }

    @Test
    @DisplayName("deve lançar exceção quando usuário não encontrado")
    void findById_whenUserNotFound_throwsUserNotFoundException() {
        // Arrange
        when(userRepository.findById(99L)).thenReturn(Optional.empty());

        // Act / Assert
        assertThatThrownBy(() -> sut.findById(99L))
            .isInstanceOf(UserNotFoundException.class);
    }
}
```

### Teste de integração (Spring Boot Test + Testcontainers)

```java
// src/test/java/.../integration/api/users/UserControllerIT.java
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@Testcontainers
class UserControllerIT {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16")
        .withDatabaseName("testdb");

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }

    @Autowired
    private TestRestTemplate restTemplate;

    @Test
    @DisplayName("GET /api/users/{id} retorna 200 quando usuário existe")
    void getUser_whenExists_returns200() {
        var response = restTemplate.getForEntity("/api/users/1", UserResponse.class);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(response.getBody()).isNotNull();
    }
}
```

### Comandos de teste

```bash
# rodar todos os testes
./mvnw test

# apenas testes unitários
./mvnw test -Dtest="**/*Test"

# apenas testes de integração
./mvnw test -Dtest="**/*IT"

# com relatório de cobertura JaCoCo
./mvnw verify

# Gradle equivalentes
./gradlew test
./gradlew jacocoTestReport
```

---

## Convenções de código

### Service (Application Layer)

```java
// src/main/java/.../application/users/UserService.java
@Service
@RequiredArgsConstructor
public class UserService {

    private final UserRepository userRepository;

    public UserResponse findById(Long id) {
        return userRepository.findById(id)
            .map(user -> new UserResponse(user.getId(), user.getName()))
            .orElseThrow(() -> new UserNotFoundException(id));
    }
}
```

### Controller (API Layer)

```java
// src/main/java/.../api/users/UserController.java
@RestController
@RequestMapping("/api/users")
@RequiredArgsConstructor
public class UserController {

    private final UserService userService;

    @GetMapping("/{id}")
    public ResponseEntity<UserResponse> findById(@PathVariable Long id) {
        return ResponseEntity.ok(userService.findById(id));
    }
}
```

### Exception Handler global

```java
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(UserNotFoundException.class)
    public ProblemDetail handleUserNotFound(UserNotFoundException ex) {
        var problem = ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, ex.getMessage());
        problem.setTitle("User Not Found");
        return problem;
    }
}
```

---

## Segurança (OWASP)

- Use `@RestControllerAdvice` com `ProblemDetail` — **nunca** exponha stack traces em produção.
- Valide inputs com Bean Validation (`@Valid`, `@NotBlank`, `@Size`, etc.) nos DTOs de request.
- Segredos em `application.yml` **nunca** — use variáveis de ambiente ou Spring Cloud Config / Vault.
- Queries via Spring Data JPA ou `@Query` parametrizado — **nunca** concatenação de strings.
- Autenticação via Spring Security + JWT (`spring-security-oauth2-resource-server`).
- Habilite CSRF apenas para sessão HTTP; para APIs stateless (JWT), desabilite e use CORS restritivo.

---

## Definition of Done (Java)

- [ ] `.gitignore` configurado com entradas adequadas à stack
- [ ] `README.md` com instruções de setup, execução local e testes
- [ ] Todos os testes passam: `./mvnw test`
- [ ] Cobertura ≥ 80%: `./mvnw verify` (JaCoCo)
- [ ] Sem warnings de build: `./mvnw compile -Werror`
- [ ] Migrations Flyway aplicáveis: `./mvnw flyway:migrate`
- [ ] Sem secrets no código
- [ ] Endpoints cobertos por testes de integração com Testcontainers