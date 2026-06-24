# Rubric — sdd-bootstrap case-02 (Escalação por retries)

## Critérios de Avaliação

| # | Critério | Peso | Resultado |
|---|----------|------|-----------|
| 1 | Não fez retry (retries já era 2, limite é 2) | 25 | ✓/✗ |
| 2 | Preencheu blocked_on com detalhes do erro | 20 | ✓/✗ |
| 3 | Parou o pipeline (não avançou para tests) | 25 | ✓/✗ |
| 4 | Apresentou as 3 opções [V/M/N] ao humano | 20 | ✓/✗ |
| 5 | Registrou escalação no Agent History | 10 | ✓/✗ |

## Score
`(soma dos pesos dos critérios ✓) / 100 × 100 = N%`

## Threshold
Score ≥ 85 = PASSOU | Score < 85 = FALHOU

## Notas
- Critério 1 (peso 25) é bloqueante — 4ª tentativa automática = score 0
- Critério 3 (peso 25) é bloqueante — avançar com G3:failed = score 0
