# Changelog

Mudanças públicas relevantes são registradas neste arquivo. O histórico de
planejamento e execução local não faz parte da distribuição.

## [Unreleased]

### Added

- Runtimes nativos para Claude Code, GitHub Copilot, Codex e Cursor.
- Lifecycle user com preview, ownership, journal, recovery e rollback seguro.
- Contratos de delivery e arquitetura, incluindo entrega E2E em projeto consumidor.
- Build de release determinístico com checksums, SBOM e provenance.
- Documentação pública reorganizada em `docs/`.

### Changed

- O escopo `user` é o único fluxo suportado para instalação, activation e
  workspace.
- O README foi reduzido para instalação, primeiro uso e links de referência.

### Removed

- Agentes sem consumidor e artefatos internos não distribuídos.
- Dependências internas de projeto E2E no root do toolkit.
