# Avisos de terceiros

Este arquivo acompanha o pacote distribuído do SDD Toolkit. Ele lista código,
ferramentas e automações que não são parte do conteúdo autoral do toolkit.
Licenças e obrigações devem ser revalidadas na preparação de cada release.

## Dependências de desenvolvimento

| Componente | Uso | Versão/escopo | Licença | Origem |
|---|---|---|---|---|
| `jsonschema` | Validação dos schemas durante testes e CI | `requirements-dev.txt`; não é empacotado pelo instalador | MIT (`MIT`) | https://github.com/python-jsonschema/jsonschema |

O runtime de produção usa somente a biblioteca padrão do Python e os scripts do
próprio projeto. A dependência acima existe apenas para validação de
desenvolvimento e não é copiada para o projeto do usuário.

O toolkit documenta e pode orientar a instalação de Playwright no projeto
consumidor, mas não depende nem redistribui Playwright, browsers ou pacotes npm.
Licenças e versões dessas dependências pertencem ao inventário do projeto que
optar por gerá-las.

## Automação de CI

| Componente | Uso | Referência fixada | Licença | Origem |
|---|---|---|---|---|
| `actions/checkout` | Checkout do repositório nos workflows | SHA fixado no workflow | MIT (`MIT`) | https://github.com/actions/checkout |
| `gitleaks/gitleaks-action` | Secret scan do checkout e histórico | SHA fixado em `.github/workflows/security.yml` | MIT (`MIT`) | https://github.com/gitleaks/gitleaks-action |

As actions são executadas somente no ambiente de CI. Não fazem parte dos
artefatos instalados no projeto do usuário.

## Conteúdo do toolkit

`agents/`, `templates/`, `evals/`, `schemas/`, `scripts/` e `dist/` são tratados
como conteúdo mantido pelo SDD Toolkit. Cada item deve ser confirmado pelos
mantenedores no inventário de [PROVENANCE](docs/PROVENANCE.md) antes do beta.

Não incluir neste arquivo conteúdo de cliente, exemplos copiados de terceiros,
marcas, imagens ou trechos de documentação sem origem e licença verificáveis.

## Checklist de release

- [ ] Confirmar a licença de cada dependência na versão efetivamente usada.
- [ ] Atualizar referências SHA quando uma action for atualizada.
- [ ] Registrar novos componentes neste arquivo e no inventário de proveniência.
- [ ] Validar que o pacote final não contém dependências de desenvolvimento,
      fixtures, caches ou dados locais.
- [ ] Obter aprovação dos responsáveis antes de publicar a release.
