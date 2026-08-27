# Claude Code

No diretório do projeto, execute `sdd activate` uma vez e `sdd start TICKET` no
dia a dia. Os agentes e skills ficam em `~/.claude/agents` e `~/.claude/skills`.

Peça ao Claude Code para usar `sdd-bootstrap` com o ticket retornado pelo CLI.
O bootstrap resolve o contexto, pode coordenar subagentes quando a versão do
harness oferecer esse recurso e sempre preserva os gates humanos.

A sintaxe exata de seleção do agente deve ser confirmada na validação manual da versão do
cliente antes de uma release estável.
