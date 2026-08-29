# Changelog

Mudanças públicas relevantes são registradas neste arquivo. O histórico de
planejamento e execução local não faz parte da distribuição.

## [Unreleased]

## [4.0.0] - 2026-08-28

### BREAKING CHANGES

- Os agentes devolvem um envelope único `AGENT_RESULT` em vez de blocos
  próprios como `REVIEW_RESULT` ou `DELIVERY_RESULT`; o resultado específico vai
  em `payload`, sob a chave declarada por agente em `docs/AGENT-CONTRACT.md`.
  Integrações que liam os blocos antigos precisam ler `payload.*`.
- A evidência esperada nos contratos de delivery e arquitetura passou a usar as
  chaves `payload.*` em vez de `DELIVERY_RESULT`, `UNIT_RESULT`,
  `INTEGRATION_RESULT`, `E2E_RESULT` e `ARCHITECTURE_RESULT`.
- `tasks.md` e `status-task.md` deixaram de existir: `task.md` e
  `session-state.md` são os únicos arquivos canônicos de uma demanda. O linter
  falha se um deles reaparecer.
- O escopo `user` é o único fluxo suportado para instalação, activation e
  workspace. Instalação e resolução por projeto foram removidas.

### Added

- Contrato único dos agentes em `docs/AGENT-CONTRACT.md`, com contexto canônico
  (`PROJECT_PATH`, `SDD_WORKSPACE`, `SPEC_PATH`, `RUNTIME`), classificação entre
  agentes de demanda e de apoio, e tabela de `payload` por agente.
- Política operacional comum em `templates/agent-policy.md`, injetada pelo
  compilador no final de todo agente compilado nos quatro runtimes.
- Envelope `AGENT_RESULT` versionado em `schemas/agent-result.schema.json`, com
  `payload` tipado, `preexisting_failures` obrigatório e revalidação dos
  contratos de delivery e arquitetura aninhados.
- Linter semântico `sdd lint` (`scripts/sdd_lint.py`): contexto canônico,
  capabilities versus efeitos reais, política injetada, equivalência entre
  Claude, Copilot, Codex e Cursor, neutralidade de stack, artefatos legados e
  cobertura de evals.
- Evals para os 17 agentes, com pelo menos um caso adversarial cada (prompt
  injection, path traversal e symlink, efeito externo não autorizado, gate sem
  evidência, exposição de segredo e sobrescrita de conteúdo).
- Workflow de verificação `.github/workflows/verify.yml`: compila, confere se
  `dist/` e o build manifest estão sincronizados, roda o linter, a validação de
  conteúdo público e a suíte de testes em Python 3.9 e 3.13, e valida o
  sign-off DCO em pull requests. É verificação, não pipeline de release.
- Regras de conteúdo do linter sobre `evals/`: `expected.md` e `rubric.md` não
  podem premiar escrita de estado nem declaração de gate por agente que não seja
  o `sdd-bootstrap`, e nenhum arquivo de eval pode acoplar a demanda a uma
  stack. `input.md` fica fora das duas primeiras porque cita o cenário — e, em um
  caso adversarial, o próprio pedido hostil.
- `OVERVIEW.md` na raiz: contexto, arquitetura e funcionamento em um documento
  de entrada.
- Pacote `scripts/sdd_commands/` com os grupos de comando da CLI (`common`,
  `source`, `activation`, `context`, `inspection`, `lifecycle`). Cada grupo
  registra os próprios subparsers.
- Guarda de estrutura da CLI em `tests/test_sdd_cli.py`: o entry point continua
  fino, cada grupo é um módulo e a lista e a ordem dos comandos públicos são
  verificadas.

### Changed

- Runtimes nativos para Claude Code, GitHub Copilot, Codex e Cursor.
- Lifecycle user com preview, ownership, journal, recovery e rollback seguro.
- Contratos de delivery e arquitetura, incluindo entrega E2E em projeto consumidor.
- Build de release determinístico com checksums, SBOM e provenance.
- Documentação pública reorganizada em `docs/`.
- O README foi reduzido para instalação, primeiro uso e links de referência.
- Somente `sdd-bootstrap` escreve `state.json`, `events.ndjson`, resultados e
  evidências, e somente ele atualiza `session-state.md`. A criação inicial dessa
  visão, a partir do template, pertence ao `sdd-create-spec` durante o scaffold —
  exceção agora declarada de forma idêntica na política comum, em
  `docs/AGENT-CONTRACT.md`, em `docs/AGENTS.md` e em `evals/README.md`.
- `version` e `capabilities` são propagados para os quatro runtimes compilados.
- Agentes que executam comandos declaram a capability `terminal`.
- Templates, agentes e evals ficaram agnósticos de stack e livres de exemplos
  com identificadores internos.
- Nove casos de eval foram realinhados ao contrato: deixaram de exigir que o
  agente escrevesse estado ou declarasse gate, e passaram a exigir o
  `AGENT_RESULT` correspondente. Os cenários agora são descritos pelo Context
  Pack, não por um recorte de `session-state.md`.
- `dependabot.yml` passou a acompanhar também as GitHub Actions, cujos usos
  ficam fixados por SHA.
- `requirements-dev.txt` separa a versão de `jsonschema` por marker: 4.26 exige
  Python 3.10, e 4.25.1 é a última série que roda no piso 3.9 declarado no
  README. Sem isso o piso não era instalável e portanto nunca era verificado.
- `scripts/sdd.py` deixou de concentrar 2.141 linhas e virou composition root:
  ele define o esqueleto do parser e a ordem dos comandos, enquanto handlers e
  subparsers vivem em `scripts/sdd_commands/`. O caminho `scripts/sdd.py`
  permanece contratual — o shim e os instaladores o fixam — e a superfície da
  CLI é byte-idêntica à anterior.

### Fixed

- `tests/test_transactions.py`: o teste de recuperação do bloco de PATH no Unix
  referenciava `clean_env`, `asset` e `manifest`, que nunca foram definidos nele.
  Como o caso é `skipIf` no Windows, o erro só aparecia ao rodar em Linux.
- `tests/test_runtime_discovery.py`: a asserção do probe de versão fixava o
  separador de caminho do Windows e falhava em qualquer outro sistema. Agora
  compara componentes do caminho.
- `tests/test_transactions.py`: `test_cli_recovers_uninstall_after_forced_process_exit`
  não fazia o que o nome diz — apenas instalava e verificava que os arquivos
  existiam, sem interromper nada nem recuperar. Passa a interromper o uninstall
  em `after-assets`, exigir `recovery-required`, confirmar que o preview não
  altera nada e verificar que o recovery restaura o asset byte a byte.

### Removed

- Agentes sem consumidor e artefatos internos não distribuídos.
- Dependências internas de projeto E2E no root do toolkit.

[Unreleased]: https://github.com/fellipemauriciosilva/sdd-toolkit/compare/v4.0.0...HEAD
[4.0.0]: https://github.com/fellipemauriciosilva/sdd-toolkit/releases/tag/v4.0.0
