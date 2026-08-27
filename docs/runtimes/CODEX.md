# Codex

No terminal do projeto, execute `sdd activate` uma vez. Para cada demanda, use
`sdd start TICKET` e solicite o agente `sdd-bootstrap` no ambiente Codex aberto
na mesma raiz.

Os agentes são instalados em `~/.codex/agents`; as skills compartilhadas ficam
em `~/.agents/skills`. O handoff do comando `start` contém o ticket e a spec
resolvida, sem exigir caminhos absolutos no prompt.

A descoberta dos agentes TOML deve ser comprovada na validação manual da versão de Codex
suportada antes da promoção de release.
