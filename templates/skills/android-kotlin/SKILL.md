---
name: android-kotlin
description: Skill para desenvolvimento de aplicativos Android nativos com Kotlin. Use quando a tarefa envolver Activities, Fragments, Jetpack Compose, ViewModels, navegação, persistência local ou integração com APIs em projetos Android nativos. Inclui padrões de TDD com JUnit 5, MockK e Espresso, estrutura de projeto por feature, convenções de código e boas práticas de segurança.
---

# Android Nativo (Kotlin)

## Stack tecnológica

| Componente | Tecnologia |
|---|---|
| Linguagem | Kotlin 2.0+ |
| Min SDK | 26 (Android 8.0) |
| Target SDK | 35 (Android 15) |
| UI | Jetpack Compose (preferencial) / View System (legado) |
| Arquitetura | MVVM + Clean Architecture |
| DI | Hilt (Dagger) |
| Navegação | Navigation Compose / Navigation Component |
| HTTP client | Retrofit 2 + OkHttp + Kotlinx Serialization |
| Persistência local | Room |
| Async | Kotlin Coroutines + Flow |
| Testes unitários | JUnit 5 + MockK + Turbine (Flow) |
| Testes de UI | Compose Testing + Espresso |
| Testes de integração | Robolectric |
| Cobertura | JaCoCo (mínimo 80%) |
| Build | Gradle Kotlin DSL |
| Linting | ktlint + detekt |
| CI | ktlint + detekt + testes no build |

---

## Estrutura de projeto (feature-based + Clean Architecture)

```
app/src/
  main/
    java/com/<empresa>/<app>/
      core/                         # Código compartilhado entre features
        di/                         # Módulos Hilt globais
          NetworkModule.kt
          DatabaseModule.kt
        network/
          ApiClient.kt
          AuthInterceptor.kt
        database/
          AppDatabase.kt
        ui/
          theme/
            Theme.kt
            Color.kt
            Type.kt
          components/               # Composables reutilizáveis
            LoadingIndicator.kt
            ErrorState.kt
        util/
          Extensions.kt
      feature/
        <dominio>/
          data/
            remote/
              <Dominio>Api.kt         # Interface Retrofit
              dto/
                <Dominio>Dto.kt
            local/
              <Dominio>Dao.kt
              entity/
                <Dominio>Entity.kt
            repository/
              <Dominio>RepositoryImpl.kt
            mapper/
              <Dominio>Mapper.kt
          domain/
            model/
              <Dominio>.kt            # Modelos de domínio (data class pura)
            repository/
              <Dominio>Repository.kt   # Interface
            usecase/
              Get<Dominio>UseCase.kt
          presentation/
            <Dominio>Screen.kt        # Composable principal
            <Dominio>ViewModel.kt
            components/
              <Dominio>Card.kt        # Composables específicos da feature
            navigation/
              <Dominio>Navigation.kt
          di/
            <Dominio>Module.kt        # Módulo Hilt da feature
      MainApplication.kt
    res/
      values/
        strings.xml
        themes.xml
  test/                              # Testes unitários
    java/com/<empresa>/<app>/
      feature/<dominio>/
        data/repository/
          <Dominio>RepositoryImplTest.kt
        domain/usecase/
          Get<Dominio>UseCaseTest.kt
        presentation/
          <Dominio>ViewModelTest.kt
  androidTest/                       # Testes instrumentados
    java/com/<empresa>/<app>/
      feature/<dominio>/
        presentation/
          <Dominio>ScreenTest.kt
```

---

## Scaffolding inicial

Ao iniciar um novo projeto, crie os seguintes arquivos **antes de qualquer código de produção ou teste**:

### `.gitignore`

```gitignore
*.iml
.gradle/
/local.properties
.idea/
*.apk
*.aab
/build/
app/build/
*.hprof
.cxx/
*.keystore
!debug.keystore
.env
.confluence-cache/
```

### `README.md`

Crie um `README.md` na raiz do projeto com, no mínimo:

- Nome e descrição do projeto
- Pré-requisitos (JDK, Android SDK, Android Studio)
- Min SDK e Target SDK
- Como sincronizar e instalar dependências (`./gradlew dependencies`)
- Como rodar o projeto no emulador/device
- Como rodar os testes (`./gradlew test`)
- Como gerar APK/AAB (`./gradlew assembleDebug`)
- Variáveis de ambiente necessárias (sem valores reais)

---

## TDD com JUnit 5 + MockK

### Ciclo obrigatório

```
🔴 RED    → ./gradlew test → deve FALHAR
🟢 GREEN  → implementar o mínimo → ./gradlew test → deve PASSAR
🔵 REFACTOR → refatorar → ./gradlew test → deve continuar PASSANDO
```

### Teste de ViewModel (Arrange-Act-Assert)

```kotlin
// app/src/test/java/.../feature/users/presentation/UserListViewModelTest.kt
import app.cash.turbine.test
import io.mockk.coEvery
import io.mockk.mockk
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.DisplayName
import org.junit.jupiter.api.Test

@OptIn(ExperimentalCoroutinesApi::class)
class UserListViewModelTest {

    private val testDispatcher = StandardTestDispatcher()
    private val getUsersUseCase: GetUsersUseCase = mockk()
    private lateinit var sut: UserListViewModel

    @BeforeEach
    fun setUp() {
        Dispatchers.setMain(testDispatcher)
    }

    @AfterEach
    fun tearDown() {
        Dispatchers.resetMain()
    }

    @Test
    @DisplayName("deve emitir lista de usuários quando carregamento é bem-sucedido")
    fun loadUsers_whenSuccess_emitsUserList() = runTest {
        // Arrange
        val users = listOf(User(id = 1, name = "Alice"))
        coEvery { getUsersUseCase() } returns Result.success(users)
        sut = UserListViewModel(getUsersUseCase)

        // Act & Assert
        sut.uiState.test {
            assertEquals(UiState.Loading, awaitItem())
            val success = awaitItem()
            assertInstanceOf(UiState.Success::class.java, success)
            assertEquals(users, (success as UiState.Success).users)
        }
    }

    @Test
    @DisplayName("deve emitir erro quando carregamento falha")
    fun loadUsers_whenFailure_emitsError() = runTest {
        // Arrange
        coEvery { getUsersUseCase() } returns Result.failure(Exception("Network error"))
        sut = UserListViewModel(getUsersUseCase)

        // Act & Assert
        sut.uiState.test {
            assertEquals(UiState.Loading, awaitItem())
            val error = awaitItem()
            assertInstanceOf(UiState.Error::class.java, error)
        }
    }
}
```

### Teste de UseCase

```kotlin
// app/src/test/java/.../feature/users/domain/usecase/GetUsersUseCaseTest.kt
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.mockk
import kotlinx.coroutines.test.runTest
import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.DisplayName
import org.junit.jupiter.api.Test

class GetUsersUseCaseTest {

    private val repository: UserRepository = mockk()
    private val sut = GetUsersUseCase(repository)

    @Test
    @DisplayName("deve retornar lista de usuários do repositório")
    fun invoke_whenCalled_returnsUsersFromRepository() = runTest {
        // Arrange
        val users = listOf(User(id = 1, name = "Alice"))
        coEvery { repository.getUsers() } returns users

        // Act
        val result = sut()

        // Assert
        assertTrue(result.isSuccess)
        assertEquals(users, result.getOrNull())
        coVerify(exactly = 1) { repository.getUsers() }
    }
}
```

### Teste de Repository (integração com Room)

```kotlin
// app/src/test/java/.../feature/users/data/repository/UserRepositoryImplTest.kt
import io.mockk.coEvery
import io.mockk.mockk
import kotlinx.coroutines.test.runTest
import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.DisplayName
import org.junit.jupiter.api.Test

class UserRepositoryImplTest {

    private val api: UserApi = mockk()
    private val dao: UserDao = mockk(relaxed = true)
    private val mapper = UserMapper()
    private val sut = UserRepositoryImpl(api, dao, mapper)

    @Test
    @DisplayName("deve buscar usuários da API e salvar no cache local")
    fun getUsers_whenApiSuccess_returnsMappedUsers() = runTest {
        // Arrange
        val dtos = listOf(UserDto(id = 1, name = "Alice"))
        coEvery { api.getUsers() } returns dtos

        // Act
        val result = sut.getUsers()

        // Assert
        assertEquals(1, result.size)
        assertEquals("Alice", result.first().name)
    }
}
```

### Teste de Composable (UI)

```kotlin
// app/src/androidTest/java/.../feature/users/presentation/UserListScreenTest.kt
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import org.junit.Rule
import org.junit.Test

class UserListScreenTest {

    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun userListScreen_whenLoading_showsProgressIndicator() {
        // Arrange
        composeTestRule.setContent {
            UserListScreen(uiState = UiState.Loading)
        }

        // Assert
        composeTestRule
            .onNodeWithContentDescription("Carregando")
            .assertIsDisplayed()
    }

    @Test
    fun userListScreen_whenSuccess_showsUserNames() {
        // Arrange
        val users = listOf(User(id = 1, name = "Alice"))
        composeTestRule.setContent {
            UserListScreen(uiState = UiState.Success(users))
        }

        // Assert
        composeTestRule
            .onNodeWithText("Alice")
            .assertIsDisplayed()
    }

    @Test
    fun userListScreen_whenError_showsRetryButton() {
        // Arrange
        composeTestRule.setContent {
            UserListScreen(uiState = UiState.Error("Erro de rede"))
        }

        // Assert
        composeTestRule
            .onNodeWithText("Tentar novamente")
            .assertIsDisplayed()
    }
}
```

### Comandos de teste

```bash
# rodar todos os testes unitários
./gradlew test

# rodar testes de um módulo específico
./gradlew :app:testDebugUnitTest

# rodar testes instrumentados (requer emulador/device)
./gradlew connectedAndroidTest

# com relatório de cobertura JaCoCo
./gradlew jacocoTestReport

# verificar linting
./gradlew ktlintCheck detekt

# rodar apenas um teste específico
./gradlew test --tests "*.UserListViewModelTest"
```

---

## Convenções de código

### ViewModel (Presentation Layer)

```kotlin
// app/src/main/java/.../feature/users/presentation/UserListViewModel.kt
@HiltViewModel
class UserListViewModel @Inject constructor(
    private val getUsersUseCase: GetUsersUseCase,
) : ViewModel() {

    private val _uiState = MutableStateFlow<UiState>(UiState.Loading)
    val uiState: StateFlow<UiState> = _uiState.asStateFlow()

    init {
        loadUsers()
    }

    fun loadUsers() {
        viewModelScope.launch {
            _uiState.value = UiState.Loading
            getUsersUseCase()
                .onSuccess { users ->
                    _uiState.value = UiState.Success(users)
                }
                .onFailure { error ->
                    _uiState.value = UiState.Error(error.message ?: "Erro desconhecido")
                }
        }
    }
}

sealed interface UiState {
    data object Loading : UiState
    data class Success(val users: List<User>) : UiState
    data class Error(val message: String) : UiState
}
```

### Composable Screen

```kotlin
// app/src/main/java/.../feature/users/presentation/UserListScreen.kt
@Composable
fun UserListScreen(
    viewModel: UserListViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    UserListScreen(uiState = uiState, onRetry = viewModel::loadUsers)
}

@Composable
fun UserListScreen(
    uiState: UiState,
    onRetry: () -> Unit = {},
) {
    when (uiState) {
        is UiState.Loading -> LoadingIndicator()
        is UiState.Success -> UserList(users = uiState.users)
        is UiState.Error -> ErrorState(
            message = uiState.message,
            onRetry = onRetry,
        )
    }
}

@Composable
private fun UserList(users: List<User>) {
    LazyColumn {
        items(users, key = { it.id }) { user ->
            UserCard(user = user)
        }
    }
}
```

### UseCase (Domain Layer)

```kotlin
// app/src/main/java/.../feature/users/domain/usecase/GetUsersUseCase.kt
class GetUsersUseCase @Inject constructor(
    private val repository: UserRepository,
) {
    suspend operator fun invoke(): Result<List<User>> = runCatching {
        repository.getUsers()
    }
}
```

### Repository (Data Layer)

```kotlin
// app/src/main/java/.../feature/users/data/repository/UserRepositoryImpl.kt
class UserRepositoryImpl @Inject constructor(
    private val api: UserApi,
    private val dao: UserDao,
    private val mapper: UserMapper,
) : UserRepository {

    override suspend fun getUsers(): List<User> {
        val dtos = api.getUsers()
        val entities = dtos.map(mapper::dtoToEntity)
        dao.insertAll(entities)
        return entities.map(mapper::entityToDomain)
    }
}
```

### Retrofit API Interface

```kotlin
// app/src/main/java/.../feature/users/data/remote/UserApi.kt
interface UserApi {
    @GET("users")
    suspend fun getUsers(): List<UserDto>

    @GET("users/{id}")
    suspend fun getUserById(@Path("id") id: Long): UserDto
}
```

### Hilt Module

```kotlin
// app/src/main/java/.../feature/users/di/UserModule.kt
@Module
@InstallIn(SingletonComponent::class)
abstract class UserModule {

    @Binds
    abstract fun bindUserRepository(
        impl: UserRepositoryImpl,
    ): UserRepository

    companion object {
        @Provides
        fun provideUserApi(retrofit: Retrofit): UserApi =
            retrofit.create(UserApi::class.java)
    }
}
```

### Navegação

```kotlin
// app/src/main/java/.../feature/users/presentation/navigation/UserNavigation.kt
fun NavGraphBuilder.userGraph(navController: NavHostController) {
    composable("users") {
        UserListScreen(
            onUserClick = { userId ->
                navController.navigate("users/$userId")
            },
        )
    }
    composable(
        route = "users/{userId}",
        arguments = listOf(navArgument("userId") { type = NavType.LongType }),
    ) { backStackEntry ->
        val userId = backStackEntry.arguments?.getLong("userId") ?: return@composable
        UserDetailScreen(userId = userId)
    }
}
```

---

## Segurança (OWASP)

- **Nunca** armazene tokens, senhas ou chaves de API em `strings.xml`, `BuildConfig` ou código-fonte — use `EncryptedSharedPreferences` para dados sensíveis locais.
- Valide certificados SSL — **nunca** desabilite a verificação de certificados (`TrustAllCerts`) mesmo em debug.
- Use `ProGuard`/`R8` para ofuscação de código em builds de release.
- Comunicação com APIs **sempre** via HTTPS — configure `network_security_config.xml` com `cleartextTrafficPermitted="false"`.
- Valide e sanitize toda entrada do usuário antes de enviar ao backend.
- Use `@Query` parametrizado no Room — **nunca** concatene strings em queries SQL.
- Não exponha componentes (`Activity`, `Service`, `BroadcastReceiver`) desnecessariamente — use `android:exported="false"` quando possível.
- Dados sensíveis não devem ser logados — evite `Log.d` com informações pessoais ou tokens.
- Use `BiometricPrompt` para autenticação biométrica quando necessário — **nunca** implemente verificação biométrica customizada.
- Verifique permissões em runtime com `ActivityCompat.checkSelfPermission` — solicite apenas as permissões estritamente necessárias.

---

## Boas práticas específicas Android

- **Lifecycle-aware**: Use `collectAsStateWithLifecycle()` no Compose para respeitar o ciclo de vida.
- **Configuração de tela**: Trate mudanças de configuração (rotação) corretamente via `ViewModel` — nunca salve estado na `Activity`.
- **Deep links**: Declare deep links no `AndroidManifest.xml` e valide-os com `intent-filter` verificados (App Links).
- **Acessibilidade**: Adicione `contentDescription` em imagens e ícones. Use `semantics {}` no Compose para leitores de tela.
- **Performance**: Use `LazyColumn`/`LazyRow` para listas. Evite recomposições desnecessárias com `remember`, `derivedStateOf` e `key`.
- **Offline-first**: Para dados críticos, implemente cache local com Room + estratégia de sync (single source of truth no banco local).

---

## Definition of Done (Android Kotlin)

- [ ] `.gitignore` configurado com entradas adequadas à stack
- [ ] `README.md` com instruções de setup, execução local e testes
- [ ] Todos os testes unitários passam: `./gradlew test`
- [ ] Testes instrumentados passam: `./gradlew connectedAndroidTest`
- [ ] Cobertura ≥ 80%: `./gradlew jacocoTestReport`
- [ ] Sem warnings de lint: `./gradlew lint`
- [ ] Sem erros de ktlint: `./gradlew ktlintCheck`
- [ ] Sem findings do detekt: `./gradlew detekt`
- [ ] Sem secrets no código
- [ ] `contentDescription` em todos os elementos visuais relevantes
- [ ] Telas funcionam em modo retrato e paisagem
- [ ] Sem `android:exported="true"` desnecessário