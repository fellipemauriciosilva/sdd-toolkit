# Proveniência e avisos de terceiros

Este documento acompanha a preparação do SDD Toolkit para distribuição pública.
Ele separa o que já foi verificado do que ainda exige aprovação antes do beta.

## Atribuição do mantenedor inicial

Os agentes fonte usam a identidade pública registrada em
[MAINTAINERS.md](MAINTAINERS.md). Essa atribuição cobre a manutenção inicial
dos arquivos autorais do toolkit; cada skill, exemplo, dependência, action ou
trecho derivado continua exigindo verificação de origem, licença e autorização
próprias.

## Inventário

| Área | Origem esperada | Situação antes do beta |
|---|---|---|
| `agents/` e `dist/` | Conteúdo mantido pelo projeto e artefatos compilados | Revisar autoria e autorização de redistribuição |
| `templates/skills/` | Templates e instruções mantidos pelo projeto | Confirmar autoria de cada skill |
| `evals/` | Casos de avaliação mantidos pelo projeto | Revisar exemplos e dados fictícios |
| `agents/sdd-generate-e2e-tests.md`, skill e evals Playwright | Conteúdo autoral do toolkit; não incorpora código do Playwright | Revisão técnica concluída; aprovação formal segue o gate jurídico |
| `.github/` | Responsáveis, templates e atualização de dependências | Revisar permissões, configuração de segurança e PRs do Dependabot |
| `requirements-dev.txt` | Dependências usadas somente em teste/CI | Licença e escopo registrados em `THIRD_PARTY_NOTICES.md` |

## Regras de publicação

- Não assumir que conteúdo gerado por IA ou derivado de documentação de terceiros é automaticamente redistribuível.
- Registrar a origem, licença e autorização de qualquer texto, imagem, código, binário ou marca reutilizado.
- Adicionar `THIRD_PARTY_NOTICES.md` quando houver dependências ou conteúdo de terceiros que exijam aviso.
- O inventário de componentes distribuídos deve permanecer sincronizado com
  `THIRD_PARTY_NOTICES.md`.
- Não publicar o beta enquanto houver item sem titularidade ou autorização verificável.

Este arquivo é um checklist de release, não uma declaração de que a auditoria jurídica foi concluída.
