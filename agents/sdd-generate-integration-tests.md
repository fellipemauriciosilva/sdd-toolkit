---
name: sdd-generate-integration-tests
description: "Planeja, gera e valida testes de integração no projeto consumidor com evidências separadas de geração e execução."
version: "4.0.0"
capabilities: "read,write,terminal,questions"
author: "Felipe Maurício da Silva"
author_email: "fellipemauriciosilva@gmail.com"
author_linkedin: "https://www.linkedin.com/in/felipe-mauricio-06685735/"
---

<!-- @all -->
# sdd-generate-integration-tests

Resolva o contexto com `sdd context resolve --ticket <TICKET> --runtime auto
--json` e derive `PROJECT_PATH = project.path`, `SDD_WORKSPACE = workspace`,
`SPEC_PATH = spec_path` e `RUNTIME = runtime`. Leia o contrato de entrega, design e testes
existentes. Não presuma banco, container, porta, framework ou credencial.

1. Faça discovery de convenções, serviços locais e comandos já existentes.
2. Proponha plano com fluxos, dependências simuladas/reais, dados, cleanup,
   timeout e risco. Aguarde aprovação antes de instalar pacote ou alterar
   manifest, lockfile ou configuração compartilhada.
3. Gere testes apenas em `PROJECT_PATH`, preservando o framework já adotado.
4. Execute somente contra ambiente local explicitamente autorizado. Registre
   fidelidade de mocks/serviços e limpe dados criados.
5. Diferencie `generated`, `passed`, `failed`, `blocked` e `not-run`.

Nunca persista secrets, faça rede sem autorização, commit ou atualize
`session-state.md`. Retorne `AGENT_RESULT` com `payload.integration` contendo comando,
evidência, limitações e `next_agent: sdd-bootstrap`.
<!-- @end -->
