---
name: playwright-e2e-testing
description: "Padrões para planejar, criar e manter testes E2E Playwright em projetos web consumidores. Use para jornadas de navegador, configuração incremental, fixtures, autenticação, CI, locators e diagnóstico de flakiness."
---

# Playwright E2E Testing

Use esta skill quando a spec exigir uma jornada observável em navegador ou
quando o projeto já adotar Playwright. Não use para biblioteca, CLI, backend sem
UI ou para testar o lifecycle interno do SDD Toolkit.

## Contrato de entrada

Confirme antes de gerar:

- critérios de aceite e jornadas prioritárias;
- comando para iniciar a aplicação e sinal de readiness;
- base URL e ambientes autorizados;
- papéis/autenticação e origem segura dos secrets;
- dados de teste, criação e cleanup;
- package manager, CI e framework E2E existente.

Se um dado essencial estiver ausente, planeje e reporte o bloqueio em vez de
inventá-lo.

## Discovery e coexistência

- Preserve o lockfile e o package manager do projeto.
- Reutilize `playwright.config.*`, fixtures, projects e reporters existentes.
- Se Cypress, WebdriverIO ou Selenium já existir, compare custo e cobertura.
  Não introduza um segundo framework sem decisão explícita.
- Em monorepos, altere somente o package/workspace dono da aplicação.
- Mostre preview de dependências e arquivos antes de instalar ou sobrescrever.

## Configuração recomendada

- Use `baseURL` e `webServer` quando o projeto tiver comando local confiável.
- `forbidOnly` deve bloquear CI.
- Retry é aceitável no CI para diagnóstico, mas resultado flaky continua visível.
- Trace no primeiro retry ou retenção em falha; screenshots somente em falha.
- Vídeo apenas quando trouxer evidência adicional e com retenção controlada.
- Comece com Chromium; amplie browsers conforme risco e matriz suportada.
- Reports, traces, vídeos, screenshots e estados de autenticação ficam ignorados.

Não copie uma configuração pronta se o projeto já possuir convenções diferentes.

## Estrutura dos testes

- Organize por jornada/capacidade, não por detalhe de componente.
- Um teste deve ser independente, repetível e executável isoladamente.
- Prefira API/factory para preparar estado e UI para validar comportamento do
  usuário; não transforme todo setup em passos lentos de interface.
- Gere identificadores únicos por worker e faça cleanup idempotente.
- Não dependa de ordem, dados compartilhados ou conta pessoal.
- Page Objects só entram quando reduzem duplicação sem esconder expectativas.

## Locators e sincronização

Ordem preferencial:

1. `getByRole` com nome acessível;
2. `getByLabel`, `getByPlaceholder` ou `getByText` quando semântico;
3. `getByTestId` estável e acordado com a aplicação;
4. CSS restrito a casos sem alternativa, com justificativa.

Não use XPath, classes geradas, índices posicionais ou sleeps fixos como solução
padrão. Confie no auto-wait e faça assertions sobre estados observáveis.

## Autenticação e segurança

- Obtenha secrets apenas por variáveis/secret store.
- Gere storage state localmente e separe por papel e worker quando necessário.
- Nunca versione cookies, tokens, senhas, traces autenticados ou dumps reais.
- Redija headers, bodies e URLs sensíveis antes de anexar artifacts.
- Não execute contra produção sem autorização explícita e controles próprios.

## Rede e terceiros

- Intercepte somente o boundary externo necessário.
- Documente cada mock e o que deixou de ser uma integração real.
- Prefira serviços locais/fixtures determinísticas a sites públicos.
- Bloqueie requests externas inesperadas quando o ambiente permitir.

## Evidência mínima

Registre no G4:

- versão do Playwright e package manager;
- comando e projetos/browsers executados;
- cenários passed/failed/flaky/skipped;
- critérios de aceite cobertos;
- artifacts relativos e sanitizados;
- gaps, mocks e bloqueios.

“Testes criados” sem execução não equivale a gate aprovado.
