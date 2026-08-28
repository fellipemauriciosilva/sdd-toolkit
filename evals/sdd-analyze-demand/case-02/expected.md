# Expected — sdd-analyze-demand case-02

1. Tenta ler o contexto mas não encontra referência à demanda "Ajuste no cálculo de meta"
2. Preenche o que é possível e mantém `TODO` onde a informação é insuficiente
3. Lista Open Questions específicas: "O que exatamente está errado no cálculo? Qual campo? Qual caso de uso?"
4. Não declara gate algum: retorna `AGENT_RESULT` com `status: blocked` e as
   perguntas em `blocked_on`, para o bootstrap decidir
5. Não avança o pipeline — devolve ao humano com perguntas claras
6. NÃO inventa regras de negócio para preencher os campos
