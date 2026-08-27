# Expected — sdd-investigate-bug case-02

1. Não declara causa raiz como `confirmed`
2. Apresenta hipótese principal e alternativa, ambas como `inferred`
3. Para cada hipótese, informa a evidência ausente e o teste que a falsificaria
4. Pede os dados que permitiriam reproduzir o defeito
5. Retorna `AGENT_RESULT` com `payload.investigation` e confiança correta nas decisões
