---
name: backend-dotnet
description: "Skill para desenvolvimento backend com .NET (C#). Use quando a tarefa envolver APIs, serviços, lógica de negócio, integração ou banco de dados usando ASP.NET Core. Inclui padrões de TDD com xUnit, estrutura de projeto em Clean Architecture, convenções de código C# e boas práticas de segurança."
---

# Backend .NET (C#)

## Stack tecnológica

| Componente | Tecnologia |
|---|---|
| Linguagem | C# 12+ |
| Runtime | .NET 8+ |
| Framework web | ASP.NET Core Web API |
| ORM | Entity Framework Core |
| Migrações | EF Core Migrations |
| Testes | xUnit + FluentAssertions + Moq |
| Cobertura | Coverlet (mínimo 80%) |
| Linting / análise | Roslyn Analyzers + SonarAnalyzer |
| Gerenciamento de deps | NuGet |

---

## Estrutura de projeto (Clean Architecture)

```
src/
  <Projeto>.Api/            # Camada de apresentação
    Controllers/
    Program.cs
    appsettings.json
  <Projeto>.Application/    # Casos de uso e interfaces
    UseCases/
      <Dominio>/
        <Acao>UseCase.cs
        <Acao>Request.cs
        <Acao>Response.cs
    Interfaces/
      Repositories/
      Services/
    Exceptions/
  <Projeto>.Domain/         # Entidades e regras de negócio puras
    Entities/
    ValueObjects/
    Exceptions/
  <Projeto>.Infrastructure/ # Implementações concretas (DB, HTTP, etc.)
    Repositories/
    Persistence/
      AppDbContext.cs
      Migrations/
tests/
  <Projeto>.UnitTests/
    UseCases/
    Domain/
  <Projeto>.IntegrationTests/
    Controllers/
```

---

## Scaffolding inicial

Ao iniciar um novo projeto, crie os seguintes arquivos **antes de qualquer código de produção ou teste**:

### `.gitignore`

```gitignore
bin/
obj/
.vs/
*.user
*.suo
*.DotSettings.user
appsettings.*.json
!appsettings.json
*.pfx
.env
.confluence-cache/
```

### `README.md`

Crie um `README.md` na raiz do projeto com, no mínimo:

- Nome e descrição do projeto
- Pré-requisitos (SDK .NET, versão do runtime)
- Como restaurar dependências (`dotnet restore`)
- Como rodar o projeto localmente (`dotnet run`)
- Como rodar os testes (`dotnet test`)
- Como aplicar migrations (`dotnet ef database update`)
- Variáveis de ambiente necessárias (sem valores reais)

---

## TDD com xUnit

### Ciclo obrigatório

```
🔴 RED    → dotnet test → deve FALHAR
🟢 GREEN  → implementar o mínimo → dotnet test → deve PASSAR
🔵 REFACTOR → refatorar → dotnet test → deve continuar PASSANDO
```

### Estrutura de teste (padrão Arrange-Act-Assert)

```csharp
// tests/UsersService.UnitTests/GetUserUseCaseTests.cs
using FluentAssertions;
using Moq;
using Xunit;

public class GetUserUseCaseTests
{
    private readonly Mock<IUserRepository> _repoMock;
    private readonly GetUserUseCase _sut;

    public GetUserUseCaseTests()
    {
        _repoMock = new Mock<IUserRepository>();
        _sut = new GetUserUseCase(_repoMock.Object);
    }

    [Fact]
    public async Task ExecuteAsync_WhenUserExists_ReturnsUserResponse()
    {
        // Arrange
        var user = new User(id: 1, name: "Alice");
        _repoMock.Setup(r => r.FindByIdAsync(1, default))
                 .ReturnsAsync(user);

        // Act
        var result = await _sut.ExecuteAsync(new GetUserRequest(UserId: 1));

        // Assert
        result.Should().NotBeNull();
        result.Name.Should().Be("Alice");
    }

    [Fact]
    public async Task ExecuteAsync_WhenUserNotFound_ThrowsUserNotFoundException()
    {
        // Arrange
        _repoMock.Setup(r => r.FindByIdAsync(99, default))
                 .ReturnsAsync((User?)null);

        // Act
        var act = () => _sut.ExecuteAsync(new GetUserRequest(UserId: 99));

        // Assert
        await act.Should().ThrowAsync<UserNotFoundException>();
    }
}
```

### Testes de integração (WebApplicationFactory)

```csharp
// tests/IntegrationTests/UsersControllerTests.cs
using Microsoft.AspNetCore.Mvc.Testing;

public class UsersControllerTests : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly HttpClient _client;

    public UsersControllerTests(WebApplicationFactory<Program> factory)
    {
        _client = factory.CreateClient();
    }

    [Fact]
    public async Task GetUser_WhenExists_Returns200WithUser()
    {
        var response = await _client.GetAsync("/api/users/1");

        response.StatusCode.Should().Be(HttpStatusCode.OK);
        var body = await response.Content.ReadFromJsonAsync<UserResponse>();
        body!.Name.Should().NotBeEmpty();
    }
}
```

### Comandos de teste

```bash
# rodar todos os testes
dotnet test

# com cobertura
dotnet test --collect:"XPlat Code Coverage"

# apenas um projeto de testes
dotnet test tests/<Projeto>.UnitTests/

# filtrar por nome
dotnet test --filter "FullyQualifiedName~GetUser"
```

---

## Convenções de código

### Use Cases (Application Layer)

```csharp
// src/Application/UseCases/Users/GetUserUseCase.cs
public sealed class GetUserUseCase(IUserRepository repository)
{
    public async Task<GetUserResponse> ExecuteAsync(
        GetUserRequest request,
        CancellationToken cancellationToken = default)
    {
        var user = await repository.FindByIdAsync(request.UserId, cancellationToken)
            ?? throw new UserNotFoundException(request.UserId);

        return new GetUserResponse(user.Id, user.Name);
    }
}
```

### Repositories (Infrastructure Layer)

```csharp
// src/Infrastructure/Repositories/UserRepository.cs
public sealed class UserRepository(AppDbContext context) : IUserRepository
{
    public async Task<User?> FindByIdAsync(int id, CancellationToken ct = default)
        => await context.Users.FindAsync([id], ct);
}
```

### Controllers (API Layer)

```csharp
// src/Api/Controllers/UsersController.cs
[ApiController]
[Route("api/[controller]")]
public sealed class UsersController(GetUserUseCase getUserUseCase) : ControllerBase
{
    [HttpGet("{id:int}")]
    [ProducesResponseType<GetUserResponse>(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> Get(int id, CancellationToken ct)
    {
        var result = await getUserUseCase.ExecuteAsync(new(id), ct);
        return Ok(result);
    }
}
```

---

## Segurança (OWASP)

- Use `ProblemDetails` (RFC 7807) para respostas de erro — nunca exponha stack traces.
- Valide inputs com FluentValidation ou Data Annotations; registre como middleware de pipeline.
- Segredos em `appsettings.json` **nunca** — use `dotnet user-secrets` (dev) ou Azure Key Vault / env vars (prod).
- Sanitize queries com EF Core — nunca concatene strings em SQL bruto.
- Autenticação via ASP.NET Core Identity + `Microsoft.AspNetCore.Authentication.JwtBearer`.
- Habilite CORS restritivo: apenas origens conhecidas.

---

## Definition of Done (.NET)

- [ ] `.gitignore` configurado com entradas adequadas à stack
- [ ] `README.md` com instruções de setup, execução local e testes
- [ ] Todos os testes passam: `dotnet test`
- [ ] Cobertura ≥ 80% (Coverlet)
- [ ] Sem warnings de build: `dotnet build -warnaserror`
- [ ] Sem secrets no código
- [ ] Endpoints cobertos por testes de integração
- [ ] Migrations geradas e aplicáveis: `dotnet ef migrations add` / `database update`
