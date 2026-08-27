---
name: sdd-analyze-migration
description: "Analisa uma migração por evidências, registra lacunas e propõe ondas verificáveis sem manipular segredos nem executar migração externa."
version: "4.0.0"
capabilities: "read,write,terminal,questions"
author: "Felipe Maurício da Silva"
author_email: "fellipemauriciosilva@gmail.com"
author_linkedin: "https://www.linkedin.com/in/felipe-mauricio-06685735/"
---

<!-- @all -->
# sdd-analyze-migration

Resolva o contexto com `sdd context resolve --ticket <TICKET> --runtime auto
--json` e derive `PROJECT_PATH = project.path`, `SDD_WORKSPACE = workspace`,
`SPEC_PATH = spec_path` e `RUNTIME = runtime`. Produza análise AS-IS em `SPEC_PATH`; não execute migração, não
descompile binários automaticamente e não acesse ambientes externos.

1. Inventarie somente evidências disponíveis em `PROJECT_PATH` e anexos:
   componentes, dependências, dados, interfaces, build, testes e operação.
2. Para cada achado, registre caminho, método de detecção, confiança
   (`confirmed`, `inferred`, `unknown`) e ação de validação para lacunas.
3. Redija credenciais, segredos, dados pessoais e URLs internas. Não afirme
   vulnerabilidade, licença, versão suportada ou fim de vida sem fonte citável.
4. Escreva `migration-analysis.md` com escopo, riscos, compatibilidade,
   estratégia de coexistência, ondas, rollback, testes e perguntas.
5. Encaminhe ao arquiteto para o TO-BE e decisão estrutural; não escolha stack
   como padrão.

Retorne `AGENT_RESULT` com `payload.migration_analysis`, sem alterar
`session-state.md`, com `next_agent: sdd-architect` ou `blocked` se faltarem
evidências essenciais.
<!-- @end -->
