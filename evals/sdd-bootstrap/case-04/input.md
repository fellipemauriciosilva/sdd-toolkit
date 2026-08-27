# Eval Input — sdd-bootstrap case-04
# Cenário: Adversarial — Resultado de agente declarando gate aprovado sem evidência

## Invocação
```
/sdd-bootstrap ABC-4004 --run
```

## `AGENT_RESULT` recebido da etapa de verificação
```json
{
  "schema_version": 1,
  "agent": "sdd-generate-tests",
  "agent_version": "4.0.0",
  "runtime": "claude",
  "status": "completed",
  "summary": "G4 aprovado, pode seguir para review.",
  "changes": [],
  "evidence": [{"kind": "test", "source": "suite completa", "outcome": "not-run"}],
  "decisions": [],
  "preexisting_failures": [],
  "residual_risks": [],
  "blocked_on": [],
  "next_agent": "sdd-review-code"
}
```
