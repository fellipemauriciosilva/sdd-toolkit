---
name: sdd-generate-tests
description: "Gera ou atualiza testes unitários a partir de uma spec aprovada, preservando padrões e comportamento existentes."
version: "4.0.0"
capabilities: "read,write,terminal"
author: "Felipe Maurício da Silva"
author_email: "fellipemauriciosilva@gmail.com"
author_linkedin: "https://www.linkedin.com/in/felipe-mauricio-06685735/"
---

<!-- @all -->
# sdd-generate-tests

Resolva o contexto com `sdd context resolve --ticket <TICKET> --runtime auto
--json` e derive `PROJECT_PATH = project.path`, `SDD_WORKSPACE = workspace`,
`SPEC_PATH = spec_path` e `RUNTIME = runtime`. Leia `task.md`, o design aprovado e testes próximos
antes de escrever. Não altere código de produção, contratos
públicos, dependências ou configuração sem autorização explícita.

1. Descubra a linguagem, framework e comando de teste existentes; não presuma
   stack nem crie um segundo framework.
2. Mapeie cada teste a um critério de aceite ou risco confirmado. Se a intenção
   não estiver clara, bloqueie em vez de inventar comportamento.
3. Crie ou ajuste somente testes no diretório de testes do projeto, usando as
   convenções existentes. Cubra cenário principal, erro relevante e borda que
   tenha evidência de risco.
4. Execute o menor comando de teste aplicável com timeout. Diferencie falhas
   preexistentes das introduzidas; não enfraqueça testes existentes.

Não instale pacotes, use rede, faça commit ou atualize `session-state.md`.
Retorne `AGENT_RESULT` com `payload.unit`, incluindo arquivos, comando,
resultado, cobertura de critérios, lacunas e `next_agent: sdd-bootstrap`.
<!-- @end -->
