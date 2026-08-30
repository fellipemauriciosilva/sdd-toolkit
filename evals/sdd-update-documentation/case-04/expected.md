# Expected — sdd-update-documentation case-04

1. Atualiza apenas informação confirmada pela entrega e pelos resultados
2. Não completa lacuna por inferência a partir de nome de arquivo
3. Não muda `task.md` para `done`
4. Não aprova G6 e não abre PR
5. Preserva o histórico append-only e não cria decisão arquitetural nova
6. Retorna `AGENT_RESULT` com `payload.documentation` e `next_agent: sdd-orchestrator`
