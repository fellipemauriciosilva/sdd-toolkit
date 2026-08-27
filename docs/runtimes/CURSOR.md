# Cursor

Abra o projeto no Cursor, execute `sdd activate` uma vez no terminal e use
`sdd start TICKET` para preparar cada demanda. Em seguida, solicite o agente
`sdd-bootstrap` no chat do Cursor com o ticket.

Os agentes ficam em `~/.cursor/agents` e as skills compartilhadas em
`~/.agents/skills`. O projeto consumidor não recebe arquivos de instalação.

A forma exata de descoberta pelo Agent/CLI depende da versão do Cursor e deve
ser registrada pela validação manual antes de uma release estável.
