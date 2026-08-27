# Expected — sdd-bootstrap case-03

## Comportamentos esperados

1. **Verifica session-state.md** — tenta ler, não encontra
2. **Verifica status-task.md** — tenta ler, não encontra
3. **Orienta corretamente** — exibe mensagem: "Spec não encontrada para JT-9999. Execute: `/sdd-create-spec example-api-gestao-meta JT-9999`"
4. **Encerra sem executar** — não cria arquivos, não executa nenhum agente
5. **Não cria session-state.md** — bootstrap não cria specs, apenas as lê
6. **Mensagem clara** — orienta próximo passo com o comando exato

## Output proibido
- Criar session-state.md automaticamente
- Executar sdd-analyze-demand sem session-state
- Retornar erro genérico sem orientação de próximo passo
