# Claude Code

Os agentes e skills ficam em `~/.claude/agents` e `~/.claude/skills`. Abra o
projeto e peça a demanda ao `sdd-orchestrator`:

```text
Use sdd-orchestrator para iniciar a demanda ABC-123 neste projeto.
```

Quando o projeto ainda não estiver ativo, o orquestrador apresenta o preview da
ativação — caminho do projeto, workspace a criar e `writes_project: false` —
pede confirmação e ativa sem exigir um terminal externo. O `sdd activate` e o
`sdd start TICKET` continuam disponíveis para automação e CI.

O orquestrador resolve o contexto, pode coordenar subagentes quando a versão do
harness oferecer esse recurso e sempre preserva os gates humanos.

A sintaxe exata de seleção do agente deve ser confirmada na validação manual da versão do
cliente antes de uma release estável.
