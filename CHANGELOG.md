# Changelog

Mudanças públicas relevantes são registradas neste arquivo. O histórico de
planejamento e execução local não faz parte da distribuição.

## [Unreleased]

### BREAKING CHANGES

- O agente orquestrador foi renomeado de `sdd-bootstrap` para
  `sdd-orchestrator`. "Bootstrap" descrevia só o primeiro passo — inicializar
  uma demanda —, não o papel que o agente cumpre no resto do ciclo: resolver
  contexto, montar o Context Pack antes de cada agente, despachar estágios,
  avaliar gates e ser o único dono do estado. Ver
  `docs/ROADMAP.local.md` #34 para o mapeamento completo.
  - `sdd start --json` e `sdd resume --json` devolvem `"agent":
    "sdd-orchestrator"` em vez de `"sdd-bootstrap"`. Qualquer automação que lê
    esse campo precisa ser atualizada.
  - O arquivo do agente é `agents/sdd-orchestrator.md`; os artefatos
    compilados mudam de nome nos quatro runtimes (`sdd-orchestrator.md`,
    `.toml`, `.agent.md`) e a skill compartilhada passa a viver em
    `dist/shared/skills/sdd-orchestrator/`.
  - `sdd update` remove automaticamente o `sdd-bootstrap.*` órfão do perfil
    de quem atualiza a partir de uma instalação 4.x — não é necessário
    desinstalar e reinstalar. Ver a entrada de `Fixed` abaixo.
  - Não há alias de transição: haver dois orquestradores instalados
    simultaneamente violaria o contrato de posse única de `session-state.md`
    e `state.json`. Quem integrou pelo nome do agente deve atualizar a
    referência.

### Added

- Tipo de demanda `greenfield` para projetos criados do zero, com o template
  `templates/specs/types/task-greenfield.md` e a tabela Foundation Decision.
  Mapeia para `delivery_kind: application` e continua roteando para
  `sdd-implement-spec`; o contrato de delivery não mudou. `new-project` e
  `novo-projeto` normalizam para `greenfield`.
- `sdd-architect` passou a ser o dono da decisão de fundação em demandas
  `greenfield`: linguagem, framework, build, framework de teste, layout e a
  skill de stack que governa a entrega. Exige alternativas comparadas com
  critério e proíbe popularidade ou default do agente como justificativa.
- `tests/test_public_content_check.py` cobre o gate de conteúdo público, que
  até então não tinha teste algum.

### Changed

- `sdd-orchestrator` ativa o projeto a partir do próprio runtime. Quando
  `sdd context resolve` devolve `status: unactivated`, ele apresenta o preview,
  pede confirmação explícita e executa `sdd start <TICKET> --yes`. O terminal
  deixa de ser obrigatório para iniciar uma demanda nos quatro runtimes;
  `sdd activate` e `sdd start` seguem válidos para automação e CI.
- `greenfield` classifica como impacto arquitetural `high` de forma
  incondicional, então nunca recebe design curto e sempre passa por checkpoint
  humano antes da entrega.
- README reorganizado como entrada de produto: cabeçalho, índice, um quickstart
  por intenção (ticket comum, projeto do zero, investigação de bug), tabela de
  runtimes com onde escrever em cada um, tabela de tipos de demanda e tabela
  "quero… / leia". O teto de linhas do README subiu de 220 para 400; o teste
  continua existindo para impedir que ele vire depósito.
- `sdd-implement-spec` bloqueia quando a fundação de uma demanda `greenfield`
  está pendente, em vez de escolher a stack por conta própria. Sem baseline, o
  alvo passa a ser o menor esqueleto que compila, roda e tem um teste passando.

- Entrada pública em inglês: `README.md` e `docs/QUICKSTART.md` passaram a ser
  os documentos primários, com a tradução ao lado em `README.pt-BR.md` e
  `docs/QUICKSTART.pt-BR.md` e seletor de idioma no topo de cada um. O restante
  de `docs/` permanece em português e é traduzido sob demanda; os agentes
  permanecem em português por dependência do linter, conforme
  `CONTRIBUTING.md`.
- `tests/test_release_engineering.py` passou a comparar o README traduzido com
  o primário: contagem de títulos, âncoras obrigatórias e presença dos links de
  referência. Tradução que perde seção deixa de ser tradução e vira fork.

### Removed

- `OVERVIEW.md` da raiz e do pacote de release. O documento misturava
  documentação de produto com uma avaliação datada do próprio toolkit — número
  de testes, contagem de arquivos e lista de achados — que envelhecia a cada
  commit e já estava incorreta. O conteúdo de referência vive em
  `docs/ARCHITECTURE.md`, `docs/PIPELINE.md` e `docs/AGENTS.md`; a entrada de
  uso é o `README.md` com `docs/QUICKSTART.md`.

### Fixed

- O gate de conteúdo público não detectava chaves de projeto da OpenAI no
  formato `sk-proj-*`: o padrão exigia dez ou mais alfanuméricos imediatamente
  após `sk-`, e a sequência quebra no hífen. Agora cobre chaves segmentadas.
- O mesmo gate acusava credencial em qualquer palavra hifenizada terminada em
  `sk` seguida de dez ou mais alfanuméricos: `task-greenfield` termina nessa
  forma e derrubava a verificação, sem conter credencial alguma. Os prefixos
  `sk-`, `ghp_` e `github_pat_` agora exigem fronteira de token.
- `sdd update` retinha silenciosamente qualquer asset cuja fonte deixasse de
  existir — um agente renomeado ou removido do kit continuava instalado e
  funcional no perfil de quem atualizasse, sem aviso. `install_user` agora
  remove um asset obsoleto sempre que seu hash em disco ainda bate com o que
  foi instalado; se o arquivo foi modificado por fora, o update bloqueia como
  qualquer outro conflito de asset, em vez de apagar uma alteração do usuário.
  O preview de `update` ganhou a chave `obsolete` para mostrar o que será
  removido antes do `--apply`.

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

- `Path.write_text(..., newline=...)` exige Python 3.10 e era usado em nove
  pontos, incluindo o compilador e o gerador de release. Substituído por
  `write_bytes(...encode("utf-8"))`, que é equivalente — `newline="
"` já
  significava "sem tradução" — e preserva a garantia de LF nos artefatos
  gerados. `dist/` continua byte a byte idêntico após a mudança.
- `tests/test_runtime_adapters.py` importava `tomllib`, que só entrou na
  stdlib no 3.11. Passa a cair para o backport `tomli` no piso 3.9.

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
