---
mode: agent
author: "Felipe Maurício da Silva"
description: "Refatora código selecionado sem alterar comportamento. Não muda contratos públicos, regras de negócio, contratos de banco/mensagem ou dependências. Preserva testes e adiciona testes se o comportamento não estiver protegido."
model: "Claude Sonnet 4.6"
capabilities: "read,write,terminal"
tools:
  - search/fileSearch
  - search/textSearch
  - edit/editFiles
  - edit/createFile
  - execute/runInTerminal
  - execute/getTerminalOutput
version: "2.3.0"
---

> **Autor:** Felipe Maurício da Silva · **E-mail:** fellipemauriciosilva@gmail.com · **LinkedIn:** https://www.linkedin.com/in/felipe-mauricio-06685735/

# Refactor Code

Refactor selected code without changing behavior. Do not change public contracts, business rules, database/message contracts or dependencies. Keep changes small. Preserve tests and add tests if behavior is unprotected. Explain what improved and how behavior was preserved.
