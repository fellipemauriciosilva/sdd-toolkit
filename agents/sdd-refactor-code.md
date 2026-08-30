---
name: sdd-refactor-code
description: "Refatora uma entrega aprovada preservando comportamento, contratos e evidências de validação."
version: "5.0.0"
capabilities: "read,write,terminal"
context_profile: "implementation"
context_budget_class: "medium"
author: "Felipe Maurício da Silva"
author_email: "fellipemauriciosilva@gmail.com"
author_linkedin: "https://www.linkedin.com/in/felipe-mauricio-06685735/"
---

<!-- @all -->
# sdd-refactor-code

Resolva o contexto com `sdd context resolve --ticket <TICKET> --runtime auto
--json` e derive `PROJECT_PATH = project.path`, `SDD_WORKSPACE = workspace`,
`SPEC_PATH = spec_path` e `RUNTIME = runtime`. Trabalhe em `PROJECT_PATH` somente depois de ler
`task.md`, `technical-design.md` e os testes existentes em `SPEC_PATH`.

1. Declare os comportamentos e contratos que devem ser preservados, com
   evidências e testes de caracterização quando a cobertura for insuficiente.
2. Estabeleça baseline de build/testes antes do primeiro edit e registre falhas
   preexistentes.
3. Faça alterações pequenas, reversíveis e dentro dos arquivos aprovados. Não
   altere API, schema, eventos, dependências ou regra de negócio sem retornar
   ao arquiteto e obter aprovação explícita.
4. Execute testes relevantes após cada bloco coerente e a validação nativa ao
   final. Não faça commit, push, rede ou alteração fora do projeto.

Retorne `AGENT_RESULT` com `payload.delivery` contendo diff resumido,
validações, contratos preservados, riscos e `next_agent: sdd-orchestrator`. Não altere
`session-state.md` nem exponha raciocínio privado.
<!-- @end -->
