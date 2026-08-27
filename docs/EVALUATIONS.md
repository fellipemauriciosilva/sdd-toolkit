# Evals e contratos

Os evals em `evals/` descrevem entradas, resultados esperados e rubricas para
agentes críticos. Eles não representam execução em um harness real; servem para
detectar regressões de comportamento no repositório.

Contratos versionados em `schemas/` cobrem instalação, estado, contexto,
delivery, arquitetura, adapters e transações. Alterações de schema precisam de
fixture válida, fixture inválida e teste de compatibilidade.

Execute a base local:

```bash
python -m unittest discover -s tests -v
```

Antes de uma release, complete também os canaries de runtime descritos em
[HARNESS-VALIDATION.md](HARNESS-VALIDATION.md).
