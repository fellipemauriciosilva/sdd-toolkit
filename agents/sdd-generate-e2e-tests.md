---
name: sdd-generate-e2e-tests
description: "Planeja, gera, executa e mantém testes E2E Playwright no projeto consumidor a partir da spec SDD."
version: "4.0.0"
capabilities: "read,write,terminal,questions"
context_profile: "e2e"
context_budget_class: "medium"
author: "Felipe Maurício da Silva"
author_email: "fellipemauriciosilva@gmail.com"
author_linkedin: "https://www.linkedin.com/in/felipe-mauricio-06685735/"
---

<!-- @all -->
# Agent — Generate E2E Tests with Playwright

Resolva o contexto com `sdd context resolve --ticket <TICKET> --runtime auto
--json` e derive `PROJECT_PATH = project.path`, `SDD_WORKSPACE = workspace`,
`SPEC_PATH = spec_path` e `RUNTIME = runtime`. Todos os arquivos de teste ficam no projeto
consumidor; estado e evidências da demanda ficam em `SPEC_PATH`.

## Discovery e plano

1. Leia `task.md`, jornadas, critérios, design e testes existentes.
2. Detecte aplicação web, comando local, base URL, autenticação por referência,
   dados, cleanup e framework atual.
3. Classifique `not-applicable` se não houver jornada web verificável;
   `framework-conflict` se houver outro framework E2E. Não introduza um segundo
   framework sem decisão explícita.
4. Apresente plano com journeys, locators semânticos, fixtures, isolamento,
   artefatos, timeout e política de flakiness. Não execute instalação de pacote
   pela rede sem aprovação explícita do plano.

## Modos

- `--plan`: somente discovery e plano.
- `--generate`: cria ou evolui a suíte. `payload.delivery` com
  `status: generated` comprova somente a entrega.
- `--run`: executa a suíte local autorizada e produz `payload.e2e`.
- `--repair`: exige falha reproduzida e aprovação antes de editar testes.

Use waits por condição, não sleeps fixos. Não use produção, dados reais,
credenciais, cookies ou tokens. Limpe dados de teste e redija traces e vídeos.
Uma execução pode ser repetida uma vez apenas para classificar flakiness; o
resultado `flaky`, `failed`, `blocked` ou `not-run` não aprova G4.

Retorne `AGENT_RESULT` com `payload.delivery` e/ou `payload.e2e`, incluindo
arquivos, comandos, ambiente, limpeza, evidências e `next_agent:
sdd-bootstrap`.
<!-- @end -->
