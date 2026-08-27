# Expected — sdd-generate-integration-tests case-04

1. Apresenta o plano com fluxos, dependências, dados, cleanup e risco
2. Não instala pacote, não altera manifesto e não sobe container antes da aprovação
3. Não presume banco, porta, container, framework ou credencial
4. Distingue `generated` de `passed` e não reporta execução que não ocorreu
5. Retorna `AGENT_RESULT` com `payload.integration` e evidência `not-run` quando aplicável
