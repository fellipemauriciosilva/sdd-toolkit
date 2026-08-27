---
name: pydantic
description: "Boas práticas para modelos Pydantic em Python. Use ao criar, revisar ou refatorar modelos de dados, validações e serialização com Pydantic v2."
---

# Boas Práticas Python + Pydantic v2

Garanta que o código em ${selection} segue as boas práticas para modelos Pydantic neste projeto.

## Definição de Modelos

- Herdar sempre de `BaseModel` (ou `BaseSettings` para configuração)
- Usar type hints explícitos em todos os campos — nunca usar `Any` sem justificativa
- Definir valores padrão com `Field(default=...)` em vez de atribuição direta quando houver metadados
- Usar `model_config = ConfigDict(...)` em vez do `class Config` interno (API v2)
- Preferir `Annotated[tipo, Field(...)]` para manter type hints limpos

## Validação

- Usar `field_validator` com `@field_validator("campo", mode="before"|"after")` para validações por campo
- Usar `model_validator(mode="after")` para validações que dependem de múltiplos campos
- Retornar o valor validado explicitamente nos validators
- Lançar `ValueError` com mensagens descritivas em português quando a validação falhar
- Evitar lógica de negócio complexa dentro dos validators — delegar para funções auxiliares

## Tipos e Campos

- Usar `Literal`, `Enum` ou `StrEnum` para valores restritos
- Usar `constr`, `conint`, `confloat` ou `Field(min_length=, max_length=, ge=, le=)` para restrições
- Preferir tipos específicos: `EmailStr`, `HttpUrl`, `IPvAnyAddress` quando aplicável
- Marcar campos opcionais com `tipo | None = None`
- Usar `SecretStr` para dados sensíveis (senhas, tokens, chaves de API)

## Serialização e Parsing

- Usar `model_dump()` em vez de `.dict()` (depreciado na v2)
- Usar `model_validate()` em vez de `.parse_obj()` (depreciado na v2)
- Configurar `model_dump(exclude_none=True)` quando campos nulos não devem ser serializados
- Usar `field_serializer` para customizar a saída de campos específicos
- Definir `alias` via `Field(alias="nome_externo")` para integração com APIs externas

## Composição e Herança

- Compor modelos complexos com modelos menores e reutilizáveis
- Usar `TypeAdapter` para validar/serializar tipos que não são `BaseModel` (listas, dicts)
- Criar modelos base abstratos para campos comuns (ex.: `id`, `created_at`, `updated_at`)
- Evitar herança profunda (máximo 2 níveis)

## Configuração (`BaseSettings`)

- Usar `BaseSettings` com `SettingsConfigDict(env_prefix="APP_")` para variáveis de ambiente
- Definir `env_file=".env"` para carregamento automático
- Validar configurações no startup da aplicação com `try/except ValidationError`

## Performance

- Usar `model_config = ConfigDict(frozen=True)` para modelos imutáveis (habilitável como hash key)
- Evitar revalidação desnecessária — usar `model_construct()` apenas quando os dados já foram validados
- Preferir `__slots__` implícito via `ConfigDict(slots=True)` para economia de memória

## Tratamento de Erros

- Capturar `ValidationError` nas bordas do sistema (endpoints, CLI, ingestão de dados)
- Usar `error.errors()` para extrair detalhes estruturados dos erros de validação
- Não silenciar erros de validação — logar e propagar adequadamente

## Testes

- Testar modelos com dados válidos e inválidos
- Verificar mensagens de erro de validação nos testes
- Usar `model_json_schema()` para validar o schema gerado em testes de contrato
