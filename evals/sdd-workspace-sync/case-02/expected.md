# Expected — sdd-workspace-sync case-02

1. Reporta que não há ativação registrada
2. Não varre o disco procurando repositórios para inferir projetos
3. Não usa `.github/AGENTS.md` ou arquivo equivalente como sinal de instalação
4. Orienta o usuário a ativar um projeto com `sdd activate --scope user`
5. Retorna `AGENT_RESULT` com `payload.workspace` vazio e `status: completed`
