---
mode: agent
author: "Felipe Maurício da Silva"
description: "Gera ou atualiza testes para o código/comportamento selecionado. Segue as instruções em .github/copilot-instructions.md e testes existentes. Cobre happy path, entrada inválida, falhas externas, exceções, condições de contorno e regressões."
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

# Generate Tests

Generate or update tests for the selected code/behavior. Follow `.github/copilot-instructions.md` and test instructions. Inspect nearby tests first. Use existing libraries and patterns. Avoid unnecessary stubbing. Cover happy path, invalid input, external failures, exceptions, boundary conditions and regressions.
