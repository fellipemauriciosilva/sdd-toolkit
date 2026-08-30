# Codex

Abra o Codex na raiz do projeto e solicite o agente `sdd-orchestrator` com o
ticket da demanda. Se o projeto ainda não estiver ativo, o orquestrador apresenta
o preview da ativação, pede confirmação e ativa sem terminal externo.

Os agentes são instalados em `~/.codex/agents`; as skills compartilhadas ficam
em `~/.agents/skills`. Para automação e CI, `sdd activate` e `sdd start TICKET`
devolvem o mesmo handoff, com o ticket e a spec resolvida, sem exigir caminhos
absolutos no prompt.

A descoberta dos agentes TOML deve ser comprovada na validação manual da versão de Codex
suportada antes da promoção de release.
