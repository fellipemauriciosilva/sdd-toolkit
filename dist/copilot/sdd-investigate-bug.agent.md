---
mode: agent
author: "Felipe Mauricio da Silva"
description: "Investiga um bug sem alterar código: inspeciona logs, stack traces, classes e testes relacionados. Identifica causa raiz, fluxos afetados, correção mínima, risco de regressão e testes para prevenir recorrência."
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

# Investigate Bug

Investigate the described bug without changing code initially. Inspect logs, stack traces, related classes and tests. Identify root cause, affected flows, minimal fix, regression risk and tests to prevent recurrence.
