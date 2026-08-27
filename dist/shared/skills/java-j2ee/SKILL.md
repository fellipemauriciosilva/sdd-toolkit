---
name: java-j2ee
description: "Skill para desenvolvimento backend com Java e J2EE (Jakarta EE). Use quando a tarefa envolver Servlets, EJB, JPA, JAX-RS, CDI, JMS ou aplicações rodando em application servers como WildFly, Payara, WebSphere ou WebLogic. Inclui padrões de TDD com JUnit 5 e Mockito, estrutura de projeto, convenções de código e boas práticas de segurança."
---

# Backend Java (J2EE / Jakarta EE)

## Stack tecnológica

| Componente | Tecnologia |
|---|---|
| Linguagem | Java 17+ |
| Plataforma | Jakarta EE 10+ (ou Java EE 8 em legados) |
| API REST | JAX-RS (Jersey / RESTEasy) |
| Lógica de negócio | EJB (Stateless/Stateful) ou CDI Beans |
| Injeção de dependência | CDI (Contexts and Dependency Injection) |
| ORM | JPA (Hibernate como provider) |
| Migrações | Flyway ou Liquibase |
| Mensageria | JMS (ActiveMQ / IBM MQ) |
| Validação | Bean Validation (Hibernate Validator) |
| Testes unitários | JUnit 5 + Mockito + AssertJ |
| Testes de integração | Arquillian + ShrinkWrap / Testcontainers |
| Cobertura | JaCoCo (mínimo 80%) |
| Build | Maven (preferencial) ou Gradle |
| Application Server | WildFly / Payara / WebSphere / WebLogic |
| Linting | Checkstyle + SpotBugs + PMD |
| Servidor embarcado (dev) | Payara Micro / WildFly Bootable JAR |

---

## Estrutura de projeto

```
src/
  main/java/com/<empresa>/<projeto>/
    api/                        # Endpoints REST (JAX-RS)
      <dominio>/
        <Dominio>Resource.java
        dto/
          <Dominio>Request.java
          <Dominio>Response.java
      provider/
        CorsFilter.java
        GlobalExceptionMapper.java
      JaxRsApplication.java     # @ApplicationPath("/api")
    service/                    # Lógica de negócio (EJB / CDI)
      <dominio>/
        <Dominio>Service.java
    domain/                     # Entidades JPA e regras puras
      <dominio>/
        <Dominio>.java          # @Entity
        <Dominio>Repository.java  # interface
    infrastructure/             # Implementações concretas
      persistence/
        <Dominio>JpaRepository.java
      messaging/
        <Dominio>MessageProducer.java
        <Dominio>MessageConsumer.java  # @MessageDriven
      config/
        DataSourceProducer.java
        EntityManagerProducer.java
  main/resources/
    META-INF/
      persistence.xml
      beans.xml
    db/migration/               # scripts Flyway
      V1__create_<tabela>.sql
  main/webapp/
    WEB-INF/
      web.xml                   # (opcional em Jakarta EE 10+)
      jboss-web.xml             # (WildFly-specific, se aplicável)
tests/
  main/java/.../
    unit/
      service/<dominio>/<Dominio>ServiceTest.java
    integration/
      api/<dominio>/<Dominio>ResourceIT.java
    arquillian/
      <Dominio>ArquillianIT.java
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
*.ear
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

- Nome e descrição do projeto
- Pré-requisitos (JDK, Maven/Gradle, Application Server)
- Como instalar dependências (`mvn dependency:resolve`)
- Como buildar o WAR/EAR (`mvn package`)
- Como deployar no Application Server
- Como rodar os testes (`mvn test`)
- Como aplicar migrations Flyway (`mvn flyway:migrate`)
- Variáveis de ambiente e configurações de DataSource necessárias (sem valores reais)

---

## TDD com JUnit 5 + Mockito

### Ciclo obrigatório

```
🔴 RED    → mvn test → deve FALHAR
🟢 GREEN  → implementar o mínimo → mvn test → deve PASSAR
🔵 REFACTOR → refatorar → mvn test → deve continuar PASSANDO
```

### Teste unitário de Service (Arrange-Act-Assert)

```java
// src/test/java/.../unit/service/users/UserServiceTest.java
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
        var user = new User(1L, "Alice", "alice@example.com");
        when(userRepository.findById(1L)).thenReturn(Optional.of(user));

        // Act
        var result = sut.findById(1L);

        // Assert
        assertThat(result.getName()).isEqualTo("Alice");
        verify(userRepository).findById(1L);
    }

    @Test
    @DisplayName("deve lançar exceção quando usuário não encontrado")
    void findById_whenUserNotFound_throwsNotFoundException() {
        // Arrange
        when(userRepository.findById(99L)).thenReturn(Optional.empty());

        // Act / Assert
        assertThatThrownBy(() -> sut.findById(99L))
            .isInstanceOf(NotFoundException.class);
    }
}
```

### Teste unitário de Resource (JAX-RS endpoint)

```java
// src/test/java/.../unit/api/users/UserResourceTest.java
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import jakarta.ws.rs.core.Response;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class UserResourceTest {

    @Mock
    private UserService userService;

    @InjectMocks
    private UserResource sut;

    @Test
    @DisplayName("GET /{id} retorna 200 quando usuário existe")
    void findById_whenUserExists_returns200() {
        // Arrange
        var userResponse = new UserResponse(1L, "Alice", "alice@example.com");
        when(userService.findById(1L)).thenReturn(userResponse);

        // Act
        Response response = sut.findById(1L);

        // Assert
        assertThat(response.getStatus()).isEqualTo(200);
        assertThat(response.getEntity()).isEqualTo(userResponse);
    }

    @Test
    @DisplayName("POST / retorna 201 com Location header")
    void create_whenValid_returns201WithLocation() {
        // Arrange
        var request = new UserRequest("Alice", "alice@example.com");
        var created = new UserResponse(1L, "Alice", "alice@example.com");
        when(userService.create(request)).thenReturn(created);

        // Act
        Response response = sut.create(request);

        // Assert
        assertThat(response.getStatus()).isEqualTo(201);
        assertThat(response.getLocation().getPath()).contains("/1");
    }
}
```

### Teste de integração com Arquillian

```java
// src/test/java/.../arquillian/UserResourceArquillianIT.java
import org.jboss.arquillian.container.test.api.Deployment;
import org.jboss.arquillian.junit5.ArquillianExtension;
import org.jboss.arquillian.test.api.ArquillianResource;
import org.jboss.shrinkwrap.api.ShrinkWrap;
import org.jboss.shrinkwrap.api.spec.WebArchive;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;

import jakarta.ws.rs.client.ClientBuilder;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import java.net.URL;

import static org.assertj.core.api.Assertions.*;

@ExtendWith(ArquillianExtension.class)
class UserResourceArquillianIT {

    @ArquillianResource
    private URL baseURL;

    @Deployment
    public static WebArchive createDeployment() {
        return ShrinkWrap.create(WebArchive.class, "test.war")
            .addPackages(true, "com.empresa.projeto")
            .addAsResource("META-INF/persistence.xml")
            .addAsResource("META-INF/beans.xml");
    }

    @Test
    @DisplayName("GET /api/users/{id} retorna 200 com JSON")
    void getUser_whenExists_returns200() {
        var client = ClientBuilder.newClient();
        Response response = client.target(baseURL + "api/users/1")
            .request(MediaType.APPLICATION_JSON)
            .get();

        assertThat(response.getStatus()).isEqualTo(200);
        assertThat(response.readEntity(String.class)).contains("Alice");
    }
}
```

### Teste de integração com Testcontainers (alternativa moderna)

```java
// src/test/java/.../integration/api/users/UserResourceIT.java
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.testcontainers.containers.GenericContainer;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

import jakarta.ws.rs.client.ClientBuilder;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

import static org.assertj.core.api.Assertions.*;

@Testcontainers
class UserResourceIT {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16")
        .withDatabaseName("testdb");

    @Test
    @DisplayName("GET /api/users/{id} retorna 200 quando usuário existe")
    void getUser_whenExists_returns200() {
        var client = ClientBuilder.newClient();
        Response response = client
            .target("http://localhost:8080/api/users/1")
            .request(MediaType.APPLICATION_JSON)
            .get();

        assertThat(response.getStatus()).isEqualTo(200);
    }
}
```

### Teste de MDB (Message-Driven Bean)

```java
// src/test/java/.../unit/infrastructure/messaging/UserMessageConsumerTest.java
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import jakarta.jms.TextMessage;

import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class UserMessageConsumerTest {

    @Mock
    private UserService userService;

    @Mock
    private TextMessage textMessage;

    @InjectMocks
    private UserMessageConsumer sut;

    @Test
    @DisplayName("deve processar mensagem JMS e criar usuário")
    void onMessage_whenValidMessage_createsUser() throws Exception {
        // Arrange
        when(textMessage.getText()).thenReturn("{\"name\":\"Alice\",\"email\":\"alice@example.com\"}");

        // Act
        sut.onMessage(textMessage);

        // Assert
        verify(userService).create(any(UserRequest.class));
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

# testes Arquillian (requer container configurado)
mvn test -Parquillian-managed

# build do WAR/EAR
mvn package

# deploy no WildFly (via plugin)
mvn wildfly:deploy

# Gradle equivalentes
./gradlew test
./gradlew war
```

---

## Convenções de código

### Resource (API Layer — JAX-RS)

```java
// src/main/java/.../api/users/UserResource.java
import jakarta.inject.Inject;
import jakarta.validation.Valid;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import java.net.URI;

@Path("/users")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class UserResource {

    @Inject
    private UserService userService;

    @GET
    @Path("/{id}")
    public Response findById(@PathParam("id") Long id) {
        var user = userService.findById(id);
        return Response.ok(user).build();
    }

    @POST
    public Response create(@Valid UserRequest request) {
        var created = userService.create(request);
        return Response.created(URI.create("/users/" + created.id()))
            .entity(created)
            .build();
    }

    @PUT
    @Path("/{id}")
    public Response update(@PathParam("id") Long id, @Valid UserRequest request) {
        var updated = userService.update(id, request);
        return Response.ok(updated).build();
    }

    @DELETE
    @Path("/{id}")
    public Response delete(@PathParam("id") Long id) {
        userService.delete(id);
        return Response.noContent().build();
    }
}
```

### Service (Business Layer — CDI / EJB)

```java
// src/main/java/.../service/users/UserService.java
import jakarta.ejb.Stateless;
import jakarta.inject.Inject;
import jakarta.transaction.Transactional;

@Stateless
public class UserService {

    @Inject
    private UserRepository userRepository;

    public UserResponse findById(Long id) {
        return userRepository.findById(id)
            .map(user -> new UserResponse(user.getId(), user.getName(), user.getEmail()))
            .orElseThrow(() -> new NotFoundException("Usuário não encontrado: " + id));
    }

    @Transactional
    public UserResponse create(UserRequest request) {
        var user = new User(request.name(), request.email());
        userRepository.save(user);
        return new UserResponse(user.getId(), user.getName(), user.getEmail());
    }
}
```

### Entity (Domain Layer — JPA)

```java
// src/main/java/.../domain/users/User.java
import jakarta.persistence.*;

@Entity
@Table(name = "users")
public class User {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String name;

    @Column(nullable = false, unique = true)
    private String email;

    protected User() {} // JPA

    public User(String name, String email) {
        this.name = name;
        this.email = email;
    }

    // getters — sem setters públicos (imutabilidade quando possível)
    public Long getId() { return id; }
    public String getName() { return name; }
    public String getEmail() { return email; }
}
```

### Repository (Infrastructure Layer)

```java
// src/main/java/.../domain/users/UserRepository.java
import java.util.Optional;
import java.util.List;

public interface UserRepository {
    Optional<User> findById(Long id);
    List<User> findAll();
    void save(User user);
    void delete(Long id);
}

// src/main/java/.../infrastructure/persistence/UserJpaRepository.java
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.persistence.EntityManager;
import jakarta.persistence.PersistenceContext;

@ApplicationScoped
public class UserJpaRepository implements UserRepository {

    @PersistenceContext
    private EntityManager em;

    @Override
    public Optional<User> findById(Long id) {
        return Optional.ofNullable(em.find(User.class, id));
    }

    @Override
    public List<User> findAll() {
        return em.createQuery("SELECT u FROM User u", User.class)
            .getResultList();
    }

    @Override
    public void save(User user) {
        if (user.getId() == null) {
            em.persist(user);
        } else {
            em.merge(user);
        }
    }

    @Override
    public void delete(Long id) {
        findById(id).ifPresent(em::remove);
    }
}
```

### Global Exception Mapper

```java
// src/main/java/.../api/provider/GlobalExceptionMapper.java
import jakarta.ws.rs.NotFoundException;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import jakarta.ws.rs.ext.ExceptionMapper;
import jakarta.ws.rs.ext.Provider;
import java.util.Map;
import java.util.logging.Level;
import java.util.logging.Logger;

@Provider
public class GlobalExceptionMapper implements ExceptionMapper<Exception> {

    private static final Logger LOG = Logger.getLogger(GlobalExceptionMapper.class.getName());

    @Override
    public Response toResponse(Exception ex) {
        if (ex instanceof NotFoundException) {
            return Response.status(Response.Status.NOT_FOUND)
                .entity(Map.of("error", ex.getMessage()))
                .type(MediaType.APPLICATION_JSON)
                .build();
        }

        LOG.log(Level.SEVERE, "Erro não tratado", ex);
        return Response.status(Response.Status.INTERNAL_SERVER_ERROR)
            .entity(Map.of("error", "Erro interno do servidor"))
            .type(MediaType.APPLICATION_JSON)
            .build();
    }
}
```

### Message-Driven Bean (JMS)

```java
// src/main/java/.../infrastructure/messaging/UserMessageConsumer.java
import jakarta.ejb.ActivationConfigProperty;
import jakarta.ejb.MessageDriven;
import jakarta.inject.Inject;
import jakarta.jms.Message;
import jakarta.jms.MessageListener;
import jakarta.jms.TextMessage;
import java.util.logging.Level;
import java.util.logging.Logger;

@MessageDriven(activationConfig = {
    @ActivationConfigProperty(propertyName = "destinationType", propertyValue = "jakarta.jms.Queue"),
    @ActivationConfigProperty(propertyName = "destination", propertyValue = "java:/jms/queue/UserQueue")
})
public class UserMessageConsumer implements MessageListener {

    private static final Logger LOG = Logger.getLogger(UserMessageConsumer.class.getName());

    @Inject
    private UserService userService;

    @Override
    public void onMessage(Message message) {
        try {
            var text = ((TextMessage) message).getText();
            var request = JsonParser.parse(text, UserRequest.class);
            userService.create(request);
        } catch (Exception e) {
            LOG.log(Level.SEVERE, "Erro ao processar mensagem JMS", e);
        }
    }
}
```

### JAX-RS Application

```java
// src/main/java/.../api/JaxRsApplication.java
import jakarta.ws.rs.ApplicationPath;
import jakarta.ws.rs.core.Application;

@ApplicationPath("/api")
public class JaxRsApplication extends Application {
    // Descoberta automática de resources via CDI
}
```

### persistence.xml

```xml
<!-- src/main/resources/META-INF/persistence.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<persistence xmlns="https://jakarta.ee/xml/ns/persistence"
             xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
             xsi:schemaLocation="https://jakarta.ee/xml/ns/persistence
             https://jakarta.ee/xml/ns/persistence/persistence_3_1.xsd"
             version="3.1">

    <persistence-unit name="primary" transaction-type="JTA">
        <jta-data-source>java:jboss/datasources/AppDS</jta-data-source>
        <properties>
            <property name="hibernate.dialect" value="org.hibernate.dialect.PostgreSQLDialect"/>
            <property name="hibernate.hbm2ddl.auto" value="validate"/>
            <property name="hibernate.show_sql" value="false"/>
        </properties>
    </persistence-unit>
</persistence>
```

---

## Segurança (OWASP)

- Use `ExceptionMapper` global — **nunca** exponha stack traces em respostas HTTP.
- Valide inputs com Bean Validation (`@Valid`, `@NotBlank`, `@Size`, `@Email`, etc.) nos DTOs de request.
- Segredos em `persistence.xml` ou código-fonte **nunca** — use JNDI DataSources configurados no application server ou variáveis de ambiente.
- Queries via JPA (`@NamedQuery`, `TypedQuery` com parâmetros) — **nunca** concatenação de strings em JPQL ou SQL nativo.
- Para SQL nativo, use `em.createNativeQuery` com parâmetros posicionais ou nomeados — **nunca** `String.format` ou concatenação.
- Configure autenticação via JAAS / Security Realms do application server, ou integre com OAuth2/JWT via `MicroProfile JWT`.
- Habilite CORS apenas para origens autorizadas via `ContainerResponseFilter` — **nunca** use `Access-Control-Allow-Origin: *` em produção.
- Proteja endpoints sensíveis com `@RolesAllowed`, `@DenyAll` ou `@PermitAll` do Jakarta Security.
- Desabilite listagem de diretórios e páginas de erro padrão do application server em produção.
- Use HTTPS obrigatório — configure `transport-guarantee` como `CONFIDENTIAL` no `web.xml` ou via application server.

---

## Particularidades J2EE / Jakarta EE

- **EJB vs CDI**: Prefira CDI (`@ApplicationScoped`, `@RequestScoped`) para beans simples. Use EJB (`@Stateless`) quando precisar de gerenciamento de transações automático (`@TransactionAttribute`) ou features como timer service (`@Schedule`).
- **Container-managed transactions**: EJBs usam CMT por padrão — cada método público é uma transação. Para CDI beans, use `@Transactional` explicitamente.
- **JNDI lookups**: Evite lookups manuais (`InitialContext.lookup`) — prefira `@Inject` e `@Resource`.
- **WAR vs EAR**: Para aplicações simples, use WAR. Use EAR apenas se houver múltiplos módulos EJB/WAR que precisam compartilhar bibliotecas.
- **MicroProfile**: Se disponível no application server (WildFly, Payara, Open Liberty), use MicroProfile Config para externalização de configuração, MicroProfile Health para health checks e MicroProfile Metrics para métricas.
- **Classloading**: Cuidado com conflitos de classpath entre bibliotecas da aplicação e do application server. Use `jboss-deployment-structure.xml` (WildFly) para isolar dependências quando necessário.

---

## Definition of Done (Java J2EE)

- [ ] `.gitignore` configurado com entradas adequadas à stack
- [ ] `README.md` com instruções de setup, build, deploy e testes
- [ ] Todos os testes passam: `mvn test`
- [ ] Cobertura ≥ 80%: `mvn verify` (JaCoCo)
- [ ] Sem warnings de build: `mvn compile`
- [ ] Migrations Flyway aplicáveis: `mvn flyway:migrate`
- [ ] Deploy no application server sem erros: `mvn package` + deploy
- [ ] Sem secrets no código ou em `persistence.xml`
- [ ] Endpoints cobertos por testes de integração
- [ ] `ExceptionMapper` trata todas as exceções sem expor stack traces
- [ ] Bean Validation nos DTOs de request
- [ ] `@RolesAllowed` configurado em endpoints que exigem autenticação

---

## Padrão Legado — IBM WebSphere + JSF/PrimeFaces (Java EE 6)

> Use esta seção ao trabalhar com projetos rodando em **IBM WebSphere Application Server 8.5.5** com **JSF 2.0 + PrimeFaces**, como o `v2-gestaometa`.

### Stack típica

| Componente | Tecnologia |
|---|---|
| Java | 1.6 / 1.7 |
| Plataforma | Java EE 6 (`com.ibm.websphere.jee:jee6`) |
| UI | JSF 2.0 (Apache MyFaces) + PrimeFaces 5.x |
| CDI | Apache MyFaces CODI (`myfaces-extcdi-bundle-jsf20`) |
| EJB | EJB 3.1 (`@Stateless`, `@Singleton`) |
| JPA | JPA 2.0 (provider IBM WebSphere) |
| JMS | IBM MQ via WebSphere |
| Testes | JUnit 4 + PowerMock + Mockito |
| Monitoramento | JavaMelody |
| Log | Log4j 1.x |

### Estrutura de módulos EAR

```
Projeto-ear/        (packaging = ear)
Projeto-ejb/        (packaging = ejb)
  src/main/java/
    dao/            ← DAOBaseCrud + DAOs específicos
    dto/            ← DTOs por módulo de negócio
    ejb/            ← Interfaces @Local dos services
      impl/         ← @Stateless ServiceImpl
      timer/        ← @Singleton + @Schedule
    entity/         ← @Entity JPA
    enumerator/     ← Enums de domínio
    jms/            ← MDB (@MessageDriven)
    report/         ← Geração JasperReports
    util/           ← Utilitários
  src/main/resources/META-INF/
    persistence.xml
    beans.xml
    ejb-jar.xml             ← interceptors (ex.: JavaMelody)
    ibm-ejb-jar-bnd.xml     ← bindings WebSphere (JNDI, security role)
    ibm-ejb-jar-ext.xml     ← extensions WebSphere

Projeto-web/        (packaging = war)
  src/main/java/
    bean/           ← @ManagedBean JSF
    componente/     ← Componentes JSF customizados
    converter/      ← @FacesConverter
    filter/         ← Servlet Filters
    listener/       ← Application/Session Listeners
    security/       ← Autenticação e autorização (perfil, permissão)
    servlet/        ← Servlets customizados
    report/         ← Relatórios web (JasperReports, CSV)
    ws/             ← Web Services (JAX-WS endpoint)
    vo/             ← Value Objects camada web
  src/main/webapp/
    faces/<modulo>/ ← Facelets .xhtml por módulo de negócio
    WEB-INF/
      web.xml
      faces-config.xml
      ibm-web-bnd.xml       ← bindings WebSphere (virtual host, datasource)
      ibm-web-ext.xml
      ibm-managed-bean-bnd.xml
```

### Padrão de EJB Service

```java
// Interface local
@Local
public interface MetaService {
    void distribuir(Long competenciaId);
    List<MetaDTO> listarPorFilial(Long filialId);
}

// Implementação
@Stateless
public class MetaServiceImpl extends AbstractService implements MetaService {

    @EJB
    private CompetenciaService competenciaService;

    @PersistenceContext(unitName = "GestaoMeta")
    private EntityManager em;

    private MetaDAO metaDAO;

    @PostConstruct
    public void init() {
        this.metaDAO = new MetaDAO(em);
    }

    @Override
    public void distribuir(Long competenciaId) {
        // lógica de negócio
    }
}
```

### Padrão de Managed Bean JSF

```java
@ManagedBean
@ViewScoped
public class MetaBean implements Serializable {

    private static final long serialVersionUID = 1L;

    @EJB
    private MetaService metaService;

    private List<MetaDTO> metas;
    private MetaDTO metaSelecionada;

    @PostConstruct
    public void init() {
        this.metas = metaService.listarPorFilial(getFilialLogada());
    }

    public void salvar() {
        metaService.distribuir(metaSelecionada.getCompetenciaId());
        FacesContext.getCurrentInstance()
            .addMessage(null, new FacesMessage("Meta salva com sucesso"));
    }

    // getters/setters
}
```

### Padrão de DAO

```java
public class MetaDAO extends DAOBaseCrud<Meta, MetaPK> {

    public MetaDAO(EntityManager em) {
        super(em, Meta.class);
    }

    public List<Meta> findByCompetencia(Long competenciaId) {
        return em.createQuery(
            "SELECT m FROM Meta m WHERE m.competencia.id = :competenciaId", Meta.class)
            .setParameter("competenciaId", competenciaId)
            .getResultList();
    }
}
```

### EJB Timer (@Schedule)

```java
@Singleton
public class SincronizacaoVendedoresSchedule {

    @EJB
    private SincronizacaoVendedoresService sincronizacaoService;

    @Schedule(hour = "2", minute = "0", second = "0", persistent = false)
    public void executar() {
        sincronizacaoService.sincronizar();
    }
}
```

### Configurações IBM WebSphere — atenção

- **DataSource via JNDI**: não declarar URL/usuário/senha no código — usar `@PersistenceContext` e configurar DataSource no console WebSphere.
- **ibm-ejb-jar-bnd.xml**: mapeia security roles para grupos LDAP corporativos.
- **ibm-web-bnd.xml**: declara virtual host e mapeamento de DataSource.
- **Classloading**: WebSphere usa "parent last" para evitar conflito de libs — verificar se necessário em `ibm-web-ext.xml`.
- **`beans.xml` obrigatório**: mesmo vazio, é necessário para ativar CDI nos módulos EJB e WAR.

### Testes com JUnit 4 + PowerMock (padrão legado)

```java
@RunWith(PowerMockRunner.class)
@PrepareForTest({ UtilitarioEstatico.class })
public class MetaServiceImplTest {

    @InjectMocks
    private MetaServiceImpl sut;

    @Mock
    private MetaDAO metaDAO;

    @Mock
    private CompetenciaService competenciaService;

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        PowerMockito.mockStatic(UtilitarioEstatico.class);
    }

    @Test
    public void deveDistribuirMetaQuandoCompetenciaAtiva() {
        // Arrange
        when(competenciaService.buscarAtiva()).thenReturn(new Competencia(1L));
        when(metaDAO.findByCompetencia(1L)).thenReturn(Arrays.asList(new Meta()));

        // Act
        sut.distribuir(1L);

        // Assert
        verify(metaDAO).findByCompetencia(1L);
    }
}
```

### Riscos comuns neste padrão

- **Acoplamento estático**: uso frequente de `FacesContext.getCurrentInstance()` e statics — dificulta testes.
- **Transações implícitas**: EJBs têm CMT — cuidado com `REQUIRED` (padrão) vs `REQUIRES_NEW` em serviços de log/auditoria.
- **Session state em `@ViewScoped`**: beans JSF serializam estado no servidor — monitorar memória em produção.
- **Classloader WebSphere**: libs declaradas como `provided` no pom devem ser compatíveis com a versão do servidor.
- **Encoding**: projetos legados frequentemente usam `cp1252` como `sourceEncoding` — garantir consistência em ambientes Linux.
- **JavaMelody**: interceptor global em todos EJBs pode impactar performance em ambientes de baixo overhead.
