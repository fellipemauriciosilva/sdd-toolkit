---
name: backend-python
description: Skill para desenvolvimento backend com Python. Use quando a tarefa envolver APIs, serviços, lógica de negócio, integração ou banco de dados usando Python com FastAPI ou Django. Inclui padrões de TDD com pytest, estrutura de projeto, convenções de código e boas práticas de segurança.
---

# Backend Python

## Stack tecnológica

| Componente | Tecnologia |
|---|---|
| Linguagem | Python 3.12+ |
| Framework web | FastAPI (padrão) ou Django/DRF |
| ORM | SQLAlchemy (FastAPI) ou Django ORM |
| Migrações | Alembic (FastAPI) ou Django migrations |
| Testes | pytest + pytest-asyncio + httpx |
| Cobertura | pytest-cov (mínimo 80%) |
| Linting | ruff |
| Formatação | black |
| Type checking | mypy |
| Gerenciamento de deps | poetry ou pip + requirements.txt |

---

## Estrutura de projeto

```
src/
  <dominio>/
    __init__.py
    routes.py          # endpoints (FastAPI) ou views.py (Django)
    schemas.py         # Pydantic models (FastAPI) ou serializers.py (DRF)
    services.py        # lógica de negócio
    repositories.py    # acesso a dados
    models.py          # modelos de banco de dados
    exceptions.py      # exceções de domínio
tests/
  unit/
    test_<dominio>_service.py
    test_<dominio>_repository.py
  integration/
    test_<dominio>_routes.py
  conftest.py          # fixtures compartilhadas
pyproject.toml
```

---

## Scaffolding inicial

Ao iniciar um novo projeto, crie os seguintes arquivos **antes de qualquer código de produção ou teste**:

### `.gitignore`

```gitignore
__pycache__/
*.pyc
*.pyo
.venv/
venv/
env/
dist/
*.egg-info/
.mypy_cache/
.ruff_cache/
.pytest_cache/
htmlcov/
.coverage
.env
.confluence-cache/
```

### `README.md`

Crie um `README.md` na raiz do projeto com, no mínimo:

- Nome e descrição do projeto
- Pré-requisitos (Python, poetry/pip)
- Como criar o ambiente virtual e instalar dependências
- Como rodar o projeto localmente (`uvicorn`, `python manage.py runserver`, etc.)
- Como rodar os testes (`pytest`)
- Como rodar linting e type checking (`ruff check`, `mypy`)
- Variáveis de ambiente necessárias (sem valores reais)

---

## TDD com pytest

### Ciclo obrigatório

```
🔴 RED    → pytest tests/unit/test_X.py::test_nome — deve FALHAR
🟢 GREEN  → implementar o mínimo → pytest — deve PASSAR
🔵 REFACTOR → refatorar → pytest — deve continuar PASSANDO
```

### Estrutura de teste (padrão Arrange-Act-Assert)

```python
# tests/unit/test_user_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.users.services import UserService
from src.users.exceptions import UserNotFoundError


class TestUserService:
    @pytest.fixture
    def user_repo(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, user_repo):
        return UserService(repository=user_repo)

    async def test_get_user_returns_user_when_found(self, service, user_repo):
        # Arrange
        user_repo.find_by_id.return_value = {"id": 1, "name": "Alice"}

        # Act
        result = await service.get_user(user_id=1)

        # Assert
        assert result["name"] == "Alice"
        user_repo.find_by_id.assert_awaited_once_with(1)

    async def test_get_user_raises_when_not_found(self, service, user_repo):
        # Arrange
        user_repo.find_by_id.return_value = None

        # Act / Assert
        with pytest.raises(UserNotFoundError):
            await service.get_user(user_id=999)
```

### Fixtures de integração (FastAPI + httpx)

```python
# tests/conftest.py
import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
```

### Comandos de teste

```bash
# rodar todos os testes
pytest

# com cobertura
pytest --cov=src --cov-report=term-missing

# apenas um módulo
pytest tests/unit/test_user_service.py -v

# parar no primeiro erro
pytest -x
```

---

## Convenções de código

### Services — lógica de negócio

```python
# src/users/services.py
from src.users.repositories import UserRepository
from src.users.exceptions import UserNotFoundError


class UserService:
    def __init__(self, repository: UserRepository) -> None:
        self._repo = repository

    async def get_user(self, user_id: int) -> dict:
        user = await self._repo.find_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User {user_id} not found")
        return user
```

### Repositories — acesso a dados

```python
# src/users/repositories.py
from sqlalchemy.ext.asyncio import AsyncSession
from src.users.models import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, user_id: int) -> User | None:
        return await self._session.get(User, user_id)
```

### Routes — endpoints FastAPI

```python
# src/users/routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from src.users.services import UserService
from src.users.schemas import UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, service: UserService = Depends()):
    return await service.get_user(user_id)
```

---

## Segurança (OWASP)

- **Nunca** exponha traceback ou detalhes internos em respostas de erro — use handlers de exceção globais.
- Valide **toda** entrada com Pydantic (FastAPI) ou serializers com `validate()` (DRF).
- Use `python-jose` ou `authlib` para JWT — nunca implemente criptografia manualmente.
- Segredos ficam em variáveis de ambiente via `pydantic-settings` ou `python-decouple`.
- Sanitize queries com o ORM — **nunca** concatene strings em queries SQL.
- Rate limiting: use `slowapi` (FastAPI) ou Django Ratelimit.

---

## Injeção de dependências

Prefira injeção explícita via construtor para facilitar testes:

```python
# ✅ testável
class OrderService:
    def __init__(self, repo: OrderRepository, notifier: Notifier) -> None:
        self._repo = repo
        self._notifier = notifier

# ❌ difícil de testar
class OrderService:
    def process(self):
        repo = OrderRepository()   # acoplamento direto
```

---

## Definition of Done (Python)

- [ ] `.gitignore` configurado com entradas adequadas à stack
- [ ] `README.md` com instruções de setup, execução local e testes
- [ ] Todos os testes passam: `pytest`
- [ ] Cobertura ≥ 80%: `pytest --cov=src`
- [ ] Sem erros de linting: `ruff check src/`
- [ ] Sem erros de tipo: `mypy src/`
- [ ] Nenhuma credencial hardcoded
- [ ] Endpoints cobertos por testes de integração