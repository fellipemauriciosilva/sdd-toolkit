# GitHub Copilot

Após instalar o SDD Toolkit no escopo user, abra o projeto no VS Code. Os
agentes e skills do toolkit ficam em `~/.copilot/agents` e `~/.copilot/skills`.
No chat do Copilot, selecione o agente SDD disponível ou peça: “Use
sdd-bootstrap para iniciar a demanda TICKET neste projeto.”

Se o projeto ainda não estiver ativo, o bootstrap mostra o preview da ativação,
pede confirmação e ativa a partir do próprio chat. `sdd activate` e
`sdd start TICKET` no terminal integrado seguem válidos para automação e CI.

A validação manual com o cliente e versão reais ainda é necessária para registrar a forma
exata de descoberta na interface. Consulte [HARNESS-VALIDATION.md](../HARNESS-VALIDATION.md).
