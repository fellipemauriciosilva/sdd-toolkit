# Expected — sdd-orchestrator case-03

## Comportamentos esperados

1. **Resolve o contexto pela CLI** — obtém `SPEC_PATH` em vez de adivinhar caminho
2. **Verifica `task.md` e `session-state.md`** — tenta ler, não encontra
3. **Orienta corretamente** — exibe: "Spec não encontrada para ABC-9999. Execute: `/sdd-create-spec ABC-9999`"
4. **Encerra sem executar** — não cria arquivos, não executa nenhum agente
5. **Não cria `session-state.md`** — o orquestrador é proprietário do estado, mas
   não cria a demanda; isso é do `sdd-create-spec`
6. **Retorna `AGENT_RESULT`** com `status: blocked`, `blocked_on` explicando a
   spec ausente e `next_agent: sdd-create-spec`

## Output proibido
- Criar `session-state.md` automaticamente
- Procurar `tasks.md` ou `status-task.md`, que não existem no contrato
- Executar `sdd-analyze-demand` sem spec
- Retornar erro genérico sem orientação de próximo passo
