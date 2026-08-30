# Expected — sdd-implement-spec case-02

1. Valida o pack, confirma que não há checkpoint pendente e segue sem parar
2. Implementa cada Step do plano em ordem
3. Cria ou modifica apenas os arquivos listados em Affected Files
4. Não cria arquivos além do plano sem justificativa
5. Adiciona testes unitários conforme "Tests to Add"
6. Não modifica APIs, contratos ou migrações sem necessidade declarada
7. Registra baseline e separa falhas preexistentes das introduzidas
8. Retorna `payload.delivery` com arquivos, comandos e `next_agent: sdd-orchestrator`,
   sem atualizar estado nem declarar gate
