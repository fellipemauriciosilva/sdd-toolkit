# Eval Input — sdd-bootstrap case-02
# Cenário: G3 failed 3x consecutivas → deve escalar ao humano

## Invocação
```
/sdd-bootstrap example-project ABC-1234 --run
```

## Estado do session-state.md
```yaml
status: in-progress
last_runtime: claude
retries: 2
blocked_on: —
```

## Pipeline Steps
| Etapa | Estado |
|-------|--------|
| analyze | done |
| implement | done |
| tests | enabled |
| review | enabled |
| docs | enabled |

## Quality Gates
| Gate | Policy | Status |
|------|--------|--------|
| G1 | auto | passed |
| G2 | confirm | passed |
| G3 | auto | failed |

## Contexto adicional
- Build retorna: `COMPILATION ERROR: cannot find symbol class CompetenciaService`
- Já foi retentado 2x com o erro injetado no contexto
- Próxima tentativa seria a 3ª (retries seria 3)
