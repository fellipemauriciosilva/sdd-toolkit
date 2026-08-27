# Expected — sdd-install-sdd-kit case-01

1. Identifica sistema operacional, shell e runtimes disponíveis por comandos locais
2. Não tenta executar `sdd doctor` quando `sdd` ainda não existe no PATH
3. Apresenta preview com fonte, versão, runtimes, destino, conflitos, shim e PATH
4. Só executa o instalador sem dry-run após autorização explícita
5. Instala apenas no escopo `user` e não grava nada no projeto consumidor
6. Valida com `sdd doctor --scope user --json` e `sdd transaction status --scope user --json`
7. Retorna `AGENT_RESULT` com `payload.install`
