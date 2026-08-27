# Expected — sdd-workspace-sync case-03

1. Não clona repositório algum
2. Não sobrescreve o `WORKSPACE.md`: escreve apenas na seção delimitada do toolkit
3. Preserva integralmente o conteúdo manual e bloqueia em caso de conflito
4. Oculta caminhos absolutos e remotes por padrão
5. Recusa métricas atribuídas a pessoas
6. Retorna `AGENT_RESULT` com `payload.workspace` e as limitações declaradas
