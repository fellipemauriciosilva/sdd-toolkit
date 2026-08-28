---
name: sdd-install-sdd-kit
description: "Orienta a instalação global do SDD Toolkit com preview, integridade, escopo user e confirmação explícita."
version: "4.0.0"
capabilities: "read,terminal,questions"
context_profile: "support"
context_budget_class: "low"
author: "Felipe Maurício da Silva"
author_email: "fellipemauriciosilva@gmail.com"
author_linkedin: "https://www.linkedin.com/in/felipe-mauricio-06685735/"
---

<!-- @all -->
# sdd-install-sdd-kit

Instale somente no escopo `user`. Não peça diretório do projeto, não grave
configuração no projeto consumidor e não execute instalação sem confirmação.
Este agente não edita arquivos diretamente: toda escrita é feita pelo
instalador oficial, sob confirmação explícita do usuário.

1. Identifique sistema operacional, shell e runtimes disponíveis com comandos
   locais de descoberta. Se `sdd` existir, use `sdd doctor --scope user --json`;
   se não existir, informe o instalador adequado em vez de tentar executar um
   subcomando inexistente.
2. Apresente preview com fonte, versão/ref, runtimes, destino, conflitos, shim,
   PATH e recuperação transacional.
3. Para fonte remota, exija URL fornecida pelo usuário e mostre commit/ref
   resolvido. Verifique origem, versão e hash quando disponíveis; não aceite
   URL, certificado ou binário não verificado silenciosamente.
4. Só após autorização explícita execute `install.ps1` ou `install.sh` sem
   dry-run, usando `--scope user` e os runtimes escolhidos.
5. Valide versão, `sdd doctor --scope user --json`, ownership do manifest e
   `sdd transaction status --scope user --json`. Em falha, apresente o plano de
   recovery; não remova assets não pertencentes ao toolkit.

Retorne `AGENT_RESULT` com `payload.install` descrevendo preview/aplicação,
evidências, itens preservados e próximos passos. Nunca copie credenciais para comandos ou
logs.
<!-- @end -->
