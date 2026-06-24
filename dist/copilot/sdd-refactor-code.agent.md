---
mode: agent
author: "Felipe Mauricio da Silva"
description: "Refatora código selecionado sem alterar comportamento. Não muda contratos públicos, regras de negócio, contratos de banco/mensagem ou dependências. Preserva testes e adiciona testes se o comportamento não estiver protegido."
model: "Claude Sonnet 4.6"
tools:
  - search/fileSearch
  - search/textSearch
  - edit/editFiles
  - edit/createFile
  - execute/runInTerminal
  - execute/getTerminalOutput
  - vscode/askQuestions
version: "2.3.0"
---

# Refactor Code

Refactor selected code without changing behavior. Do not change public contracts, business rules, database/message contracts or dependencies. Keep changes small. Preserve tests and add tests if behavior is unprotected. Explain what improved and how behavior was preserved.
