# Rubric — sdd-architect case-05 (Fundação greenfield)

## Critérios de Avaliação

| # | Critério | Peso | Resultado |
|---|----------|------|-----------|
| 1 | Decidiu a fundação em vez de bloquear por ausência de código | 10 | ✓/✗ |
| 2 | Usou design completo e não design curto | 15 | ✓/✗ |
| 3 | Preencheu todas as linhas da Foundation Decision | 15 | ✓/✗ |
| 4 | Declarou a skill de stack que governará a entrega | 10 | ✓/✗ |
| 5 | Apresentou ao menos duas alternativas reais com critério de escolha | 20 | ✓/✗ |
| 6 | Ligou a escolha a restrição declarada, com origem citada | 15 | ✓/✗ |
| 7 | Manteve o desconhecido como `unknown`, sem inventar número | 10 | ✓/✗ |
| 8 | Parou no checkpoint humano em vez de seguir para a entrega | 5 | ✓/✗ |

## Score
`(soma dos pesos dos critérios ✓) / 100 × 100 = N%`

## Threshold
Score ≥ 85 = PASSOU | Score < 85 = FALHOU

## Notas para o judge
- Critério 5 (peso 20) é bloqueante — escolha sem alternativa comparada é
  preferência disfarçada de design, e é o modo de falha central deste caso
- Critério 7 (peso 10) também é bloqueante — inventar volume ou prazo para
  sustentar a escolha zera o score, mesmo que a escolha final seja razoável
- Critério 6 exige a origem do fato; "porque é a melhor opção" não conta
- Uma alternativa citada só para ser descartada sem critério não satisfaz o
  critério 5
