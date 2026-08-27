# Contribuindo com o SDD Toolkit

Obrigado por contribuir. O projeto é um toolkit de prompts, templates e instaladores para Spec-Driven Development.

A autoria e os canais do mantenedor inicial estão em [MAINTAINERS.md](docs/MAINTAINERS.md).
Contribuições continuam pertencendo aos seus autores e devem seguir o DCO.

## Antes de abrir uma mudança

- Leia o [README](README.md), a [governança](docs/GOVERNANCE.md) e a documentação em `docs/`.
- Abra uma issue para mudanças de comportamento ou novas funcionalidades.
- Não inclua dados de clientes, caminhos pessoais, URLs privadas, credenciais ou conteúdo sem licença.
- Para vulnerabilidades, siga [SECURITY.md](SECURITY.md) e não abra uma issue pública.

## Estrutura importante

- `agents/`: fonte dos agentes.
- `dist/`: artefatos compilados; não edite manualmente.
- `templates/`: templates de specs, gates, verificadores e skills.
- `evals/`: cenários e rubricas de avaliação.
- `install.ps1` e `install.sh`: instaladores por plataforma.

## Alterando um agente

1. Edite o arquivo em `agents/`.
2. Preserve o frontmatter e as seções `@all`, `@claude` e `@copilot` quando aplicáveis.
3. Atualize a versão do agente se o contrato comportamental mudou.
4. Recompile os artefatos com `python scripts/sdd_compile.py --runtime all`.
5. Execute os validadores e evals correspondentes.
6. Atualize a documentação e o `CHANGELOG.md` quando necessário.

Para a capacidade Playwright, valide o contrato e os evals do agente. Não
adicione `package.json`, browsers, `playwright.config.*` ou uma suíte E2E ao root
do toolkit: esses artefatos são gerados somente no projeto consumidor.

## Pull requests

Um pull request deve explicar o problema, a solução, os runtimes afetados e como foi validado. Mudanças em instaladores, permissões, execução de terminal ou resolução de paths exigem testes multiplataforma.

Commits devem ser pequenos e descritivos. Não faça commit de arquivos gerados ou locais sem confirmar que são parte do contrato do projeto.

## DCO

O projeto adota o Developer Certificate of Origin (DCO). Cada commit enviado em
um pull request deve conter uma linha `Signed-off-by` com o nome e o e-mail do
autor, confirmando que ele tem o direito de contribuir com a alteração. O
GitHub deve exigir essa verificação antes do merge.

## Checklist

- [ ] Testes e validações executados.
- [ ] Nenhuma referência corporativa ou credencial adicionada.
- [ ] `dist/` atualizado de forma reproduzível, quando aplicável.
- [ ] Documentação atualizada.
- [ ] Breaking change identificada.
- [ ] Proveniência e licença do conteúdo novo conhecidas.
