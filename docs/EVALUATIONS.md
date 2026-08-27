# Evals e contratos

Os evals em `evals/` descrevem entradas, resultados esperados e rubricas. Os 17
agentes têm cobertura, e cada um tem pelo menos um caso **adversarial**: prompt
injection em documento, código ou log; path traversal e escape por link
simbólico; efeito externo não autorizado; aprovação de gate sem evidência;
exposição de segredo; sobrescrita de conteúdo do usuário. Eles não representam
execução em um harness real; servem para detectar regressões de comportamento no
repositório.

Independentemente da rubrica de cada caso, todo eval exige o contrato descrito
em [AGENT-CONTRACT.md](AGENT-CONTRACT.md): contexto canônico resolvido pela CLI,
`AGENT_RESULT` válido, estado escrito apenas pelo `sdd-bootstrap` e efeitos
externos somente sob autorização explícita.

Contratos versionados em `schemas/` cobrem instalação, estado, contexto,
delivery, arquitetura, resultado de agente, adapters e transações. Alterações de
schema precisam de fixture válida, fixture inválida e teste de compatibilidade.

Execute a base local:

```bash
python scripts/sdd_lint.py --json
python -m unittest discover -s tests -v
```

O linter cobre contrato de contexto, capabilities versus efeitos, política comum
injetada, equivalência entre os quatro runtimes, artefatos legados e cobertura
de evals. `tests/test_agent_evals.py` garante que nenhum agente fique sem eval
ou sem caso adversarial.

Antes de uma release, complete também os canaries de runtime descritos em
[HARNESS-VALIDATION.md](HARNESS-VALIDATION.md).
