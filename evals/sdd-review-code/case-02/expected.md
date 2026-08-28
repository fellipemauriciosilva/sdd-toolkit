# Expected — sdd-review-code case-02

1. Lista os achados `major` com localização e sugestão
2. Nenhum achado `critical`: devolve `payload.review` com os achados e
   `next_agent: sdd-bootstrap`, sem declarar G5 nem acionar CHECKPOINT 2
3. Não edita arquivo algum e não atualiza estado — o bootstrap persiste o G5
4. Resumo no painel: "2 achados `major` (melhorias), 0 críticos"
