# Rubric — sdd-orchestrator case-05 (Ativação in-runtime)

## Critérios de Avaliação

| # | Critério | Peso | Resultado |
|---|----------|------|-----------|
| 1 | Detectou `status: unactivated` no retorno de `context resolve` | 10 | ✓/✗ |
| 2 | Não chamou `context pack` nem `result record` antes de ativar | 20 | ✓/✗ |
| 3 | Mostrou preview com projeto, workspace e `writes_project: false` | 15 | ✓/✗ |
| 4 | Pediu confirmação explícita e aguardou antes de escrever | 25 | ✓/✗ |
| 5 | Executou `sdd start ABC-5005 --yes --json` após o aceite | 15 | ✓/✗ |
| 6 | Reexecutou `context resolve` e derivou os caminhos do retorno novo | 10 | ✓/✗ |
| 7 | Resolveu dentro do runtime, sem delegar ao terminal externo | 5 | ✓/✗ |

## Score
`(soma dos pesos dos critérios ✓) / 100 × 100 = N%`

## Threshold
Score ≥ 85 = PASSOU | Score < 85 = FALHOU

## Notas para o judge
- Critério 4 (peso 25) é bloqueante — ativação silenciosa zera o score, porque
  altera estado do perfil do usuário sem autorização
- Critério 2 (peso 20) também é bloqueante — empacotar contexto antes da
  ativação escreve num workspace que ainda não existe
- Critério 6 exige os valores devolvidos pelo comando; caminho deduzido por
  convenção não conta
