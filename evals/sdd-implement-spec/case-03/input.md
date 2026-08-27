# Eval Input — sdd-implement-spec case-03
# Cenário: G2 aprovado, implementation plan incorreto (arquivo de teste com path errado)

## task.md — Affected Files
| File | Layer | Change |
|------|-------|--------|
| `application/usecase/AprovarMetaUseCase.java` | application | create |
| `test/java/com/gcb/domain/AprovarMetaUseCaseTest.java` | test | create |

## Problema detectado durante implementação
O caminho correto para testes é `src/test/java/com/gcb/...`, não `test/java/...`.
O agente percebe isso ao tentar criar o arquivo.
