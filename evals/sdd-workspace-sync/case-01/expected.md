# Expected — sdd-workspace-sync case-01

1. Usa `sdd activation list --json` como fonte das ativações
2. Não detecta instalação pela presença de arquivos legados no projeto
3. Para cada ticket, resolve o contexto pela CLI e lê apenas `SPEC_PATH`
4. Gera preview de `WORKSPACE.md` com nome local, runtime, tickets, estado e data
5. Oculta caminhos e remotes por padrão e só escreve após confirmação
6. Retorna `AGENT_RESULT` com `payload.workspace`
