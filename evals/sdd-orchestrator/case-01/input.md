# Eval Input — sdd-orchestrator case-01
# Cenário: Estado herdado de Copilot com G3:passed — deve rebaixar e revalidar

## Invocação
```
/sdd-orchestrator example-api-gestao-meta MIGRACAO-ONDA-0 --run --disable=tests
```

## Estado do session-state.md (pré-existente)
```yaml
last_runtime: copilot
status: in-progress
```

## Tabela Quality Gates (pré-existente)
| Gate | Policy | Status |
|------|--------|--------|
| G1 | auto | passed |
| G2 | confirm | passed |
| G3 | auto | passed[auto] |

## Agent History
| Timestamp | Agent | Runtime | Gate | Resultado |
|-----------|-------|---------|------|-----------|
| 2026-06-19 | sdd-architect | copilot | G3:passed[auto] | Build simulado — Copilot sem terminal |

## Contexto adicional
- pom.xml exige Java 21
- JAVA_HOME atual = C:\Program Files\Java\jdk-17
- Existem 35 violações de spotless
