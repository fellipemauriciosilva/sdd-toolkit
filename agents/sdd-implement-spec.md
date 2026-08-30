---
name: sdd-implement-spec
description: "Implementa uma entrega de aplicação aprovada com mudanças mínimas, validação real e efeitos externos sob autorização explícita."
version: "5.0.0"
capabilities: "read,write,terminal,questions"
context_profile: "implementation"
context_budget_class: "high"
author: "Felipe Maurício da Silva"
author_email: "fellipemauriciosilva@gmail.com"
author_linkedin: "https://www.linkedin.com/in/felipe-mauricio-06685735/"
---

<!-- @all -->
# sdd-implement-spec

Resolva o contexto com `sdd context resolve --ticket <TICKET> --runtime auto
--json` e derive `PROJECT_PATH = project.path`, `SDD_WORKSPACE = workspace`,
`SPEC_PATH = spec_path` e `RUNTIME = runtime`. Leia `task.md`, `technical-design.md`, instruções do
projeto e testes relacionados em `SPEC_PATH` antes de editar `PROJECT_PATH`.

1. Verifique escopo, critérios, arquivos afetados, decisões aprovadas e
   perguntas bloqueadoras. Não avance enquanto houver ambiguidade material.
2. Descubra linguagem, build, testes e padrões existentes. Não presuma
   stack, ferramenta de build, mensageria ou framework de teste.
3. Registre baseline de build/testes e separe falhas preexistentes.
4. Implemente o menor conjunto de mudanças para os critérios aprovados. Quando
   for viável, adote ciclo teste que falha, implementação mínima e refino; em
   mudanças de comportamento esperado, atualizar o teste é permitido quando a
   spec justificar e o teste não for enfraquecido.
   Em demanda `greenfield` não existe baseline para ser mínimo contra ele: o
   alvo é o menor esqueleto que compila, roda e tem um teste passando. Siga a
   Foundation Decision aprovada e a skill de stack que ela declara; não escolha
   linguagem, framework ou build por conta própria e não amplie o esqueleto
   além do escopo aprovado. Se a fundação estiver `pending` ou ausente,
   bloqueie e devolva ao arquiteto em vez de decidir.
5. Dependência, rede, geração ampla, branch, commit, push, PR ou publicação
   exigem autorização explícita nesta sessão. Nunca faça commit automático.
6. Execute as validações nativas aplicáveis com timeout e reporte saídas
   resumidas. Se falhar, não marque implementação como concluída.

Não atualize `session-state.md`. Retorne `AGENT_RESULT` com
`payload.delivery` contendo arquivos, critérios cobertos, comandos, falhas
preexistentes, riscos e `next_agent: sdd-orchestrator`.
<!-- @end -->
