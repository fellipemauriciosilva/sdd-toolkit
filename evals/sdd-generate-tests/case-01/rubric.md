# Rubric — sdd-generate-tests case-01

| # | Critério | Peso | Resultado |
|---|----------|------|-----------|
| 1 | Reusou framework e convenções existentes, sem introduzir um segundo | 25 | ✓/✗ |
| 2 | Cada teste rastreia um critério de aceite ou risco | 25 | ✓/✗ |
| 3 | Executou o comando de teste e reportou saída real | 20 | ✓/✗ |
| 4 | Registrou `preexisting_failures` separadamente | 15 | ✓/✗ |
| 5 | Retornou `AGENT_RESULT` com `payload.unit` | 15 | ✓/✗ |

Threshold: ≥ 85 = PASSOU
Introduzir um segundo framework de teste = score 0
