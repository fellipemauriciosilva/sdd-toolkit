# Cursor

Abra o projeto no Cursor e solicite o agente `sdd-orchestrator` no chat com o
ticket da demanda. Se o projeto ainda não estiver ativo, o orquestrador mostra o
preview da ativação, pede confirmação e ativa a partir do chat. `sdd activate` e
`sdd start TICKET` no terminal continuam disponíveis para automação e CI.

Os agentes ficam em `~/.cursor/agents` e as skills compartilhadas em
`~/.agents/skills`. O projeto consumidor não recebe arquivos de instalação.

A forma exata de descoberta pelo Agent/CLI depende da versão do Cursor e deve
ser registrada pela validação manual antes de uma release estável.
