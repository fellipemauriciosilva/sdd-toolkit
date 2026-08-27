# Changelog

Mudanças públicas relevantes são registradas neste arquivo. O histórico de
planejamento e execução local não faz parte da distribuição.

## [Unreleased]

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

### Changed

- Runtimes nativos para Claude Code, GitHub Copilot, Codex e Cursor.
- Lifecycle user com preview, ownership, journal, recovery e rollback seguro.
- Contratos de delivery e arquitetura, incluindo entrega E2E em projeto consumidor.
- Build de release determinístico com checksums, SBOM e provenance.
- Documentação pública reorganizada em `docs/`.

### Changed

- O escopo `user` é o único fluxo suportado para instalação, activation e
  workspace.
- O README foi reduzido para instalação, primeiro uso e links de referência.
- Os agentes devolvem `AGENT_RESULT` em vez de blocos próprios como
  `REVIEW_RESULT` ou `DELIVERY_RESULT`; o resultado específico vai em `payload`.
- Somente `sdd-bootstrap` escreve `session-state.md`; os demais agentes
  devolvem evidência e o bootstrap consolida o estado.
- `version` e `capabilities` são propagados para os quatro runtimes compilados.
- Agentes que executam comandos declaram a capability `terminal`.
- Evidência esperada nos contratos de delivery e arquitetura passou a usar as
  chaves `payload.*` em vez de `DELIVERY_RESULT`, `UNIT_RESULT`,
  `INTEGRATION_RESULT`, `E2E_RESULT` e `ARCHITECTURE_RESULT`.
- Templates, agentes e evals ficaram agnósticos de stack e livres de exemplos
  com identificadores internos.

### Removed

- Agentes sem consumidor e artefatos internos não distribuídos.
- Dependências internas de projeto E2E no root do toolkit.
- `tasks.md` e `status-task.md`: `task.md` e `session-state.md` são os únicos
  arquivos canônicos de uma demanda.
